import 'dart:async';

import 'package:flutter/services.dart';

import '../models/vpn_models.dart';

/// PlatformChannel bridge to Android (`AuraLinkVpnService.kt`) and iOS (`AppDelegate.swift`).
class VpnPlatformChannel {
  static const MethodChannel _control = MethodChannel('com.auralink.vpn/control');
  static const EventChannel _events = EventChannel('com.auralink.vpn/events');
  static const EventChannel _stats = EventChannel('com.auralink.vpn/stats');
  static const EventChannel _logs = EventChannel('com.auralink.vpn/logs');

  Stream<Map<String, dynamic>> get eventStream => _events
      .receiveBroadcastStream()
      .where((e) => e is Map)
      .map((e) => Map<String, dynamic>.from(e as Map));

  Stream<Map<String, dynamic>> get statsStream => _stats
      .receiveBroadcastStream()
      .where((e) => e is Map)
      .map((e) => Map<String, dynamic>.from(e as Map));

  Stream<String> get logStream =>
      _logs.receiveBroadcastStream().map((e) => e.toString());

  /// Checks if the native platform has embedded Shadowsocks + tun2socks binaries
  /// or iOS NetworkExtension configured.
  Future<bool> hasNativeEngine() async {
    try {
      final res = await _control.invokeMethod<bool>('hasNativeEngine');
      return res ?? false;
    } on MissingPluginException {
      return false;
    } catch (_) {
      return false;
    }
  }

  /// Requests OS VPN permission (Android `VpnService.prepare()` or iOS NEVPNManager).
  Future<bool> prepareVpn() async {
    try {
      final granted = await _control.invokeMethod<bool>('prepareVpn');
      return granted ?? false;
    } on MissingPluginException {
      return false;
    }
  }

  /// Starts native full-tunnel VPN with Shadowsocks config, DNS, and IPv6 shield.
  Future<bool> startVpn({
    required VpnProfile profile,
    required VpnSettings settings,
  }) async {
    final payload = <String, dynamic>{
      'profile_name': profile.name,
      'server': profile.server,
      'server_port': profile.serverPort,
      'method': profile.method,
      'password': profile.password,
      'prefix': profile.prefix ?? '',
      'ss_config': profile.toShadowsocksConfig(udpRelay: settings.udpRelay),
      'dns_primary': settings.dnsPrimary,
      'dns_backup': settings.dnsBackup,
      'disable_ipv6': settings.disableIpv6,
      'udp_relay': settings.udpRelay,
      'verify_tunnel': settings.verifyTunnel,
    };
    final ok = await _control.invokeMethod<bool>('connect', payload);
    return ok ?? false;
  }

  /// Cancels an in-flight connection immediately without waiting on handshake timeouts.
  Future<bool> cancelConnect() async {
    try {
      final ok = await _control.invokeMethod<bool>('cancelConnect');
      return ok ?? true;
    } on MissingPluginException {
      return true;
    }
  }

  /// Stops active VPN tunnel and restores system routes, DNS, and IPv6.
  Future<bool> stopVpn() async {
    try {
      final ok = await _control.invokeMethod<bool>('disconnect');
      return ok ?? true;
    } on MissingPluginException {
      return true;
    }
  }

  /// Queries current native tunnel state (useful after app relaunch).
  Future<Map<String, dynamic>> getStatus() async {
    try {
      final raw = await _control.invokeMethod<Map<dynamic, dynamic>>('getStatus');
      return raw != null ? Map<String, dynamic>.from(raw) : const {};
    } on MissingPluginException {
      return const {};
    } catch (_) {
      return const {};
    }
  }
}
