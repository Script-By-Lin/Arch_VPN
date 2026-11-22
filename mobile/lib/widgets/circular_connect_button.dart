import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../models/vpn_models.dart';
import '../theme/daylight_theme.dart';

/// Animated Daylight orbital connect/cancel/disconnect button matching `gui/app.py`.
class CircularConnectButton extends StatefulWidget {
  final VpnConnectionState state;
  final VoidCallback onTap;
  final double size;

  const CircularConnectButton({
    super.key,
    required this.state,
    required this.onTap,
    this.size = 188,
  });

  @override
  State<CircularConnectButton> createState() => _CircularConnectButtonState();
}

class _CircularConnectButtonState extends State<CircularConnectButton>
    with TickerProviderStateMixin {
  late final AnimationController _loopCtrl;
  late final AnimationController _shockCtrl;
  bool _pressed = false;
  bool _lastShockIsDisconnect = false;

  @override
  void initState() {
    super.initState();
    _loopCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2200),
    )..repeat();
    _shockCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 520),
    );
  }

  @override
  void dispose() {
    _loopCtrl.dispose();
    _shockCtrl.dispose();
    super.dispose();
  }

  void _handleTap() {
    _lastShockIsDisconnect = widget.state == VpnConnectionState.connected ||
        widget.state == VpnConnectionState.connecting;
    _shockCtrl.forward(from: 0.0);
    widget.onTap();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => setState(() => _pressed = true),
      onTapUp: (_) {
        setState(() => _pressed = false);
        _handleTap();
      },
      onTapCancel: () => setState(() => _pressed = false),
      child: AnimatedScale(
        scale: _pressed ? 0.94 : 1.0,
        duration: const Duration(milliseconds: 110),
        curve: Curves.easeOut,
        child: SizedBox(
          width: widget.size,
          height: widget.size,
          child: AnimatedBuilder(
            animation: Listenable.merge([_loopCtrl, _shockCtrl]),
            builder: (context, _) {
              return CustomPaint(
                painter: _OrbitalButtonPainter(
                  state: widget.state,
                  loopValue: _loopCtrl.value,
                  shockValue: _shockCtrl.isAnimating ? _shockCtrl.value : 0.0,
                  shockActive: _shockCtrl.isAnimating,
                  shockIsDisconnect: _lastShockIsDisconnect,
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}

class _OrbitalButtonPainter extends CustomPainter {
  final VpnConnectionState state;
  final double loopValue;
  final double shockValue;
  final bool shockActive;
  final bool shockIsDisconnect;

  _OrbitalButtonPainter({
    required this.state,
    required this.loopValue,
    required this.shockValue,
    required this.shockActive,
    required this.shockIsDisconnect,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (math.min(size.width, size.height) / 2) - 18.0;

    late Color gradEnd;
    late Color borderColor;
    late Color iconColor;
    late Color textColor;
    late String subText;

    switch (state) {
      case VpnConnectionState.connected:
        gradEnd = DaylightColors.successSoft;
        borderColor = DaylightColors.successBright;
        iconColor = DaylightColors.success;
        textColor = DaylightColors.successDark;
        subText = 'CONNECTED • TAP TO STOP';
      case VpnConnectionState.connecting:
        gradEnd = DaylightColors.warningSoft;
        borderColor = DaylightColors.warningBright;
        iconColor = DaylightColors.warning;
        textColor = DaylightColors.warningDark;
        subText = 'CONNECTING • CANCEL';
      case VpnConnectionState.disconnecting:
        gradEnd = DaylightColors.warningSoft;
        borderColor = DaylightColors.warningBright;
        iconColor = DaylightColors.warning;
        textColor = DaylightColors.warningDark;
        subText = 'DISCONNECTING...';
      case VpnConnectionState.error:
        gradEnd = DaylightColors.dangerSoft;
        borderColor = DaylightColors.dangerBright;
        iconColor = DaylightColors.danger;
        textColor = DaylightColors.dangerDark;
        subText = 'RETRY CONNECTION';
      case VpnConnectionState.disconnected:
        gradEnd = const Color(0xFFF0F9FF);
        borderColor = DaylightColors.borderLight;
        iconColor = DaylightColors.primary;
        textColor = DaylightColors.textSecondary;
        subText = 'TAP TO CONNECT';
    }

    // Concentric breathing ripples when connected
    if (state == VpnConnectionState.connected) {
      for (final offset in [0.0, 0.5]) {
        final wave = (loopValue + offset) % 1.0;
        final rippleR = radius + 2.0 + wave * 14.0;
        final alpha = ((1.0 - wave) * 0.42).clamp(0.0, 1.0);
        final paint = Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2.0
          ..color = DaylightColors.successBright.withOpacity(alpha);
        canvas.drawCircle(center, rippleR, paint);
      }
    }

    // Expanding tactile click shockwave
    if (shockActive) {
      final swR = radius + 2.0 + shockValue * 22.0;
      final alpha = ((1.0 - shockValue) * 0.65).clamp(0.0, 1.0);
      final swCol =
          shockIsDisconnect ? DaylightColors.warningBright : DaylightColors.successBright;
      final paint = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = math.max(1.0, 2.8 * (1.0 - shockValue * 0.5))
        ..color = swCol.withOpacity(alpha);
      canvas.drawCircle(center, swR, paint);
    }

    // Soft drop halo
    canvas.drawCircle(
      center.translate(0, 4),
      radius + 5.0,
      Paint()..color = borderColor.withOpacity(0.14),
    );

    // Main frosted ceramic disc
    final discPaint = Paint()
      ..shader = RadialGradient(
        center: const Alignment(-0.2, -0.35),
        radius: 1.15,
        colors: [Colors.white, gradEnd],
      ).createShader(Rect.fromCircle(center: center, radius: radius));
    canvas.drawCircle(center, radius, discPaint);

    // Disc border
    canvas.drawCircle(
      center,
      radius,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.5
        ..color = borderColor,
    );

    // Rotating orbital arcs while connecting or disconnecting
    if (state == VpnConnectionState.connecting ||
        state == VpnConnectionState.disconnecting) {
      final arcR = radius + 6.5;
      final arcRect = Rect.fromCircle(center: center, radius: arcR);
      final angle = loopValue * math.pi * 2.0;
      canvas.drawArc(
        arcRect,
        angle,
        math.pi * 0.52,
        false,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 3.0
          ..strokeCap = StrokeCap.round
          ..color = DaylightColors.warningBright,
      );
      canvas.drawArc(
        arcRect,
        angle + math.pi,
        math.pi * 0.34,
        false,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2.0
          ..strokeCap = StrokeCap.round
          ..color = DaylightColors.warningBright.withOpacity(0.35),
      );
    }

    // Power icon backing disc
    final iconCenter = center.translate(0, -12);
    canvas.drawCircle(
      iconCenter,
      26.0,
      Paint()..color = iconColor.withOpacity(0.11),
    );

    // Power icon arc + stem
    const iconR = 14.5;
    final iconPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.0
      ..strokeCap = StrokeCap.round
      ..color = iconColor;
    canvas.drawArc(
      Rect.fromCircle(center: iconCenter, radius: iconR),
      -math.pi / 2 + 0.55,
      math.pi * 2 - 1.1,
      false,
      iconPaint,
    );
    canvas.drawLine(
      iconCenter.translate(0, -17.5),
      iconCenter.translate(0, -3.5),
      iconPaint,
    );

    // Status caption
    final textPainter = TextPainter(
      text: TextSpan(
        text: subText,
        style: TextStyle(
          fontSize: 8.5,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.6,
          color: textColor,
        ),
      ),
      textAlign: TextAlign.center,
      textDirection: TextDirection.ltr,
    )..layout(maxWidth: radius * 1.85);

    textPainter.paint(
      canvas,
      Offset(center.dx - textPainter.width / 2, center.dy + 22),
    );
  }

  @override
  bool shouldRepaint(covariant _OrbitalButtonPainter old) => true;
}
