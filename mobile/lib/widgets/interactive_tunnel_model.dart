import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../models/vpn_models.dart';
import '../theme/daylight_theme.dart';

/// Interactive 4-hop mobile VPN packet pipeline widget:
///   [Mobile Apps] ---> [TUN L3] ---> [sslocal] ---> [VPN Node]
/// Matches the desktop `InteractiveTunnelModelWidget` with tappable node inspection,
/// animated packet flow, and stage badges (1/5 -> 5/5 -> LIVE FLOW).
class InteractiveTunnelModel extends StatefulWidget {
  final VpnConnectionState state;
  final ConnectionStage stage;
  final VpnProfile? profile;
  final VpnSettings settings;
  final TrafficStats stats;
  final bool ipv6ShieldActive;
  final String lastError;

  const InteractiveTunnelModel({
    super.key,
    required this.state,
    required this.stage,
    required this.profile,
    required this.settings,
    required this.stats,
    required this.ipv6ShieldActive,
    this.lastError = '',
  });

  @override
  State<InteractiveTunnelModel> createState() => _InteractiveTunnelModelState();
}

class _InteractiveTunnelModelState extends State<InteractiveTunnelModel>
    with SingleTickerProviderStateMixin {
  late final AnimationController _flowCtrl;
  int _selectedIdx = 1; // Default to TUN L3 node

  static const _nodes = [
    ('apps', 'Mobile Apps'),
    ('tun0', 'TUN L3'),
    ('sslocal', 'sslocal'),
    ('server', 'VPN Node'),
  ];

  @override
  void initState() {
    super.initState();
    _flowCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1600),
    )..repeat();
  }

  @override
  void dispose() {
    _flowCtrl.dispose();
    super.dispose();
  }

  String _stageBadgeText() {
    if (widget.state == VpnConnectionState.connected) return 'LIVE FLOW';
    if (widget.state == VpnConnectionState.disconnecting) return 'TEARDOWN...';
    if (widget.state == VpnConnectionState.error) return 'CONNECTION FAILED';
    if (widget.state == VpnConnectionState.connecting) {
      switch (widget.stage) {
        case ConnectionStage.resolving:
          return '1/5: RESOLVING NODE';
        case ConnectionStage.sslocal:
          return '2/5: SOCKS5 CORE';
        case ConnectionStage.tun0:
          return '3/5: TUNNEL ARMED';
        case ConnectionStage.routing:
          return '4/5: ROUTES & DNS';
        case ConnectionStage.verifying:
          return '5/5: VERIFYING NET';
        default:
          return 'HANDSHAKE';
      }
    }
    return 'IDLE • DIRECT ROUTE';
  }

  Color _stageBadgeColor() {
    switch (widget.state) {
      case VpnConnectionState.connected:
        return DaylightColors.success;
      case VpnConnectionState.connecting:
      case VpnConnectionState.disconnecting:
        return DaylightColors.warning;
      case VpnConnectionState.error:
        return DaylightColors.danger;
      case VpnConnectionState.disconnected:
        return DaylightColors.textMuted;
    }
  }

  String _inspectorText() {
    if (widget.state == VpnConnectionState.error) {
      return 'Error • ${widget.lastError.isNotEmpty ? widget.lastError : 'Connection failed'}';
    }
    final isConn = widget.state == VpnConnectionState.connected;
    final isBusy = widget.state == VpnConnectionState.connecting;
    final prof = widget.profile;

    switch (_selectedIdx) {
      case 0:
        if (isConn) {
          return 'Mobile Apps • Full-Tunnel • DNS ${widget.settings.dnsPrimary} • ↓ ${widget.stats.rxSpeedFormatted} ↑ ${widget.stats.txSpeedFormatted}';
        }
        if (isBusy && widget.stage == ConnectionStage.verifying) {
          return 'Mobile Apps • Verifying real internet & DNS reachability...';
        }
        return isBusy
            ? 'Mobile Apps • Redirecting system traffic -> TUN (10.0.0.2/24)'
            : 'Mobile Apps • Direct Mobile Route • Standard Carrier / Wi-Fi DNS';
      case 1:
        if (isConn) {
          final shield = widget.ipv6ShieldActive ? 'IPv6 Shield Active' : 'IPv6 Active';
          return 'TUN L3 • 10.0.0.2/24 • $shield • ${widget.stats.rxTotalFormatted} ↓ / ${widget.stats.txTotalFormatted} ↑';
        }
        return isBusy
            ? 'TUN L3 • Provisioning VpnService interface & IPv6 leak shield...'
            : 'TUN L3 • Interface Standby • IPv6 Guard Ready • 10.0.0.2/24';
      case 2:
        final mode = widget.settings.udpRelay ? 'TCP+UDP' : 'TCP';
        final cipher = prof?.method ?? 'chacha20-ietf-poly1305';
        if (isConn) {
          return 'sslocal • SOCKS5 127.0.0.1:1080 • $mode • $cipher';
        }
        return isBusy
            ? 'sslocal • Starting local SOCKS5 ($mode) core...'
            : 'sslocal • SOCKS5 Core Standby • Configured ($mode)';
      default:
        final name = prof?.name ?? 'No Server';
        final endpoint = prof != null ? '${prof.server}:${prof.serverPort}' : '--';
        final ping = (prof?.lastPingMs != null && prof!.lastPingMs! >= 0)
            ? '${prof.lastPingMs}ms'
            : '--';
        if (isConn) {
          return 'VPN Node • $name ($endpoint) • Ping: $ping • Uptime: ${widget.stats.durationFormatted}';
        }
        if (isBusy && widget.stage == ConnectionStage.verifying) {
          return 'VPN Node • Probing internet & DNS traffic via $name...';
        }
        return isBusy
            ? 'VPN Node • Handshaking with $name ($endpoint)...'
            : 'VPN Node • $name ($endpoint) • Ping: $ping • Standby';
    }
  }

  String _nodeStatus(int idx) {
    if (widget.state == VpnConnectionState.error) return 'error';
    if (widget.state == VpnConnectionState.connected) return 'active';
    if (widget.state == VpnConnectionState.disconnecting) return 'connecting';
    if (widget.state == VpnConnectionState.connecting) {
      switch (widget.stage) {
        case ConnectionStage.resolving:
          return idx == 3 ? 'connecting' : (idx == 0 ? 'standby' : 'inactive');
        case ConnectionStage.sslocal:
          return idx == 3 ? 'active' : (idx == 2 ? 'connecting' : 'inactive');
        case ConnectionStage.tun0:
          return (idx == 2 || idx == 3)
              ? 'active'
              : (idx == 1 ? 'connecting' : 'standby');
        case ConnectionStage.routing:
          return idx == 0 ? 'connecting' : 'active';
        case ConnectionStage.verifying:
          return idx == 3 ? 'connecting' : 'active';
        default:
          return 'connecting';
      }
    }
    return (idx == 0 || idx == 3) ? 'standby' : 'inactive';
  }

  @override
  Widget build(BuildContext context) {
    final isConn = widget.state == VpnConnectionState.connected;
    final isBusy = widget.state == VpnConnectionState.connecting ||
        widget.state == VpnConnectionState.disconnecting;
    final isErr = widget.state == VpnConnectionState.error;

    final pillBg = isConn
        ? DaylightColors.successSoft
        : isBusy
            ? DaylightColors.warningSoft
            : isErr
                ? DaylightColors.dangerSoft
                : DaylightColors.bgMain;
    final pillBorder = isConn
        ? DaylightColors.successBorder
        : isBusy
            ? DaylightColors.warningBorder
            : isErr
                ? DaylightColors.dangerBorder
                : DaylightColors.border;
    final pillFg = isConn
        ? DaylightColors.successDark
        : isBusy
            ? DaylightColors.warningDark
            : isErr
                ? DaylightColors.dangerDark
                : DaylightColors.textSecondary;

    return Container(
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
      decoration: BoxDecoration(
        color: DaylightColors.bgCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: DaylightColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              const Text(
                'INTERACTIVE TUNNEL MODEL',
                style: TextStyle(
                  fontSize: 9.5,
                  fontWeight: FontWeight.w800,
                  fontFamily: 'monospace',
                  letterSpacing: 0.6,
                  color: DaylightColors.textMuted,
                ),
              ),
              const Spacer(),
              Text(
                _stageBadgeText(),
                style: TextStyle(
                  fontSize: 9.5,
                  fontWeight: FontWeight.w800,
                  fontFamily: 'monospace',
                  color: _stageBadgeColor(),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          SizedBox(
            height: 54,
            child: Stack(
              alignment: Alignment.center,
              children: [
                Positioned.fill(
                  child: AnimatedBuilder(
                    animation: _flowCtrl,
                    builder: (_, __) => CustomPaint(
                      painter: _PipelineTrackPainter(
                        state: widget.state,
                        stage: widget.stage,
                        t: _flowCtrl.value,
                      ),
                    ),
                  ),
                ),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: List.generate(_nodes.length, (idx) {
                    final selected = _selectedIdx == idx;
                    final status = _nodeStatus(idx);
                    final stroke = status == 'active'
                        ? (selected
                            ? DaylightColors.success
                            : DaylightColors.successBright)
                        : status == 'connecting'
                            ? DaylightColors.warning
                            : status == 'error'
                                ? DaylightColors.dangerBright
                                : (selected
                                    ? DaylightColors.primary
                                    : DaylightColors.borderLight);
                    final dot = status == 'active'
                        ? DaylightColors.success
                        : status == 'connecting'
                            ? DaylightColors.warning
                            : status == 'error'
                                ? DaylightColors.danger
                                : (selected
                                    ? DaylightColors.primary
                                    : DaylightColors.textMuted);

                    return GestureDetector(
                      onTap: () => setState(() => _selectedIdx = idx),
                      behavior: HitTestBehavior.opaque,
                      child: SizedBox(
                        width: 68,
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            AnimatedContainer(
                              duration: const Duration(milliseconds: 220),
                              width: 28,
                              height: 28,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: Colors.white,
                                border: Border.all(
                                  color: stroke,
                                  width: selected ? 2.2 : 1.5,
                                ),
                                boxShadow: selected
                                    ? [
                                        BoxShadow(
                                          color: stroke.withOpacity(0.24),
                                          blurRadius: 8,
                                          spreadRadius: 2,
                                        ),
                                      ]
                                    : null,
                              ),
                              child: Center(
                                child: Container(
                                  width: 8,
                                  height: 8,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    color: dot,
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(height: 5),
                            Text(
                              _nodes[idx].$2,
                              textAlign: TextAlign.center,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                fontSize: 9.5,
                                fontWeight:
                                    selected ? FontWeight.w800 : FontWeight.w600,
                                color: selected
                                    ? DaylightColors.textPrimary
                                    : DaylightColors.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  }),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: pillBg,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: pillBorder),
            ),
            child: Text(
              _inspectorText(),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w600,
                fontFamily: 'monospace',
                color: pillFg,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PipelineTrackPainter extends CustomPainter {
  final VpnConnectionState state;
  final ConnectionStage stage;
  final double t;

  _PipelineTrackPainter({
    required this.state,
    required this.stage,
    required this.t,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final y = 14.0;
    const leftX = 34.0;
    final rightX = math.max(leftX + 20, size.width - 34.0);
    final span = rightX - leftX;

    final trackColor = state == VpnConnectionState.connected
        ? DaylightColors.successBright
        : (state == VpnConnectionState.connecting ||
                state == VpnConnectionState.disconnecting)
            ? DaylightColors.warningBright
            : state == VpnConnectionState.error
                ? DaylightColors.dangerBorder
                : DaylightColors.borderLight;

    canvas.drawLine(
      Offset(leftX, y),
      Offset(rightX, y),
      Paint()
        ..color = trackColor
        ..strokeWidth = state == VpnConnectionState.connected ? 2.2 : 1.6
        ..strokeCap = StrokeCap.round,
    );

    if (state == VpnConnectionState.connected ||
        state == VpnConnectionState.connecting) {
      final dotCol = state == VpnConnectionState.connected
          ? DaylightColors.success
          : DaylightColors.warning;
      for (final offset in [0.0, 0.33, 0.66]) {
        final pos = (t + offset) % 1.0;
        final x = leftX + span * pos;
        canvas.drawCircle(
          Offset(x, y),
          5.5,
          Paint()..color = dotCol.withOpacity(0.24),
        );
        canvas.drawCircle(
          Offset(x, y),
          2.6,
          Paint()..color = dotCol,
        );
      }
    }
  }

  @override
  bool shouldRepaint(covariant _PipelineTrackPainter old) => true;
}
