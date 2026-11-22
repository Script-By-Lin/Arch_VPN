import 'package:flutter/material.dart';

import '../models/free_key_region.dart';
import '../theme/daylight_theme.dart';

/// Daylight Region Card displaying a published FREE VPN key from the Admin Backend.
class FreeRegionCard extends StatelessWidget {
  final FreeRegionKey item;
  final bool isActive;
  final bool isConnected;
  final bool isConnecting;
  final VoidCallback onConnect;
  final VoidCallback onPing;

  const FreeRegionCard({
    super.key,
    required this.item,
    required this.isActive,
    required this.isConnected,
    required this.isConnecting,
    required this.onConnect,
    required this.onPing,
  });

  @override
  Widget build(BuildContext context) {
    final ping = item.lastPingMs;
    final pingText = ping == null
        ? 'Ping'
        : ping < 0
            ? 'Timeout'
            : '${ping}ms';
    final pingColor = ping == null
        ? DaylightColors.textMuted
        : ping < 0
            ? DaylightColors.danger
            : ping < 150
                ? DaylightColors.success
                : DaylightColors.warning;

    final borderColor = isConnected
        ? DaylightColors.successBright
        : isConnecting
            ? DaylightColors.warningBright
            : isActive
                ? DaylightColors.primary
                : DaylightColors.border;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isConnected ? DaylightColors.successSoft.withOpacity(0.45) : DaylightColors.bgSurface,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: borderColor, width: isActive ? 1.6 : 1.0),
        boxShadow: [
          BoxShadow(
            color: DaylightColors.textPrimary.withOpacity(0.04),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              // Region Flag Tile
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: DaylightColors.bgCard,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: DaylightColors.border),
                ),
                alignment: Alignment.center,
                child: Text(
                  item.flag,
                  style: const TextStyle(fontSize: 22),
                ),
              ),
              const SizedBox(width: 11),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Flexible(
                          child: Text(
                            item.city.isNotEmpty
                                ? '${item.region} • ${item.city}'
                                : item.region,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w800,
                              color: DaylightColors.textPrimary,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 2),
                    Text(
                      item.label,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: DaylightColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: DaylightColors.successSoft,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: DaylightColors.successBorder),
                ),
                child: Text(
                  item.tier,
                  style: const TextStyle(
                    fontSize: 9.5,
                    fontWeight: FontWeight.w800,
                    fontFamily: 'monospace',
                    color: DaylightColors.successDark,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: Text(
                  '${item.countryCode} • ${item.method}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 10.5,
                    fontFamily: 'monospace',
                    color: DaylightColors.textMuted,
                  ),
                ),
              ),
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
              const SizedBox(width: 8),
              FilledButton(
                onPressed: onConnect,
                style: FilledButton.styleFrom(
                  backgroundColor: isConnected
                      ? DaylightColors.success
                      : isConnecting
                          ? DaylightColors.warning
                          : DaylightColors.primary,
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  minimumSize: Size.zero,
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),
                child: Text(
                  isConnected
                      ? 'Connected'
                      : isConnecting
                          ? 'Cancel'
                          : 'Connect',
                  style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w700),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
