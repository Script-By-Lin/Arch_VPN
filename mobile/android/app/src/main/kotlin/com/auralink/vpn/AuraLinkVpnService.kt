package com.auralink.vpn

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.net.ConnectivityManager
import android.net.LocalServerSocket
import android.net.LocalSocket
import android.net.LocalSocketAddress
import android.net.TrafficStats
import android.net.VpnService
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.ParcelFileDescriptor
import android.system.Os
import android.system.OsConstants
import io.flutter.plugin.common.EventChannel
import org.json.JSONObject
import java.io.BufferedReader
import java.io.File
import java.io.FileInputStream
import java.io.InputStream
import java.io.InputStreamReader
import java.net.HttpURLConnection
import java.net.Inet4Address
import java.net.InetAddress
import java.net.InetSocketAddress
import java.net.Proxy
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
 *   1/5: Resolve server hostname to IPv4, check direct reachability & start protect_path UDS
 *   2/5: Start Android-native Shadowsocks core (`libsslocal.so` with `outbound_vpn_protect_path`)
 *   3/5: Establish Android VpnService TUN (`10.0.0.2/24`, MTU 1420) + native IPv6 Leak Shield
 *   4/5: Spawn `libtun2socks.so` via JNI `TunExec.spawnWithFd` (FD 3 guaranteed open O_RDWR)
 *   5/5: Verify real internet + DNS reachability THROUGH `socks5://127.0.0.1:1080`
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
        private const val TUN_MTU = 1420

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
    private var tun2socksPid: Int = -1
    private var tun2socksLogPfd: ParcelFileDescriptor? = null
    private var statsTask: ScheduledFuture<*>? = null
    private val sslocalListening = AtomicBoolean(false)

    // Unix Domain Socket server implementing shadowsocks-rust `outbound_vpn_protect_path`
    private val protectServerRunning = AtomicBoolean(false)
    private var protectBindSocket: LocalSocket? = null
    private var protectServerSocket: LocalServerSocket? = null

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

    /**
     * Starts a local UNIX domain socket implementing shadowsocks-rust's `outbound_vpn_protect_path`
     * RPC so every outbound TCP/UDP socket created by `libsslocal.so` is explicitly protected via
     * `VpnService.protect(fd)` (matching official shadowsocks-android).
     */
    private fun startProtectServer(socketFile: File) {
        stopProtectServer()
        if (socketFile.exists()) {
            socketFile.delete()
        }

        val bindSock = LocalSocket(LocalSocket.SOCKET_STREAM)
        bindSock.bind(LocalSocketAddress(socketFile.absolutePath, LocalSocketAddress.Namespace.FILESYSTEM))
        val serverSock = LocalServerSocket(bindSock.fileDescriptor)
        protectBindSocket = bindSock
        protectServerSocket = serverSock
        protectServerRunning.set(true)

        Thread({
            while (protectServerRunning.get()) {
                var client: LocalSocket? = null
                try {
                    client = serverSock.accept()
                    val inp = client.inputStream
                    val out = client.outputStream
                    // shadowsocks-rust sends 1 dummy byte + 1 SCM_RIGHTS fd
                    val dummy = inp.read()
                    if (dummy < 0) continue
                    val fds = client.ancillaryFileDescriptors
                    var ok = false
                    if (fds != null && fds.isNotEmpty()) {
                        for (i in fds.indices) {
                            if (i == 0) {
                                try {
                                    ParcelFileDescriptor.dup(fds[i]).use { dupPfd ->
                                        ok = protect(dupPfd.fd)
                                    }
                                } catch (e: Exception) {
                                    emitLog("[protect] protect() error: ${e.message}")
                                }
                            }
                            try {
                                Os.close(fds[i])
                            } catch (_: Exception) {}
                        }
                    }
                    // shadowsocks-rust treats 0xFF as failure and any other byte (0x00) as success
                    out.write(if (ok) 0 else 0xFF)
                    out.flush()
                } catch (_: Exception) {
                    if (!protectServerRunning.get()) break
                } finally {
                    try {
                        client?.close()
                    } catch (_: Exception) {}
                }
            }
        }, "auralink-protect-uds").start()
    }

    private fun stopProtectServer() {
        protectServerRunning.set(false)
        try {
            protectServerSocket?.close()
        } catch (_: Exception) {}
        protectServerSocket = null
        try {
            protectBindSocket?.close()
        } catch (_: Exception) {}
        protectBindSocket = null
    }

    private data class PreparedConfig(
        val json: String,
        val server: String,
        val port: Int,
        val method: String
    )

    private fun prepareShadowsocksConfig(
        rawJson: String,
        dnsPrimary: String,
        protectPath: String
    ): PreparedConfig {
        val cfg = JSONObject(rawJson)
        var resolvedServer = cfg.optString("server", "").trim()
        val port = cfg.optInt("server_port", 443)
        val method = cfg.optString("method", "chacha20-ietf-poly1305")

        if (resolvedServer.isNotEmpty()) {
            try {
                val addrs = InetAddress.getAllByName(resolvedServer)
                val v4 = addrs.firstOrNull { it is Inet4Address } ?: addrs.firstOrNull()
                if (v4 != null && !v4.hostAddress.isNullOrBlank()) {
                    val resolved = v4.hostAddress!!
                    if (resolved != resolvedServer) {
                        emitLog("[dns] Resolved $resolvedServer -> $resolved")
                    }
                    resolvedServer = resolved
                    cfg.put("server", resolvedServer)
                }
            } catch (e: Exception) {
                emitLog("[dns] Could not pre-resolve $resolvedServer: ${e.message}")
            }
        }

        if (!cfg.has("dns") && dnsPrimary.isNotBlank()) {
            cfg.put("dns", dnsPrimary)
        }
        // Enable official Android VpnService.protect() RPC for all outbound sslocal sockets
        cfg.put("outbound_vpn_protect_path", protectPath)

        return PreparedConfig(
            json = cfg.toString(),
            server = resolvedServer,
            port = port,
            method = method
        )
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
            teardownResources()

            currentState = "CONNECTING"
            emitStage("resolving", "1/5: Resolving Node", "Preparing config for $profileName...")
            if (checkCancelled()) return

            // Start Android protect_path Unix socket server before sslocal starts
            val protectFile = File(filesDir, "protect_path")
            startProtectServer(protectFile)

            val prepared = prepareShadowsocksConfig(ssConfigJson, dnsPrimary, protectFile.absolutePath)
            emitLog("[config] Target ${prepared.server}:${prepared.port} (${prepared.method})")

            // Pre-VPN direct TCP reachability diagnostic
            if (prepared.server.isNotEmpty() && prepared.port > 0) {
                val t0 = System.currentTimeMillis()
                try {
                    Socket().use { s ->
                        s.connect(InetSocketAddress(prepared.server, prepared.port), 3500)
                    }
                    emitLog("[probe] Direct TCP ${prepared.server}:${prepared.port} OK (${System.currentTimeMillis() - t0}ms)")
                } catch (e: Exception) {
                    emitLog("[probe] Direct TCP ${prepared.server}:${prepared.port} FAILED: ${e.message}")
                }
            }
            if (checkCancelled()) return

            val configFile = File(filesDir, "active_config.json")
            configFile.writeText(prepared.json)

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
            sslocalListening.set(false)
            sslocalProcess = ProcessBuilder(sslocalBin.absolutePath, "-c", configFile.absolutePath, "-v")
                .directory(filesDir)
                .redirectErrorStream(true)
                .start()
            pipeStreamLogs("sslocal", sslocalProcess!!.inputStream)

            if (!waitForLocalPort(1080, 5000)) {
                if (checkCancelled()) return
                throw IllegalStateException("sslocal failed to listen on 127.0.0.1:1080")
            }
            if (checkCancelled()) return

            // Stage 3/5: Establish Android VpnService TUN + native IPv6 Leak Shield
            emitStage("tun0", "3/5: Virtual TUN", "Establishing TUN interface (MTU $TUN_MTU) & IPv6 shield...")
            val builder = Builder()
                .setSession("AuraLink VPN — $profileName")
                .setMtu(TUN_MTU)
                .addAddress("10.0.0.2", 24)
                .addRoute("0.0.0.0", 0)
                .addDnsServer(dnsPrimary)
                .addDisallowedApplication(packageName)

            if (dnsBackup.isNotBlank()) {
                builder.addDnsServer(dnsBackup)
            }

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                builder.setMetered(false)
            }

            // Attach current physical network as underlying network for Android ConnectivityManager
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP_MR1) {
                try {
                    val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
                    val activeNet = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                        cm?.activeNetwork
                    } else {
                        null
                    }
                    if (activeNet != null) {
                        builder.setUnderlyingNetworks(arrayOf(activeNet))
                    }
                } catch (_: Exception) {}
            }

            if (disableIpv6) {
                ipv6DisabledActive = true
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

            // Stage 4/5: Spawn tun2socks via JNI TunExec so FD 3 is genuinely inherited O_RDWR
            emitStage("routing", "4/5: Routes & DNS", "Attaching tun2socks to TUN FD & applying DNS $dnsPrimary...")
            val tunArgs = arrayOf(
                tun2socksBin.absolutePath,
                "-device", "fd://3",
                "-mtu", TUN_MTU.toString(),
                "-proxy", "socks5://127.0.0.1:1080",
                "-loglevel", "info"
            )
            val spawned = TunExec.spawnWithFd(tun2socksBin.absolutePath, tunArgs, pfd.fd, 3)
                ?: throw IllegalStateException("Failed to spawn tun2socks with inherited TUN FD.")
            tun2socksPid = spawned[0]
            val logReadFd = spawned[1]
            if (logReadFd >= 0) {
                val logPfd = ParcelFileDescriptor.adoptFd(logReadFd)
                tun2socksLogPfd = logPfd
                pipeStreamLogs("tun2socks", FileInputStream(logPfd.fileDescriptor))
            }

            Thread.sleep(350)
            if (checkCancelled()) return
            if (!TunExec.isAlive(tun2socksPid)) {
                throw IllegalStateException("tun2socks exited unexpectedly — check Logs for details.")
            }

            // Stage 5/5: Verify real internet + DNS flow THROUGH local SOCKS5 proxy
            var verified = true
            var verifyLatency: Int? = null
            var verifyDetail = "Verification skipped"
            if (verifyTunnel) {
                emitStage("verifying", "5/5: Verifying Net", "Checking real internet & DNS through VPN tunnel...")
                val probe = verifyConnectivityThroughTunnel(timeoutMs = 12000)
                if (checkCancelled()) return
                if (!TunExec.isAlive(tun2socksPid) || sslocalProcess?.isAlive != true) {
                    throw IllegalStateException("VPN daemon exited during tunnel verification.")
                }
                verified = probe.first
                verifyLatency = probe.second
                if (!verified) {
                    throw IllegalStateException(
                        "Server ${prepared.server}:${prepared.port} did not pass internet traffic (check Logs or switch node)."
                    )
                }
                verifyDetail = "Tunnel internet & DNS verified (${verifyLatency}ms)"
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
        val start = System.currentTimeMillis()
        val deadline = start + timeoutMs
        while (System.currentTimeMillis() < deadline) {
            if (cancelRequested.get()) return false
            if (sslocalListening.get()) return true
            val proc = sslocalProcess
            if (proc != null && !proc.isAlive) return false
            if (System.currentTimeMillis() - start >= 1500) {
                try {
                    Socket().use { s ->
                        s.connect(InetSocketAddress("127.0.0.1", port), 250)
                        return true
                    }
                } catch (_: Exception) {}
            }
            Thread.sleep(40)
        }
        return false
    }

    /**
     * Probes real HTTP reachability THROUGH `socks5://127.0.0.1:1080` so verification actually
     * tests the remote VPN server (instead of bypassing the tunnel via addDisallowedApplication).
     */
    private fun verifyConnectivityThroughTunnel(timeoutMs: Long): Pair<Boolean, Int?> {
        val probes = listOf(
            "http://cp.cloudflare.com/generate_204",
            "http://1.1.1.1/cdn-cgi/trace",
            "http://connectivitycheck.gstatic.com/generate_204"
        )
        val socksProxy = Proxy(Proxy.Type.SOCKS, InetSocketAddress("127.0.0.1", 1080))
        val deadline = System.currentTimeMillis() + timeoutMs
        var attempt = 0
        while (System.currentTimeMillis() < deadline) {
            if (cancelRequested.get()) return Pair(false, null)
            if (!TunExec.isAlive(tun2socksPid) || sslocalProcess?.isAlive != true) {
                return Pair(false, null)
            }
            val urlStr = probes[attempt % probes.size]
            val t0 = System.currentTimeMillis()
            try {
                val conn = (URL(urlStr).openConnection(socksProxy) as HttpURLConnection).apply {
                    connectTimeout = 3000
                    readTimeout = 3000
                    requestMethod = "GET"
                    instanceFollowRedirects = false
                }
                val code = conn.responseCode
                conn.disconnect()
                if (code in 200..399) {
                    emitLog("[verify] Tunnel probe $urlStr OK (HTTP $code, ${System.currentTimeMillis() - t0}ms)")
                    return Pair(true, (System.currentTimeMillis() - t0).toInt())
                }
            } catch (e: Exception) {
                if (attempt < 2) {
                    emitLog("[verify] Probe $urlStr failed: ${e.message}")
                }
            }
            attempt++
            Thread.sleep(450)
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
        if (tun2socksPid > 0) {
            try {
                TunExec.killProcess(tun2socksPid)
            } catch (_: Exception) {}
            tun2socksPid = -1
        }
        try {
            tun2socksLogPfd?.close()
        } catch (_: Exception) {}
        tun2socksLogPfd = null
        try {
            sslocalProcess?.destroy()
        } catch (_: Exception) {}
        sslocalProcess = null
        stopProtectServer()
        try {
            tunInterface?.close()
        } catch (_: Exception) {}
        tunInterface = null
    }

    private fun pipeStreamLogs(tag: String, stream: InputStream) {
        Thread {
            try {
                BufferedReader(InputStreamReader(stream)).use { reader ->
                    var line: String?
                    while (reader.readLine().also { line = it } != null) {
                        val rawLine = line ?: continue
                        if (tag == "sslocal" && rawLine.contains("listening on", ignoreCase = true)) {
                            sslocalListening.set(true)
                        }
                        emitLog("[$tag] $rawLine")
                    }
                }
            } catch (_: Exception) {}
        }.start()
    }

    private fun emitLog(msg: String) {
        mainHandler.post { logSink?.success(msg) }
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
