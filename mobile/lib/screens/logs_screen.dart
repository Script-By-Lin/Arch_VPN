import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../models/vpn_models.dart';
import '../services/vpn_controller.dart';
import '../theme/daylight_theme.dart';

/// Clean line-by-line color-coded real-time log terminal with Wrap toggle, Clear, and Copy.
class LogsScreen extends StatelessWidget {
  const LogsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<VpnController>(
      builder: (context, ctrl, _) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 12),
            child: Column(
              children: [
                Row(
                  children: [
                    const Text(
                      '>_ Log Stream',
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w800,
                        fontFamily: 'monospace',
                        color: DaylightColors.textPrimary,
                      ),
                    ),
                    const Spacer(),
                    _MiniActionChip(
                      label: ctrl.logWrap ? 'Wrap: On' : 'Wrap: Off',
                      onTap: ctrl.toggleLogWrap,
                    ),
                    const SizedBox(width: 6),
                    _MiniActionChip(
                      label: 'Copy',
                      onTap: () {
                        final text =
                            ctrl.logs.map((e) => e.toPlainLine()).join('\n');
                        Clipboard.setData(ClipboardData(text: text));
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('Logs copied to clipboard'),
                            duration: Duration(seconds: 1),
                          ),
                        );
                      },
                    ),
                    const SizedBox(width: 6),
                    _MiniActionChip(
                      label: 'Clear',
                      onTap: ctrl.clearLogs,
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Expanded(
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: DaylightColors.bgSurface,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: DaylightColors.border),
                    ),
                    child: ctrl.logs.isEmpty
                        ? const Center(
                            child: Text(
                              'No log entries yet.',
                              style: TextStyle(
                                fontFamily: 'monospace',
                                color: DaylightColors.textSubtle,
                              ),
                            ),
                          )
                        : ListView.builder(
                            reverse: false,
                            itemCount: ctrl.logs.length,
                            itemBuilder: (context, idx) {
                              final entry = ctrl.logs[idx];
                              return _LogLineRow(
                                entry: entry,
                                wrap: ctrl.logWrap,
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

class _LogLineRow extends StatelessWidget {
  final LogEntry entry;
  final bool wrap;

  const _LogLineRow({required this.entry, required this.wrap});

  Color _levelColor() {
    switch (entry.level) {
      case LogLevel.ok:
        return DaylightColors.success;
      case LogLevel.warn:
        return DaylightColors.warning;
      case LogLevel.error:
        return DaylightColors.danger;
      case LogLevel.debug:
        return DaylightColors.textSubtle;
      case LogLevel.info:
        return DaylightColors.primary;
    }
  }

  @override
  Widget build(BuildContext context) {
    final content = Text.rich(
      TextSpan(
        style: const TextStyle(
          fontSize: 11,
          height: 1.45,
          fontFamily: 'monospace',
          color: DaylightColors.textPrimary,
        ),
        children: [
          TextSpan(
            text: '[${entry.timeFormatted}] ',
            style: const TextStyle(color: DaylightColors.textSubtle),
          ),
          TextSpan(
            text: '[${entry.source}] ',
            style: const TextStyle(
              color: Color(0xFF7C3AED),
              fontWeight: FontWeight.w700,
            ),
          ),
          TextSpan(
            text: '${entry.levelTag.padRight(4)} ',
            style: TextStyle(
              color: _levelColor(),
              fontWeight: FontWeight.w800,
            ),
          ),
          TextSpan(text: entry.message),
        ],
      ),
      softWrap: wrap,
      maxLines: wrap ? null : 1,
    );

    if (wrap) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 2),
        child: content,
      );
    }

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: content,
      ),
    );
  }
}

class _MiniActionChip extends StatelessWidget {
  final String label;
  final VoidCallback onTap;

  const _MiniActionChip({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(7),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
        decoration: BoxDecoration(
          color: DaylightColors.bgSurface,
          borderRadius: BorderRadius.circular(7),
          border: Border.all(color: DaylightColors.borderLight),
        ),
        child: Text(
          label,
          style: const TextStyle(
            fontSize: 10.5,
            fontWeight: FontWeight.w700,
            fontFamily: 'monospace',
            color: DaylightColors.textSecondary,
          ),
        ),
      ),
    );
  }
}
