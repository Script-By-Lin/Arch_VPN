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
                  value: DnsPreset.presets.any((p) => p.name == s.dnsPresetName)
                      ? s.dnsPresetName
                      : DnsPreset.presets.first.name,
                  decoration: const InputDecoration(isDense: true),
                  items: DnsPreset.presets
                      .map(
                        (p) => DropdownMenuItem<String>(
                          value: p.name,
                          child: Text(
                            p.name,
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
              const SizedBox(height: 12),
              // Engine Backend Card
              _SectionCard(
                title: 'VPN ENGINE BACKEND',
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          ctrl.nativeEngineAvailable
                              ? Icons.verified_rounded
                              : Icons.science_rounded,
                          size: 18,
                          color: ctrl.nativeEngineAvailable
                              ? DaylightColors.success
                              : DaylightColors.warning,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            ctrl.nativeEngineAvailable
                                ? 'Native VpnService / NetworkExtension detected'
                                : 'Native binaries not bundled — Demo fallback active',
                            style: const TextStyle(
                              fontSize: 12.5,
                              fontWeight: FontWeight.w700,
                              color: DaylightColors.textPrimary,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    SwitchListTile.adaptive(
                      contentPadding: EdgeInsets.zero,
                      title: const Text(
                        'Force Demo Mode',
                        style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600),
                      ),
                      subtitle: const Text(
                        'Simulate the 5-stage tunnel pipeline & sparklines without OS VPN permission.',
                        style: TextStyle(fontSize: 11.5, color: DaylightColors.textMuted),
                      ),
                      value: s.demoMode,
                      onChanged: (v) => ctrl.updateSettings(demoMode: v),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              _FreeBackendUrlCard(
                initialUrl: s.freeKeysBackendUrl,
                onSave: (url) async {
                  await ctrl.updateFreeKeysBackendUrl(url);
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Updated Free Keys Backend URL & refreshed regions'),
                        backgroundColor: DaylightColors.success,
                      ),
                    );
                  }
                },
              ),
            ],
          ),
        );
      },
    );
  }
}

class _FreeBackendUrlCard extends StatefulWidget {
  final String initialUrl;
  final Future<void> Function(String url) onSave;

  const _FreeBackendUrlCard({
    required this.initialUrl,
    required this.onSave,
  });

  @override
  State<_FreeBackendUrlCard> createState() => _FreeBackendUrlCardState();
}

class _FreeBackendUrlCardState extends State<_FreeBackendUrlCard> {
  late final TextEditingController _ctrl;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _ctrl = TextEditingController(text: widget.initialUrl);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return _SectionCard(
      title: 'MOBILE FREE KEYS ADMIN BACKEND',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text(
            'Endpoint used by the Mobile Free Regions tab (GET /api/mobile/free-keys).',
            style: TextStyle(fontSize: 12, color: DaylightColors.textMuted),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _ctrl,
            keyboardType: TextInputType.url,
            decoration: const InputDecoration(
              hintText: 'https://your-admin-backend.example.com',
              isDense: true,
            ),
          ),
          const SizedBox(height: 8),
          FilledButton.icon(
            onPressed: _saving
                ? null
                : () async {
                    setState(() => _saving = true);
                    await widget.onSave(_ctrl.text);
                    if (mounted) setState(() => _saving = false);
                  },
            style: FilledButton.styleFrom(
              backgroundColor: DaylightColors.primary,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
            ),
            icon: _saving
                ? const SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.cloud_sync_rounded, size: 17),
            label: Text(_saving ? 'Syncing...' : 'Save & Sync Free Regions'),
          ),
        ],
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  final String title;
  final Widget child;

  const _SectionCard({required this.title, required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: DaylightColors.bgSurface,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: DaylightColors.border),
      ),
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
    );
  }
}
