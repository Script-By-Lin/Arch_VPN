import NetworkExtension

/// iOS NEPacketTunnelProvider scaffold for AuraLink Daylight VPN.
///
/// Configures the iOS virtual TUN interface (`10.0.0.2/24`, MTU 1500, custom DNS,
/// and IPv6 leak shield). To enable live Shadowsocks packet forwarding on iOS,
/// embed `Libbox.xcframework` (sing-box) or `Tun2SocksKit.xcframework` into the
/// `PacketTunnel` Xcode Extension target and invoke it inside `startEngine(...)`.
class PacketTunnelProvider: NEPacketTunnelProvider {

    override func startTunnel(
        options: [String: NSObject]?,
        completionHandler: @escaping (Error?) -> Void
    ) {
        guard
            let proto = protocolConfiguration as? NETunnelProviderProtocol,
            let config = proto.providerConfiguration
        else {
            completionHandler(
                NSError(
                    domain: "com.auralink.vpn",
                    code: -1,
                    userInfo: [NSLocalizedDescriptionKey: "Missing AuraLink tunnel configuration."]
                )
            )
            return
        }

        let server = config["server"] as? String ?? "127.0.0.1"
        let dnsPrimary = config["dns_primary"] as? String ?? "1.1.1.1"
        let dnsBackup = config["dns_backup"] as? String ?? "1.0.0.1"
        let disableIpv6 = config["disable_ipv6"] as? Bool ?? true

        let settings = NEPacketTunnelNetworkSettings(tunnelRemoteAddress: server)
        settings.mtu = 1500

        // Full-tunnel IPv4 routing
        let ipv4 = NEIPv4Settings(addresses: ["10.0.0.2"], subnetMasks: ["255.255.255.0"])
        ipv4.includedRoutes = [NEIPv4Route.default()]
        settings.ipv4Settings = ipv4

        // IPv6 Leak Shield: route ::/0 into TUN so unproxied IPv6 never leaks to carrier/Wi-Fi
        if disableIpv6 {
            let ipv6 = NEIPv6Settings(addresses: ["fd00:auralink::2"], networkPrefixLengths: [128])
            ipv6.includedRoutes = [NEIPv6Route.default()]
            settings.ipv6Settings = ipv6
        }

        // Custom upstream DNS (match all domains via "")
        var dnsServers = [dnsPrimary]
        if !dnsBackup.isEmpty { dnsServers.append(dnsBackup) }
        let dns = NEDNSSettings(servers: dnsServers)
        dns.matchDomains = [""]
        settings.dnsSettings = dns

        setTunnelNetworkSettings(settings) { [weak self] error in
            if let error = error {
                completionHandler(error)
                return
            }
            // Hook: start sing-box / shadowsocks-rust + tun2socks native xcframework engine here
            self?.startNativePacketForwarder(config: config)
            completionHandler(nil)
        }
    }

    private func startNativePacketForwarder(config: [String: Any]) {
        // Attach self.packetFlow to your embedded Shadowsocks/sing-box xcframework engine.
        // See mobile/README.md for build instructions.
        _ = config
    }

    override func stopTunnel(
        with reason: NEProviderStopReason,
        completionHandler: @escaping () -> Void
    ) {
        // Stop embedded native Shadowsocks/tun2socks engine cleanly here.
        completionHandler()
    }
}
