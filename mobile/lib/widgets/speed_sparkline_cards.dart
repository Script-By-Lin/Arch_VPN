import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../models/vpn_models.dart';
import '../theme/daylight_theme.dart';

/// Dual DOWNLOAD / UPLOAD telemetry tiles with SESSION totals and live sparkline waveforms.
class SpeedSparklineCards extends StatelessWidget {
  final TrafficStats stats;

  const SpeedSparklineCards({super.key, required this.stats});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _SpeedTile(
            label: 'DOWNLOAD',
            speedText: stats.rxSpeedFormatted,
            sessionText: stats.rxTotalFormatted,
            icon: Icons.arrow_downward_rounded,
            accentColor: DaylightColors.primary,
            badgeBg: DaylightColors.primarySoft,
            badgeBorder: DaylightColors.primaryBorder,
            values: stats.rxHistory,
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _SpeedTile(
            label: 'UPLOAD',
            speedText: stats.txSpeedFormatted,
            sessionText: stats.txTotalFormatted,
            icon: Icons.arrow_upward_rounded,
            accentColor: DaylightColors.success,
            badgeBg: DaylightColors.successSoft,
            badgeBorder: DaylightColors.successBorder,
            values: stats.txHistory,
          ),
        ),
      ],
    );
  }
}

class _SpeedTile extends StatelessWidget {
  final String label;
  final String speedText;
  final String sessionText;
  final IconData icon;
  final Color accentColor;
  final Color badgeBg;
  final Color badgeBorder;
  final List<double> values;

  const _SpeedTile({
    required this.label,
    required this.speedText,
    required this.sessionText,
    required this.icon,
    required this.accentColor,
    required this.badgeBg,
    required this.badgeBorder,
    required this.values,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(10, 10, 10, 8),
      decoration: BoxDecoration(
        color: DaylightColors.bgCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: DaylightColors.border),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                width: 28,
                height: 28,
                decoration: BoxDecoration(
                  color: badgeBg,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: badgeBorder),
                ),
                child: Icon(icon, size: 15, color: accentColor),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      label,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 8.5,
                        fontWeight: FontWeight.w700,
                        fontFamily: 'monospace',
                        letterSpacing: 0.4,
                        color: DaylightColors.textMuted,
                      ),
                    ),
                    Text(
                      speedText,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                        fontFamily: 'monospace',
                        color: DaylightColors.textPrimary,
                      ),
                    ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  const Text(
                    'SESSION',
                    style: TextStyle(
                      fontSize: 7.5,
                      fontWeight: FontWeight.w700,
                      fontFamily: 'monospace',
                      color: DaylightColors.textSubtle,
                    ),
                  ),
                  Text(
                    sessionText,
                    style: const TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w700,
                      fontFamily: 'monospace',
                      color: DaylightColors.textSecondary,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 8),
          SizedBox(
            height: 24,
            width: double.infinity,
            child: CustomPaint(
              painter: _SparklinePainter(
                values: values,
                lineColor: accentColor,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SparklinePainter extends CustomPainter {
  final List<double> values;
  final Color lineColor;

  _SparklinePainter({required this.values, required this.lineColor});

  @override
  void paint(Canvas canvas, Size size) {
    if (values.length < 2) return;
    final maxVal = math.max(values.reduce(math.max), 1024.0);
    final stepX = size.width / (values.length - 1);

    final linePath = Path();
    final fillPath = Path();

    for (int i = 0; i < values.length; i++) {
      final x = i * stepX;
      final norm = (values[i] / maxVal).clamp(0.0, 1.0);
      final y = size.height - 2.0 - norm * (size.height - 5.0);
      if (i == 0) {
        linePath.moveTo(x, y);
        fillPath.moveTo(x, size.height);
        fillPath.lineTo(x, y);
      } else {
        linePath.lineTo(x, y);
        fillPath.lineTo(x, y);
      }
    }
    fillPath.lineTo(size.width, size.height);
    fillPath.close();

    final fillPaint = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [
          lineColor.withOpacity(0.22),
          lineColor.withOpacity(0.01),
        ],
      ).createShader(Offset.zero & size);
    canvas.drawPath(fillPath, fillPaint);

    canvas.drawPath(
      linePath,
      Paint()
        ..color = lineColor
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.8
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round,
    );
  }

  @override
  bool shouldRepaint(covariant _SparklinePainter old) => old.values != values;
}
