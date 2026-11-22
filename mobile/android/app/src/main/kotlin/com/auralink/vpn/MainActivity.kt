package com.auralink.vpn

import android.app.Activity
import android.content.Intent
import android.net.VpnService
import android.os.Build
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodChannel
import org.json.JSONObject
import java.io.File

class MainActivity : FlutterActivity() {
    companion object {
        private const val CHANNEL_CONTROL = "com.auralink.vpn/control"
        private const val CHANNEL_EVENTS = "com.auralink.vpn/events"
        private const val CHANNEL_STATS = "com.auralink.vpn/stats"
        private const val CHANNEL_LOGS = "com.auralink.vpn/logs"
        private const val VPN_PREPARE_REQ = 4201
    }

    private var pendingPrepareResult: MethodChannel.Result? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        // EventChannel: State & Stage updates
        EventChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL_EVENTS)
            .setStreamHandler(object : EventChannel.StreamHandler {
                override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
                    AuraLinkVpnService.eventSink = events
                }

                override fun onCancel(arguments: Any?) {
                    AuraLinkVpnService.eventSink = null
                }
            })

        // EventChannel: Live byte counters & speeds
        EventChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL_STATS)
            .setStreamHandler(object : EventChannel.StreamHandler {
                override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
                    AuraLinkVpnService.statsSink = events
                }

                override fun onCancel(arguments: Any?) {
                    AuraLinkVpnService.statsSink = null
                }
            })

        // EventChannel: Daemon log stream
        EventChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL_LOGS)
            .setStreamHandler(object : EventChannel.StreamHandler {
                override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
                    AuraLinkVpnService.logSink = events
                }

                override fun onCancel(arguments: Any?) {
                    AuraLinkVpnService.logSink = null
                }
            })

        // MethodChannel: Control commands
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL_CONTROL)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "hasNativeEngine" -> {
                        val libDir = applicationInfo.nativeLibraryDir
                        val hasSs = File(libDir, "libsslocal.so").exists()
                        val hasTun = File(libDir, "libtun2socks.so").exists()
                        result.success(hasSs && hasTun)
                    }

                    "prepareVpn" -> {
                        val intent = VpnService.prepare(this)
                        if (intent == null) {
                            result.success(true)
                        } else {
                            pendingPrepareResult = result
                            startActivityForResult(intent, VPN_PREPARE_REQ)
                        }
                    }

                    "connect" -> {
                        @Suppress("UNCHECKED_CAST")
                        val args = call.arguments as? Map<String, Any?> ?: emptyMap()
                        val ssConfigMap = args["ss_config"] as? Map<*, *>
                        val ssConfigJson = if (ssConfigMap != null) JSONObject(ssConfigMap).toString() else "{}"

                        val intent = Intent(this, AuraLinkVpnService::class.java).apply {
                            action = AuraLinkVpnService.ACTION_CONNECT
                            putExtra("profile_name", args["profile_name"]?.toString() ?: "AuraLink Node")
                            putExtra("server", args["server"]?.toString() ?: "")
                            putExtra("server_port", (args["server_port"] as? Number)?.toInt() ?: 443)
                            putExtra("ss_config_json", ssConfigJson)
                            putExtra("dns_primary", args["dns_primary"]?.toString() ?: "1.1.1.1")
                            putExtra("dns_backup", args["dns_backup"]?.toString() ?: "1.0.0.1")
                            putExtra("disable_ipv6", (args["disable_ipv6"] as? Boolean) ?: true)
                            putExtra("udp_relay", (args["udp_relay"] as? Boolean) ?: true)
                            putExtra("verify_tunnel", (args["verify_tunnel"] as? Boolean) ?: true)
                        }
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                            startForegroundService(intent)
                        } else {
                            startService(intent)
                        }
                        result.success(true)
                    }

                    "cancelConnect" -> {
                        AuraLinkVpnService.requestCancel()
                        val intent = Intent(this, AuraLinkVpnService::class.java).apply {
                            action = AuraLinkVpnService.ACTION_CANCEL
                        }
                        startService(intent)
                        result.success(true)
                    }

                    "disconnect" -> {
                        AuraLinkVpnService.requestCancel()
                        val intent = Intent(this, AuraLinkVpnService::class.java).apply {
                            action = AuraLinkVpnService.ACTION_DISCONNECT
                        }
                        startService(intent)
                        result.success(true)
                    }

                    "getStatus" -> {
                        result.success(
                            mapOf(
                                "state" to AuraLinkVpnService.currentState,
                                "ipv6_disabled" to AuraLinkVpnService.ipv6DisabledActive
                            )
                        )
                    }

                    else -> result.notImplemented()
                }
            }
    }

    @Deprecated("Deprecated in Android API, preserved for FlutterActivity compatibility")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        if (requestCode == VPN_PREPARE_REQ) {
            pendingPrepareResult?.success(resultCode == Activity.RESULT_OK)
            pendingPrepareResult = null
            return
        }
        super.onActivityResult(requestCode, resultCode, data)
    }
}
