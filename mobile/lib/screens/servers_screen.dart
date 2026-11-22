import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../models/vpn_models.dart';
import '../services/vpn_controller.dart';
import '../theme/daylight_theme.dart';

class ServersScreen extends StatefulWidget {
  const ServersScreen({super.key});

  @override
  State<ServersScreen> createState() => _ServersScreenState();
}

class _ServersScreenState extends State<ServersScreen> {
  final TextEditingController _keyController = TextEditingController();
  bool _importing = false;
  bool _pingingAll = false;

  @override
  void dispose() {
    _keyController.dispose();
    super.dispose();
  }

  Future<void> _handleImport(VpnController ctrl) async {
    final text = _keyController.text.trim();
    if (text.isEmpty) return;
    setState(() => _importing = true);
    try {
      final prof = await ctrl.importKey(text);
      _keyController.clear();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Imported ${prof.name}'),
            backgroundColor: DaylightColors.success,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.toString()),
            backgroundColor: DaylightColors.danger,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _importing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<VpnController>(
      builder: (context, ctrl, _) {
        final activeId = ctrl.activeProfile?.id;
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    const Text(
                      'VPN Nodes',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w800,
                        color: DaylightColors.textPrimary,
                      ),
                    ),
                    const Spacer(),
                    OutlinedButton.icon(
                      onPressed: _pingingAll
                          ? null
                          : () async {
                              setState(() => _pingingAll = true);
                              await ctrl.pingAllProfiles();
                              if (mounted) setState(() => _pingingAll = false);
                            },
                      icon: _pingingAll
                          ? const SizedBox(
                              width: 14,
                              height: 14,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.speed_rounded, size: 16),
                      label: const Text('Ping All'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: DaylightColors.primaryDark,
                        side: const BorderSide(color: DaylightColors.primaryBorder),
                        backgroundColor: DaylightColors.primarySoft,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                // Quick Import Input Card
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: DaylightColors.bgSurface,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: DaylightColors.border),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _keyController,
                              decoration: const InputDecoration(
                                hintText: 'Paste ssconf://, ss://, or JSON...',
                                isDense: true,
                              ),
                              onSubmitted: (_) => _handleImport(ctrl),
                            ),
                          ),
                          const SizedBox(width: 8),
                          IconButton.filledTonal(
                            tooltip: 'Paste from clipboard',
                            onPressed: () async {
                              final clip =
                                  await Clipboard.getData(Clipboard.kTextPlain);
                              if (clip?.text != null) {
                                _keyController.text = clip!.text!.trim();
                              }
                            },
                            icon: const Icon(Icons.paste_rounded, size: 18),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      FilledButton.icon(
                        onPressed: _importing ? null : () => _handleImport(ctrl),
                        style: FilledButton.styleFrom(
                          backgroundColor: DaylightColors.primary,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                        ),
                        icon: _importing
                            ? const SizedBox(
                                width: 15,
                                height: 15,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.add_rounded, size: 18),
                        label: Text(_importing ? 'Importing...' : 'Add Server Node'),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                Expanded(
                  child: ctrl.profiles.isEmpty
                      ? const Center(
                          child: Text(
                            'No profiles saved yet.\nPaste an ss:// or ssconf:// key above.',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: DaylightColors.textMuted),
                          ),
                        )
                      : ListView.separated(
                          itemCount: ctrl.profiles.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 8),
                          itemBuilder: (context, index) {
                            final prof = ctrl.profiles[index];
                            final selected = prof.id == activeId;
                            return _ProfileCard(
                              profile: prof,
                              selected: selected,
                              isConnected: selected &&
                                  ctrl.state == VpnConnectionState.connected,
                              onSelect: () => ctrl.selectProfile(prof.id),
                              onPing: () => ctrl.pingProfile(prof.id),
                              onDelete: () => _confirmDelete(context, ctrl, prof),
                            );
                          },
                        ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _confirmDelete(
    BuildContext context,
    VpnController ctrl,
    VpnProfile prof,
  ) {
    final isActiveConn = ctrl.activeProfile?.id == prof.id &&
        ctrl.state == VpnConnectionState.connected;
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: DaylightColors.bgSurface,
        title: const Text('Delete Server Profile?'),
        content: Text(
          isActiveConn
              ? 'This node is currently connected. Deleting "${prof.name}" will disconnect the VPN first.'
              : 'Remove "${prof.name}" (${prof.server}:${prof.serverPort}) from saved profiles?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: DaylightColors.danger),
            onPressed: () {
              Navigator.of(ctx).pop();
              ctrl.deleteProfile(prof.id);
            },
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }
}

class _ProfileCard extends StatelessWidget {
  final VpnProfile profile;
  final bool selected;
  final bool isConnected;
  final VoidCallback onSelect;
  final VoidCallback onPing;
  final VoidCallback onDelete;

  const _ProfileCard({
    required this.profile,
    required this.selected,
    required this.isConnected,
    required this.onSelect,
    required this.onPing,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final ping = profile.lastPingMs;
    final pingColor = ping == null
        ? DaylightColors.textMuted
        : ping < 0
            ? DaylightColors.danger
            : ping < 150
                ? DaylightColors.success
                : DaylightColors.warning;
    final pingText = ping == null
        ? '--'
        : ping < 0
            ? 'Timeout'
            : '${ping}ms';

    return InkWell(
      onTap: onSelect,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(13),
        decoration: BoxDecoration(
          color: selected ? DaylightColors.bgCardHover : DaylightColors.bgSurface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isConnected
                ? DaylightColors.successBright
                : selected
                    ? DaylightColors.primary
                    : DaylightColors.border,
            width: selected ? 1.5 : 1.0,
          ),
        ),
        child: Row(
          children: [
            Icon(
              isConnected
                  ? Icons.check_circle_rounded
                  : selected
                      ? Icons.radio_button_checked_rounded
                      : Icons.radio_button_unchecked_rounded,
              color: isConnected
                  ? DaylightColors.success
                  : selected
                      ? DaylightColors.primary
                      : DaylightColors.borderLight,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    profile.name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 13.5,
                      fontWeight: FontWeight.w700,
                      color: DaylightColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '${profile.server}:${profile.serverPort} • ${profile.method}',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 10.5,
                      fontFamily: 'monospace',
                      color: DaylightColors.textMuted,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 6),
            InkWell(
              onTap: onPing,
              borderRadius: BorderRadius.circular(8),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: DaylightColors.bgCard,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: DaylightColors.border),
                ),
                child: Text(
                  pingText,
                  style: TextStyle(
                    fontSize: 10.5,
                    fontWeight: FontWeight.w700,
                    fontFamily: 'monospace',
                    color: pingColor,
                  ),
                ),
              ),
            ),
            IconButton(
              onPressed: onDelete,
              icon: const Icon(Icons.delete_outline_rounded, size: 19),
              color: DaylightColors.danger,
              tooltip: 'Delete profile',
            ),
          ],
        ),
      ),
    );
  }
}
