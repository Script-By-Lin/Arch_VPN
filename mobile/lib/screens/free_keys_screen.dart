import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/vpn_models.dart';
import '../services/vpn_controller.dart';
import '../theme/daylight_theme.dart';
import '../widgets/free_region_card.dart';

/// Mobile-only Free Region Cards screen powered by the Admin Backend (`GET /api/mobile/free-keys`).
class FreeKeysScreen extends StatefulWidget {
  final VoidCallback onJumpToTunnel;

  const FreeKeysScreen({super.key, required this.onJumpToTunnel});

  @override
  State<FreeKeysScreen> createState() => _FreeKeysScreenState();
}

class _FreeKeysScreenState extends State<FreeKeysScreen> {
  String _selectedRegion = 'All';
  bool _pinging = false;

  @override
  Widget build(BuildContext context) {
    return Consumer<VpnController>(
      builder: (context, ctrl, _) {
        final allKeys = ctrl.freeRegionKeys;
        final regionNames = <String>['All'];
        for (final k in allKeys) {
          if (!regionNames.contains(k.region)) {
            regionNames.add(k.region);
          }
        }
        if (!regionNames.contains(_selectedRegion)) {
          _selectedRegion = 'All';
        }

        final visibleKeys = _selectedRegion == 'All'
            ? allKeys
            : allKeys.where((k) => k.region == _selectedRegion).toList();

        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Header
                Row(
                  children: [
                    const Text(
                      'Free Regions',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w800,
                        color: DaylightColors.textPrimary,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                      decoration: BoxDecoration(
                        color: DaylightColors.successSoft,
                        borderRadius: BorderRadius.circular(7),
                        border: Border.all(color: DaylightColors.successBorder),
                      ),
                      child: const Text(
                        'FREE',
                        style: TextStyle(
                          fontSize: 9.5,
                          fontWeight: FontWeight.w800,
                          fontFamily: 'monospace',
                          color: DaylightColors.successDark,
                        ),
                      ),
                    ),
                    const Spacer(),
                    IconButton.filledTonal(
                      tooltip: 'Ping all free regions',
                      onPressed: (_pinging || allKeys.isEmpty)
                          ? null
                          : () async {
                              setState(() => _pinging = true);
                              await ctrl.pingAllFreeRegionKeys();
                              if (mounted) setState(() => _pinging = false);
                            },
                      icon: _pinging
                          ? const SizedBox(
                              width: 15,
                              height: 15,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.speed_rounded, size: 18),
                    ),
                    const SizedBox(width: 4),
                    IconButton.filledTonal(
                      tooltip: 'Refresh from Admin Backend',
                      onPressed: ctrl.loadingFreeKeys ? null : ctrl.fetchFreeRegionKeys,
                      icon: ctrl.loadingFreeKeys
                          ? const SizedBox(
                              width: 15,
                              height: 15,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.refresh_rounded, size: 18),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                // Region Filter Chips
                if (regionNames.length > 1)
                  SizedBox(
                    height: 36,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      itemCount: regionNames.length,
                      separatorBuilder: (_, __) => const SizedBox(width: 8),
                      itemBuilder: (context, idx) {
                        final reg = regionNames[idx];
                        final selected = reg == _selectedRegion;
                        return ChoiceChip(
                          label: Text(reg),
                          selected: selected,
                          onSelected: (_) => setState(() => _selectedRegion = reg),
                          selectedColor: DaylightColors.primarySoft,
                          backgroundColor: DaylightColors.bgSurface,
                          side: BorderSide(
                            color: selected
                                ? DaylightColors.primary
                                : DaylightColors.borderLight,
                          ),
                          labelStyle: TextStyle(
                            fontSize: 11.5,
                            fontWeight: FontWeight.w700,
                            color: selected
                                ? DaylightColors.primaryDark
                                : DaylightColors.textSecondary,
                          ),
                        );
                      },
                    ),
                  ),
                if (ctrl.freeKeysError != null) ...[
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: DaylightColors.warningSoft,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: DaylightColors.warningBorder),
                    ),
                    child: Text(
                      'Admin Backend (${ctrl.settings.freeKeysBackendUrl}): ${ctrl.freeKeysError}',
                      style: const TextStyle(
                        fontSize: 11,
                        fontFamily: 'monospace',
                        color: DaylightColors.warningDark,
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 10),
                // Region Cards List
                Expanded(
                  child: RefreshIndicator(
                    onRefresh: ctrl.fetchFreeRegionKeys,
                    child: visibleKeys.isEmpty
                        ? ListView(
                            children: [
                              const SizedBox(height: 60),
                              Icon(
                                Icons.public_rounded,
                                size: 48,
                                color: DaylightColors.borderLight,
                              ),
                              const SizedBox(height: 12),
                              const Text(
                                'No published free region keys yet',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  fontSize: 15,
                                  fontWeight: FontWeight.w700,
                                  color: DaylightColors.textPrimary,
                                ),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                'Upload keys from your Admin Panel at\n${ctrl.settings.freeKeysBackendUrl}/admin\nthen pull down to refresh.',
                                textAlign: TextAlign.center,
                                style: const TextStyle(
                                  fontSize: 12,
                                  fontFamily: 'monospace',
                                  color: DaylightColors.textMuted,
                                ),
                              ),
                            ],
                          )
                        : ListView.separated(
                            itemCount: visibleKeys.length,
                            separatorBuilder: (_, __) => const SizedBox(height: 10),
                            itemBuilder: (context, idx) {
                              final item = visibleKeys[idx];
                              final isActive = ctrl.activeProfile?.id == item.profileId;
                              final isConn = isActive &&
                                  ctrl.state == VpnConnectionState.connected;
                              final isBusy = isActive &&
                                  ctrl.state == VpnConnectionState.connecting;
                              return FreeRegionCard(
                                item: item,
                                isActive: isActive,
                                isConnected: isConn,
                                isConnecting: isBusy,
                                onPing: () => ctrl.pingFreeRegionKey(item.id),
                                onConnect: () async {
                                  if (isConn) {
                                    await ctrl.disconnect();
                                  } else if (isBusy) {
                                    await ctrl.cancelConnect();
                                  } else {
                                    widget.onJumpToTunnel();
                                    await ctrl.connectToFreeRegionKey(item);
                                  }
                                },
                              );
                            },
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
}
