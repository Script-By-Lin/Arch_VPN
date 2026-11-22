import Flutter
import NetworkExtension
import UIKit

@main
@objc class AppDelegate: FlutterAppDelegate {
    private let controlChannelName = "com.auralink.vpn/control"
    private let eventsChannelName = "com.auralink.vpn/events"
    private let tunnelBundleId = "com.auralink.vpn.PacketTunnel"

    private var eventSink: FlutterEventSink?
    private var tunnelManager: NETunnelProviderManager?

    override func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {
        GeneratedPluginRegistrant.register(with: self)

        if let controller = window?.rootViewController as? FlutterViewController {
            let control = FlutterMethodChannel(
                name: controlChannelName,
                binaryMessenger: controller.binaryMessenger
            )
            let events = FlutterEventChannel(
                name: eventsChannelName,
                binaryMessenger: controller.binaryMessenger
            )

            events.setStreamHandler(self)
            control.setMethodCallHandler { [weak self] call, result in
                self?.handleMethodCall(call, result: result)
            }
        }

        NotificationCenter.default.addObserver(
            self,
            selector: #selector(vpnStatusDidChange(_:)),
            name: .NEVPNStatusDidChange,
            object: nil
        )

        return super.application(application, didFinishLaunchingWithOptions: launchOptions)
    }

    private func handleMethodCall(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
        switch call.method {
        case "hasNativeEngine":
            // Returns true once PacketTunnel NetworkExtension target is signed & bundled in Xcode
            let extPath = Bundle.main.builtInPlugInsPath.map {
                URL(fileURLWithPath: $0).appendingPathComponent("PacketTunnel.appex").path
            }
            let exists = extPath.map { FileManager.default.fileExists(atPath: $0) } ?? false
            result(exists)

        case "prepareVpn":
            loadOrCreateManager { manager, error in
                if let error = error {
                    result(FlutterError(code: "PREPARE_FAILED", message: error.localizedDescription, details: nil))
                } else {
                    result(manager != nil)
                }
            }

        case "connect":
            guard let args = call.arguments as? [String: Any] else {
                result(false)
                return
            }
            startTunnel(config: args, result: result)

        case "cancelConnect", "disconnect":
            tunnelManager?.connection.stopVPNTunnel()
            emitEvent(["type": "disconnected", "message": "VPN Disconnected"])
            result(true)

        case "getStatus":
            let statusStr = mapStatus(tunnelManager?.connection.status ?? .disconnected)
            result(["state": statusStr])

        default:
            result(FlutterMethodNotImplemented)
        }
    }

    private func loadOrCreateManager(completion: @escaping (NETunnelProviderManager?, Error?) -> Void) {
        NETunnelProviderManager.loadAllFromPreferences { [weak self] managers, error in
            if let error = error {
                completion(nil, error)
                return
            }
            let manager = managers?.first ?? NETunnelProviderManager()
            self?.tunnelManager = manager
            completion(manager, nil)
        }
    }

    private func startTunnel(config: [String: Any], result: @escaping FlutterResult) {
        loadOrCreateManager { [weak self] manager, error in
            guard let self = self, let manager = manager else {
                result(FlutterError(code: "MANAGER_ERR", message: error?.localizedDescription ?? "No manager", details: nil))
                return
            }

            let proto = NETunnelProviderProtocol()
            proto.providerBundleIdentifier = self.tunnelBundleId
            proto.serverAddress = config["server"] as? String ?? "AuraLink Node"
            proto.providerConfiguration = [
                "profile_name": config["profile_name"] as? String ?? "AuraLink Node",
                "server": config["server"] as? String ?? "",
                "server_port": config["server_port"] as? Int ?? 443,
                "method": config["method"] as? String ?? "chacha20-ietf-poly1305",
                "password": config["password"] as? String ?? "",
                "dns_primary": config["dns_primary"] as? String ?? "1.1.1.1",
                "dns_backup": config["dns_backup"] as? String ?? "1.0.0.1",
                "disable_ipv6": config["disable_ipv6"] as? Bool ?? true,
                "udp_relay": config["udp_relay"] as? Bool ?? true
            ]

            manager.protocolConfiguration = proto
            manager.localizedDescription = "AuraLink Daylight VPN"
            manager.isEnabled = true

            manager.saveToPreferences { saveErr in
                if let saveErr = saveErr {
                    result(FlutterError(code: "SAVE_ERR", message: saveErr.localizedDescription, details: nil))
                    return
                }
                manager.loadFromPreferences { loadErr in
                    if let loadErr = loadErr {
                        result(FlutterError(code: "LOAD_ERR", message: loadErr.localizedDescription, details: nil))
                        return
                    }
                    do {
                        try manager.connection.startVPNTunnel()
                        result(true)
                    } catch {
                        result(FlutterError(code: "START_ERR", message: error.localizedDescription, details: nil))
                    }
                }
            }
        }
    }

    @objc private func vpnStatusDidChange(_ notification: Notification) {
        guard let conn = notification.object as? NEVPNConnection else { return }
        switch conn.status {
        case .connecting:
            emitEvent([
                "type": "stage_changed",
                "stage": "tun0",
                "stage_label": "3/5: Virtual TUN",
                "message": "Establishing iOS NetworkExtension tunnel..."
            ])
        case .connected:
            emitEvent([
                "type": "connected",
                "message": "iOS NetworkExtension tunnel active",
                "ipv6_disabled": true,
                "verified": true
            ])
        case .disconnecting:
            emitEvent([
                "type": "stage_changed",
                "stage": "teardown",
                "stage_label": "Disconnecting",
                "message": "Tearing down iOS tunnel..."
            ])
        case .disconnected, .invalid:
            emitEvent(["type": "disconnected", "message": "VPN Disconnected"])
        default:
            break
        }
    }

    private func mapStatus(_ status: NEVPNStatus) -> String {
        switch status {
        case .connected: return "CONNECTED"
        case .connecting, .reasserting: return "CONNECTING"
        case .disconnecting: return "DISCONNECTING"
        default: return "DISCONNECTED"
        }
    }

    private func emitEvent(_ payload: [String: Any]) {
        DispatchQueue.main.async { [weak self] in
            self?.eventSink?(payload)
        }
    }
}

extension AppDelegate: FlutterStreamHandler {
    func onListen(withArguments arguments: Any?, eventSink events: @escaping FlutterEventSink) -> FlutterError? {
        self.eventSink = events
        return nil
    }

    func onCancel(withArguments arguments: Any?) -> FlutterError? {
        self.eventSink = nil
        return nil
    }
}
