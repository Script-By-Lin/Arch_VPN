import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/vpn_models.dart';
import '../services/vpn_controller.dart';
import '../theme/daylight_theme.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<VpnController>(
      builder: (context, ctrl, _) {
        final s = ctrl.settings;
        return SafeArea(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 20),
            children: [
              const Text(
                'Tunnel & Network Settings',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                  color: DaylightColors.textPrimary,
                ),
              ),
              const SizedBox(height: 12),
              // Upstream DNS Preset Card
              _SectionCard(
                title: 'DNS UPSTREAM RESOLVER',
                child: DropdownButtonFormField<String>(
                  isExpanded: true,
                  initialValue: DnsPreset.presets.any((p) => p.name == s.dnsPresetName)
                      ? s.dnsPresetName
                      : DnsPreset.presets.first.name,
                  decoration: const InputDecoration(isDense: true),
                  items: DnsPreset.presets
                      .map(
                        (p) => DropdownMenuItem<String>(
                          value: p.name,
                          child: Text(
                            p.name,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 13),
                          ),
                        ),
                      )
                      .toList(),
                  onChanged: (val) {
                    if (val != null) {
                      ctrl.updateDnsPreset(DnsPreset.byName(val));
                    }
                  },
                ),
              ),
              const SizedBox(height: 12),
              // Protection & Performance Toggles
              _SectionCard(
                title: 'SECURITY & PERFORMANCE',
                child: Column(
                  children: [
                    SwitchListTile.adaptive(
                      contentPadding: EdgeInsets.zero,
                      title: const Text(
                        'IPv6 Leak Shield',
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                      ),
                      subtitle: const Text(
                        'Blocks non-tunneled IPv6 traffic while VPN is active.',
                        style: TextStyle(fontSize: 12, color: DaylightColors.textMuted),
                      ),
                      value: s.disableIpv6,
                      onChanged: (v) => ctrl.updateSettings(disableIpv6: v),
                    ),
                    const Divider(height: 1, color: DaylightColors.border),
                    SwitchListTile.adaptive(
                      contentPadding: EdgeInsets.zero,
                      title: const Text(
                        'TCP + UDP Relay (Fast DNS / QUIC)',
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                      ),
                      subtitle: const Text(
                        'Enables Shadowsocks UDP ASSOCIATE + TCP_NODELAY to avoid 10s DNS fallback timeouts.',
                        style: TextStyle(fontSize: 12, color: DaylightColors.textMuted),
                      ),
                      value: s.udpRelay,
                      onChanged: (v) => ctrl.updateSettings(udpRelay: v),
                    ),
                    const Divider(height: 1, color: DaylightColors.border),
                    SwitchListTile.adaptive(
                      contentPadding: EdgeInsets.zero,
                      title: const Text(
                        'Verify Internet Before Connected',
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                      ),
                      subtitle: const Text(
                        'Stage 5/5 probe confirms real DNS & HTTP flow over TUN before turning green.',
                        style: TextStyle(fontSize: 12, color: DaylightColors.textMuted),
                      ),
                      value: s.verifyTunnel,
                      onChanged: (v) => ctrl.updateSettings(verifyTunnel: v),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _SectionCard extends StatelessWidget {
  final String title;
  final Widget child;

  const _SectionCard({required this.title, required this.child});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: DaylightColors.bgSurface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(18),
        side: const BorderSide(color: DaylightColors.border),
      ),
      clipBehavior: Clip.antiAlias,
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w800,
                fontFamily: 'monospace',
                letterSpacing: 0.7,
                color: DaylightColors.textMuted,
              ),
            ),
            const SizedBox(height: 10),
            child,
          ],
        ),
      ),
    );
  }
}
