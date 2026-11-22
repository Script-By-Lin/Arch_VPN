import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../models/vpn_models.dart';
import '../services/vpn_controller.dart';
import '../theme/daylight_theme.dart';
import '../widgets/circular_connect_button.dart';
import '../widgets/interactive_tunnel_model.dart';
import '../widgets/speed_sparkline_cards.dart';

class HomeScreen extends StatelessWidget {
  final VoidCallback onOpenServers;

  const HomeScreen({super.key, required this.onOpenServers});

  @override
  Widget build(BuildContext context) {
    return Consumer<VpnController>(
      builder: (context, ctrl, _) {
        final profile = ctrl.activeProfile;
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 12),
            child: Column(
              children: [
                _buildHeader(context, ctrl),
                const SizedBox(height: 12),
                // Main elevated Daylight hub card (connect button centered, pipeline & speed docked cleanly at bottom)
                Expanded(
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: DaylightColors.bgSurface,
                      borderRadius: BorderRadius.circular(22),
                      border: Border.all(color: DaylightColors.border),
                      boxShadow: [
                        BoxShadow(
                          color: DaylightColors.textPrimary.withValues(alpha: 0.05),
                          blurRadius: 20,
                          offset: const Offset(0, 6),
                        ),
                      ],
                    ),
                    child: Column(
                      children: [
                        // Active node quick selector pill at top of card
                        _ActiveNodeBar(
                          profile: profile,
                          onTap: onOpenServers,
                          onImport: () => _showQuickImportSheet(context, ctrl),
                        ),
                        const Spacer(),
                        CircularConnectButton(
                          state: ctrl.state,
                          onTap: ctrl.toggleConnection,
                        ),
                        const SizedBox(height: 10),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          child: Text(
                            ctrl.statusMessage,
                            textAlign: TextAlign.center,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              fontSize: 11.5,
                              fontFamily: 'monospace',
                              fontWeight: ctrl.state == VpnConnectionState.connected
                                  ? FontWeight.w700
                                  : FontWeight.w500,
                              color: ctrl.state == VpnConnectionState.connected
                                  ? DaylightColors.successDark
                                  : ctrl.state == VpnConnectionState.error
                                      ? DaylightColors.danger
                                      : DaylightColors.textMuted,
                            ),
                          ),
                        ),
                        const Spacer(),
                        // Bottom-docked Interactive 4-Hop Tunnel Model
                        InteractiveTunnelModel(
                          state: ctrl.state,
                          stage: ctrl.stage,
                          profile: profile,
                          settings: ctrl.settings,
                          stats: ctrl.stats,
                          ipv6ShieldActive: ctrl.ipv6ShieldActive,
                          lastError: ctrl.lastError,
                        ),
                        const SizedBox(height: 10),
                        // Bottom-docked dual speed sparkline tiles
                        SpeedSparklineCards(stats: ctrl.stats),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildHeader(BuildContext context, VpnController ctrl) {
    final isConn = ctrl.state == VpnConnectionState.connected;
    final isBusy = ctrl.state == VpnConnectionState.connecting ||
        ctrl.state == VpnConnectionState.disconnecting;
    final isErr = ctrl.state == VpnConnectionState.error;

    final pillBg = isConn
        ? DaylightColors.successSoft
        : isBusy
            ? DaylightColors.warningSoft
            : isErr
                ? DaylightColors.dangerSoft
                : DaylightColors.bgSurface;
    final pillBorder = isConn
        ? DaylightColors.successBorder
        : isBusy
            ? DaylightColors.warningBorder
            : isErr
                ? DaylightColors.dangerBorder
                : DaylightColors.borderLight;
    final pillFg = isConn
        ? DaylightColors.successDark
        : isBusy
            ? DaylightColors.warningDark
            : isErr
                ? DaylightColors.dangerDark
                : DaylightColors.textSecondary;
    final statusLabel = isConn
        ? 'CONNECTED'
        : ctrl.state == VpnConnectionState.connecting
            ? 'CONNECTING'
            : ctrl.state == VpnConnectionState.disconnecting
                ? 'STOPPING'
                : isErr
                    ? 'ERROR'
                    : 'IDLE';

    return Row(
      children: [
        Expanded(
          child: Row(
            children: [
              const Flexible(
                child: Text(
                  'AuraLink',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w800,
                    color: DaylightColors.textPrimary,
                    letterSpacing: -0.3,
                  ),
                ),
              ),
              const SizedBox(width: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: DaylightColors.primarySoft,
                  borderRadius: BorderRadius.circular(7),
                  border: Border.all(color: DaylightColors.primaryBorder),
                ),
                child: Text(
                  ctrl.isUsingDemoEngine ? 'DEMO' : 'DAYLIGHT',
                  style: const TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.w800,
                    fontFamily: 'monospace',
                    color: DaylightColors.primaryDark,
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 6),
        // IPv6 Shield pill
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 4),
          decoration: BoxDecoration(
            color: ctrl.ipv6ShieldActive
                ? DaylightColors.successSoft
                : DaylightColors.bgSurface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: ctrl.ipv6ShieldActive
                  ? DaylightColors.successBorder
                  : DaylightColors.borderLight,
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.shield_outlined,
                size: 11,
                color: ctrl.ipv6ShieldActive
                    ? DaylightColors.successDark
                    : DaylightColors.textMuted,
              ),
              const SizedBox(width: 3),
              Text(
                ctrl.ipv6ShieldActive ? 'IPv6 OFF' : 'IPv6',
                style: TextStyle(
                  fontSize: 9,
                  fontWeight: FontWeight.w700,
                  fontFamily: 'monospace',
                  color: ctrl.ipv6ShieldActive
                      ? DaylightColors.successDark
                      : DaylightColors.textMuted,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 6),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
          decoration: BoxDecoration(
            color: pillBg,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: pillBorder),
          ),
          child: Text(
            statusLabel,
            style: TextStyle(
              fontSize: 9.5,
              fontWeight: FontWeight.w800,
              fontFamily: 'monospace',
              color: pillFg,
            ),
          ),
        ),
      ],
    );
  }

  void _showQuickImportSheet(BuildContext context, VpnController ctrl) {
    final textCtrl = TextEditingController();
    bool loading = false;
    String? errText;

    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: DaylightColors.bgSurface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
      ),
      builder: (sheetCtx) {
        return StatefulBuilder(
          builder: (ctx, setSheetState) {
            return Padding(
              padding: EdgeInsets.fromLTRB(
                20,
                16,
                20,
                MediaQuery.of(ctx).viewInsets.bottom + 20,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    children: [
                      const Text(
                        'Import Shadowsocks Key',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                          color: DaylightColors.textPrimary,
                        ),
                      ),
                      const Spacer(),
                      TextButton.icon(
                        onPressed: () async {
                          final clip = await Clipboard.getData(Clipboard.kTextPlain);
                          if (clip?.text != null) {
                            textCtrl.text = clip!.text!.trim();
                          }
                        },
                        icon: const Icon(Icons.paste_rounded, size: 16),
                        label: const Text('Paste'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: textCtrl,
                    maxLines: 3,
                    minLines: 2,
                    decoration: const InputDecoration(
                      hintText: 'ssconf://..., ss://..., https://..., or JSON config',
                    ),
                  ),
                  if (errText != null) ...[
                    const SizedBox(height: 8),
                    Text(
                      errText!,
                      style: const TextStyle(
                        color: DaylightColors.danger,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                  const SizedBox(height: 14),
                  FilledButton.icon(
                    style: FilledButton.styleFrom(
                      backgroundColor: DaylightColors.primary,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    onPressed: loading
                        ? null
                        : () async {
                            setSheetState(() {
                              loading = true;
                              errText = null;
                            });
                            try {
                              final prof = await ctrl.importKey(textCtrl.text);
                              if (ctx.mounted) {
                                Navigator.of(ctx).pop();
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(
                                    content: Text('Imported ${prof.name}'),
                                    backgroundColor: DaylightColors.success,
                                  ),
                                );
                              }
                            } catch (e) {
                              setSheetState(() {
                                loading = false;
                                errText = e.toString();
                              });
                            }
                          },
                    icon: loading
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.add_link_rounded),
                    label: Text(loading ? 'Fetching & Validating...' : 'Import Node'),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }
}

class _ActiveNodeBar extends StatelessWidget {
  final VpnProfile? profile;
  final VoidCallback onTap;
  final VoidCallback onImport;

  const _ActiveNodeBar({
    required this.profile,
    required this.onTap,
    required this.onImport,
  });

  @override
  Widget build(BuildContext context) {
    final ping = profile?.lastPingMs;
    final pingText = ping == null
        ? 'Ping --'
        : ping < 0
            ? 'Timeout'
            : '${ping}ms';

    return Row(
      children: [
        Expanded(
          child: InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(12),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
              decoration: BoxDecoration(
                color: DaylightColors.bgCard,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: DaylightColors.border),
              ),
              child: Row(
                children: [
                  const Icon(Icons.dns_rounded, size: 17, color: DaylightColors.primary),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          profile?.name ?? 'No Server Selected',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 12.5,
                            fontWeight: FontWeight.w700,
                            color: DaylightColors.textPrimary,
                          ),
                        ),
                        if (profile != null)
                          Text(
                            '${profile!.server}:${profile!.serverPort} • $pingText',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 10,
                              fontFamily: 'monospace',
                              color: DaylightColors.textMuted,
                            ),
                          ),
                      ],
                    ),
                  ),
                  const Icon(Icons.chevron_right_rounded,
                      size: 18, color: DaylightColors.textSubtle),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(width: 8),
        InkWell(
          onTap: onImport,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            height: 48,
            width: 48,
            decoration: BoxDecoration(
              color: DaylightColors.primarySoft,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: DaylightColors.primaryBorder),
            ),
            child: const Icon(Icons.add_rounded, color: DaylightColors.primaryDark),
          ),
        ),
      ],
    );
  }
}
