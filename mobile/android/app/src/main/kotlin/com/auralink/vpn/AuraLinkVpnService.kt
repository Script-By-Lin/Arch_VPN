package com.auralink.vpn

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Intent
import android.net.TrafficStats
import android.net.VpnService
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.ParcelFileDescriptor
import android.system.OsConstants
import io.flutter.plugin.common.EventChannel
import java.io.BufferedReader
import java.io.File
import java.io.InputStreamReader
import java.net.HttpURLConnection
import java.net.InetSocketAddress
import java.net.Socket
import java.net.URL
import java.util.concurrent.Executors
import java.util.concurrent.ScheduledFuture
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean

/**
 * AuraLink Native Android VpnService.
 *
 * Pipeline (mirrors Linux core/vpn_service.py):
 *   1/5: Resolve & validate config
 *   2/5: Start local Shadowsocks core (`libsslocal.so`, TCP+UDP + TCP_NODELAY)
 *   3/5: Establish Android VpnService TUN (`10.0.0.2/24`) + IPv6 Leak Shield
 *   4/5: Attach `libtun2socks.so` to TUN FD & route 0.0.0.0/0 with custom DNS
 *   5/5: Verify real internet + DNS reachability via HTTP 204 probe
 *
 * Supports lock-free cancellation (`cancelRequested`) at every stage.
 */
class AuraLinkVpnService : VpnService() {
    companion object {
        const val ACTION_CONNECT = "com.auralink.vpn.CONNECT"
        const val ACTION_CANCEL = "com.auralink.vpn.CANCEL"
        const val ACTION_DISCONNECT = "com.auralink.vpn.DISCONNECT"
        private const val NOTIF_CHANNEL_ID = "auralink_vpn_channel"
        private const val NOTIF_ID = 1001

        @Volatile
        var eventSink: EventChannel.EventSink? = null

        @Volatile
        var statsSink: EventChannel.EventSink? = null

        @Volatile
        var logSink: EventChannel.EventSink? = null

        @Volatile
        var currentState: String = "DISCONNECTED"

        @Volatile
        var ipv6DisabledActive: Boolean = false

        private val cancelRequested = AtomicBoolean(false)

        fun requestCancel() {
            cancelRequested.set(true)
        }
    }

    private val mainHandler = Handler(Looper.getMainLooper())
    private val worker = Executors.newSingleThreadExecutor()
    private val statsScheduler = Executors.newSingleThreadScheduledExecutor()

    private var tunInterface: ParcelFileDescriptor? = null
    private var sslocalProcess: Process? = null
    private var tun2socksProcess: Process? = null
    private var statsTask: ScheduledFuture<*>? = null

    private var baseRxBytes: Long = 0L
    private var baseTxBytes: Long = 0L
    private var lastRxBytes: Long = 0L
    private var lastTxBytes: Long = 0L

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_CONNECT -> {
                cancelRequested.set(false)
                val profileName = intent.getStringExtra("profile_name") ?: "AuraLink Node"
                val ssConfigJson = intent.getStringExtra("ss_config_json") ?: "{}"
                val dnsPrimary = intent.getStringExtra("dns_primary") ?: "1.1.1.1"
                val dnsBackup = intent.getStringExtra("dns_backup") ?: "1.0.0.1"
                val disableIpv6 = intent.getBooleanExtra("disable_ipv6", true)
                val verifyTunnel = intent.getBooleanExtra("verify_tunnel", true)

                startForeground(NOTIF_ID, buildNotification("Connecting to $profileName..."))
                worker.execute {
                    runConnectPipeline(
                        profileName = profileName,
                        ssConfigJson = ssConfigJson,
                        dnsPrimary = dnsPrimary,
                        dnsBackup = dnsBackup,
                        disableIpv6 = disableIpv6,
                        verifyTunnel = verifyTunnel
                    )
                }
            }

            ACTION_CANCEL, ACTION_DISCONNECT -> {
                cancelRequested.set(true)
                worker.execute {
                    teardownTunnel("VPN Disconnected")
                }
            }
        }
        return START_NOT_STICKY
    }

    private fun runConnectPipeline(
        profileName: String,
        ssConfigJson: String,
        dnsPrimary: String,
        dnsBackup: String,
        disableIpv6: Boolean,
        verifyTunnel: Boolean
    ) {
        try {
            currentState = "CONNECTING"
            emitStage("resolving", "1/5: Resolving Node", "Preparing config for $profileName...")
            if (checkCancelled()) return

            // Write active_config.json to app private storage
            val configFile = File(filesDir, "active_config.json")
            configFile.writeText(ssConfigJson)

            val libDir = applicationInfo.nativeLibraryDir
            val sslocalBin = File(libDir, "libsslocal.so")
            val tun2socksBin = File(libDir, "libtun2socks.so")
            if (!sslocalBin.exists() || !tun2socksBin.exists()) {
                throw IllegalStateException(
                    "Native VPN libraries (libsslocal.so / libtun2socks.so) not found in jniLibs."
                )
            }

            // Stage 2/5: Start sslocal
            emitStage("sslocal", "2/5: SOCKS5 Core", "Starting Shadowsocks core on 127.0.0.1:1080...")
            sslocalProcess = ProcessBuilder(sslocalBin.absolutePath, "-c", configFile.absolutePath)
                .redirectErrorStream(true)
                .start()
            pipeProcessLogs("sslocal", sslocalProcess!!)

            if (!waitForLocalPort(1080, 5000)) {
                if (checkCancelled()) return
                throw IllegalStateException("sslocal failed to listen on 127.0.0.1:1080")
            }
            if (checkCancelled()) return

            // Stage 3/5: Establish Android VpnService TUN + IPv6 Leak Shield
            emitStage("tun0", "3/5: Virtual TUN", "Establishing TUN interface & IPv6 shield...")
            val builder = Builder()
                .setSession("AuraLink VPN — $profileName")
                .setMtu(1500)
                .addAddress("10.0.0.2", 24)
                .addRoute("0.0.0.0", 0)
                .addDnsServer(dnsPrimary)
                .addDisallowedApplication(packageName) // Prevent routing loops for sslocal

            if (dnsBackup.isNotBlank()) {
                builder.addDnsServer(dnsBackup)
            }

            // IPv6 Leak Shield: capture ::/0 inside TUN (dropping unrouted IPv6) or disallow AF_INET6
            if (disableIpv6) {
                try {
                    builder.addAddress("fd00:auralink::2", 128)
                    builder.addRoute("::", 0)
                    ipv6DisabledActive = true
                } catch (_: Exception) {
                    ipv6DisabledActive = false
                }
            } else {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                    builder.allowFamily(OsConstants.AF_INET6)
                }
                ipv6DisabledActive = false
            }

            val pfd = builder.establish()
                ?: throw IllegalStateException("Failed to establish Android VpnService interface.")
            tunInterface = pfd
            if (checkCancelled()) return

            // Stage 4/5: Attach tun2socks to TUN file descriptor
            emitStage("routing", "4/5: Routes & DNS", "Attaching tun2socks to TUN & applying DNS $dnsPrimary...")
            val fdNum = pfd.fd
            tun2socksProcess = ProcessBuilder(
                tun2socksBin.absolutePath,
                "-device", "fd://$fdNum",
                "-proxy", "socks5://127.0.0.1:1080",
                "-loglevel", "info"
            )
                .redirectErrorStream(true)
                .start()
            pipeProcessLogs("tun2socks", tun2socksProcess!!)

            Thread.sleep(250)
            if (checkCancelled()) return

            // Stage 5/5: Verify real internet + DNS flow
            var verified = true
            var verifyLatency: Int? = null
            var verifyDetail = "Verification skipped"
            if (verifyTunnel) {
                emitStage("verifying", "5/5: Verifying Net", "Checking internet & DNS flow through TUN...")
                val probe = verifyConnectivity(timeoutMs = 12000)
                if (checkCancelled()) return
                verified = probe.first
                verifyLatency = probe.second
                verifyDetail = if (verified) {
                    "Internet & DNS verified (${verifyLatency}ms)"
                } else {
                    "Probe timed out — check server node"
                }
            }

            currentState = "CONNECTED"
            startStatsPolling()
            updateNotification("Connected • $profileName")

            emitEvent(
                mapOf(
                    "type" to "connected",
                    "message" to "VPN Connected Successfully",
                    "ipv6_disabled" to ipv6DisabledActive,
                    "verified" to verified,
                    "verify_latency_ms" to verifyLatency,
                    "verify_detail" to verifyDetail
                )
            )
        } catch (e: Exception) {
            if (cancelRequested.get()) {
                teardownTunnel("Connection cancelled by user")
                return
            }
            teardownResources()
            currentState = "ERROR"
            emitEvent(
                mapOf(
                    "type" to "error",
                    "error" to (e.message ?: "Unknown VPN error"),
                    "message" to (e.message ?: "Unknown VPN error")
                )
            )
            stopSelf()
        }
    }

    private fun checkCancelled(): Boolean {
        if (cancelRequested.get()) {
            teardownTunnel("Connection cancelled by user")
            return true
        }
        return false
    }

    private fun waitForLocalPort(port: Int, timeoutMs: Long): Boolean {
        val deadline = System.currentTimeMillis() + timeoutMs
        while (System.currentTimeMillis() < deadline) {
            if (cancelRequested.get()) return false
            try {
                Socket().use { s ->
                    s.connect(InetSocketAddress("127.0.0.1", port), 250)
                    return true
                }
            } catch (_: Exception) {
                Thread.sleep(50)
            }
        }
        return false
    }

    private fun verifyConnectivity(timeoutMs: Long): Pair<Boolean, Int?> {
        val probes = listOf(
            "http://cp.cloudflare.com/generate_204",
            "http://connectivitycheck.gstatic.com/generate_204"
        )
        val deadline = System.currentTimeMillis() + timeoutMs
        var attempt = 0
        while (System.currentTimeMillis() < deadline) {
            if (cancelRequested.get()) return Pair(false, null)
            val urlStr = probes[attempt % probes.size]
            val t0 = System.currentTimeMillis()
            try {
                val conn = (URL(urlStr).openConnection() as HttpURLConnection).apply {
                    connectTimeout = 2000
                    readTimeout = 2000
                    requestMethod = "GET"
                }
                val code = conn.responseCode
                conn.disconnect()
                if (code in 200..399) {
                    return Pair(true, (System.currentTimeMillis() - t0).toInt())
                }
            } catch (_: Exception) {
                // Retry until deadline
            }
            attempt++
            Thread.sleep(400)
        }
        return Pair(false, null)
    }

    private fun startStatsPolling() {
        statsTask?.cancel(true)
        val uid = applicationInfo.uid
        baseRxBytes = TrafficStats.getTotalRxBytes().coerceAtLeast(0L)
        baseTxBytes = TrafficStats.getTotalTxBytes().coerceAtLeast(0L)
        lastRxBytes = baseRxBytes
        lastTxBytes = baseTxBytes

        statsTask = statsScheduler.scheduleAtFixedRate({
            if (currentState != "CONNECTED") return@scheduleAtFixedRate
            val curRx = TrafficStats.getTotalRxBytes().coerceAtLeast(baseRxBytes)
            val curTx = TrafficStats.getTotalTxBytes().coerceAtLeast(baseTxBytes)
            val rxDelta = (curRx - lastRxBytes).coerceAtLeast(0L)
            val txDelta = (curTx - lastTxBytes).coerceAtLeast(0L)
            lastRxBytes = curRx
            lastTxBytes = curTx

            mainHandler.post {
                statsSink?.success(
                    mapOf(
                        "uid" to uid,
                        "rx_speed_bps" to rxDelta.toDouble(),
                        "tx_speed_bps" to txDelta.toDouble(),
                        "rx_bytes" to (curRx - baseRxBytes),
                        "tx_bytes" to (curTx - baseTxBytes)
                    )
                )
            }
        }, 1, 1, TimeUnit.SECONDS)
    }

    private fun teardownTunnel(reason: String) {
        teardownResources()
        currentState = "DISCONNECTED"
        ipv6DisabledActive = false
        emitEvent(mapOf("type" to "disconnected", "message" to reason))
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private fun teardownResources() {
        statsTask?.cancel(true)
        statsTask = null
        try {
            tun2socksProcess?.destroy()
        } catch (_: Exception) {}
        tun2socksProcess = null
        try {
            sslocalProcess?.destroy()
        } catch (_: Exception) {}
        sslocalProcess = null
        try {
            tunInterface?.close()
        } catch (_: Exception) {}
        tunInterface = null
    }

    private fun pipeProcessLogs(tag: String, process: Process) {
        Thread {
            try {
                BufferedReader(InputStreamReader(process.inputStream)).use { reader ->
                    var line: String?
                    while (reader.readLine().also { line = it } != null) {
                        val msg = "[$tag] $line"
                        mainHandler.post { logSink?.success(msg) }
                    }
                }
            } catch (_: Exception) {}
        }.start()
    }

    private fun emitStage(stage: String, label: String, message: String) {
        emitEvent(
            mapOf(
                "type" to "stage_changed",
                "stage" to stage,
                "stage_label" to label,
                "message" to message
            )
        )
    }

    private fun emitEvent(payload: Map<String, Any?>) {
        mainHandler.post { eventSink?.success(payload) }
    }

    private fun buildNotification(content: String): Notification {
        val mgr = getSystemService(NotificationManager::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val ch = NotificationChannel(
                NOTIF_CHANNEL_ID,
                "AuraLink VPN Tunnel",
                NotificationManager.IMPORTANCE_LOW
            )
            mgr.createNotificationChannel(ch)
        }
        val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Notification.Builder(this, NOTIF_CHANNEL_ID)
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this)
        }
        return builder
            .setContentTitle("AuraLink Daylight VPN")
            .setContentText(content)
            .setSmallIcon(android.R.drawable.ic_lock_lock)
            .setOngoing(true)
            .build()
    }

    private fun updateNotification(content: String) {
        val mgr = getSystemService(NotificationManager::class.java)
        mgr.notify(NOTIF_ID, buildNotification(content))
    }

    override fun onRevoke() {
        cancelRequested.set(true)
        teardownTunnel("VPN permission revoked by system")
        super.onRevoke()
    }

    override fun onDestroy() {
        teardownResources()
        worker.shutdownNow()
        statsScheduler.shutdownNow()
        super.onDestroy()
    }
}
