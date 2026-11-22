import 'dart:convert';

enum VpnConnectionState {
  disconnected,
  connecting,
  connected,
  disconnecting,
  error,
}

enum ConnectionStage {
  idle,
  resolving,
  sslocal,
  tun0,
  routing,
  verifying,
  connected,
  teardown,
  error,
}

class DnsPreset {
  final String name;
  final String primary;
  final String secondary;

  const DnsPreset({
    required this.name,
    required this.primary,
    required this.secondary,
  });

  static const List<DnsPreset> presets = [
    DnsPreset(
      name: 'Cloudflare (1.1.1.1 / 1.0.0.1)',
      primary: '1.1.1.1',
      secondary: '1.0.0.1',
    ),
    DnsPreset(
      name: 'Google (8.8.8.8 / 8.8.4.4)',
      primary: '8.8.8.8',
      secondary: '8.8.4.4',
    ),
    DnsPreset(
      name: 'Quad9 (9.9.9.9 / 149.112.112.112)',
      primary: '9.9.9.9',
      secondary: '149.112.112.112',
    ),
    DnsPreset(
      name: 'AdGuard (94.140.14.14 / 94.140.15.15)',
      primary: '94.140.14.14',
      secondary: '94.140.15.15',
    ),
  ];

  static DnsPreset byName(String name) {
    return presets.firstWhere(
      (p) => p.name == name,
      orElse: () => presets.first,
    );
  }
}

class VpnProfile {
  final String id;
  final String name;
  final String rawKey;
  final String sourceType; // ss | ssconf | url | json
  final String server;
  final int serverPort;
  final String method;
  final String password;
  final String? prefix;
  final Map<String, dynamic> extraConfig;
  final int? lastPingMs;

  const VpnProfile({
    required this.id,
    required this.name,
    required this.rawKey,
    required this.sourceType,
    required this.server,
    required this.serverPort,
    required this.method,
    required this.password,
    this.prefix,
    this.extraConfig = const {},
    this.lastPingMs,
  });

  VpnProfile copyWith({
    String? name,
    int? lastPingMs,
    bool clearPing = false,
  }) {
    return VpnProfile(
      id: id,
      name: name ?? this.name,
      rawKey: rawKey,
      sourceType: sourceType,
      server: server,
      serverPort: serverPort,
      method: method,
      password: password,
      prefix: prefix,
      extraConfig: extraConfig,
      lastPingMs: clearPing ? null : (lastPingMs ?? this.lastPingMs),
    );
  }

  /// Generates the Shadowsocks JSON config payload passed to native sslocal / engine.
  Map<String, dynamic> toShadowsocksConfig({
    String localAddress = '127.0.0.1',
    int localPort = 1080,
    bool udpRelay = true,
  }) {
    final map = <String, dynamic>{
      ...extraConfig,
      'server': server,
      'server_port': serverPort,
      'password': password,
      'method': method,
      'local_address': localAddress,
      'local_port': localPort,
      'no_delay': extraConfig['no_delay'] ?? true,
    };
    if (prefix != null && prefix!.isNotEmpty) {
      map['prefix'] = prefix;
    }
    if (udpRelay && !map.containsKey('mode')) {
      map['mode'] = 'tcp_and_udp';
    }
    return map;
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'raw_key': rawKey,
        'source_type': sourceType,
        'server': server,
        'server_port': serverPort,
        'method': method,
        'password': password,
        'prefix': prefix,
        'extra_config': extraConfig,
        'last_ping_ms': lastPingMs,
      };

  factory VpnProfile.fromJson(Map<String, dynamic> json) {
    return VpnProfile(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? 'AuraLink Node',
      rawKey: json['raw_key']?.toString() ?? '',
      sourceType: json['source_type']?.toString() ?? 'ss',
      server: json['server']?.toString() ?? '',
      serverPort: (json['server_port'] is int)
          ? json['server_port'] as int
          : int.tryParse(json['server_port']?.toString() ?? '443') ?? 443,
      method: json['method']?.toString() ?? 'chacha20-ietf-poly1305',
      password: json['password']?.toString() ?? '',
      prefix: json['prefix']?.toString(),
      extraConfig: json['extra_config'] is Map
          ? Map<String, dynamic>.from(json['extra_config'] as Map)
          : const {},
      lastPingMs: json['last_ping_ms'] is int ? json['last_ping_ms'] as int : null,
    );
  }

  String toJsonString() => jsonEncode(toJson());
}

class VpnSettings {
  final String dnsPresetName;
  final String dnsPrimary;
  final String dnsBackup;
  final bool disableIpv6;
  final bool udpRelay;
  final bool verifyTunnel;
  final bool demoMode;
  final String freeKeysBackendUrl;
  final String? activeProfileId;

  const VpnSettings({
    this.dnsPresetName = 'Cloudflare (1.1.1.1 / 1.0.0.1)',
    this.dnsPrimary = '1.1.1.1',
    this.dnsBackup = '1.0.0.1',
    this.disableIpv6 = true,
    this.udpRelay = true,
    this.verifyTunnel = true,
    this.demoMode = false,
    this.freeKeysBackendUrl = 'http://10.0.2.2:8088',
    this.activeProfileId,
  });

  VpnSettings copyWith({
    String? dnsPresetName,
    String? dnsPrimary,
    String? dnsBackup,
    bool? disableIpv6,
    bool? udpRelay,
    bool? verifyTunnel,
    bool? demoMode,
    String? freeKeysBackendUrl,
    String? activeProfileId,
    bool clearActiveProfile = false,
  }) {
    return VpnSettings(
      dnsPresetName: dnsPresetName ?? this.dnsPresetName,
      dnsPrimary: dnsPrimary ?? this.dnsPrimary,
      dnsBackup: dnsBackup ?? this.dnsBackup,
      disableIpv6: disableIpv6 ?? this.disableIpv6,
      udpRelay: udpRelay ?? this.udpRelay,
      verifyTunnel: verifyTunnel ?? this.verifyTunnel,
      demoMode: demoMode ?? this.demoMode,
      freeKeysBackendUrl: freeKeysBackendUrl ?? this.freeKeysBackendUrl,
      activeProfileId:
          clearActiveProfile ? null : (activeProfileId ?? this.activeProfileId),
    );
  }

  Map<String, dynamic> toJson() => {
        'dns_preset': dnsPresetName,
        'dns_primary': dnsPrimary,
        'dns_backup': dnsBackup,
        'disable_ipv6': disableIpv6,
        'udp_relay': udpRelay,
        'verify_tunnel': verifyTunnel,
        'demo_mode': demoMode,
        'free_keys_backend_url': freeKeysBackendUrl,
        'active_profile_id': activeProfileId,
      };

  factory VpnSettings.fromJson(Map<String, dynamic> json) {
    return VpnSettings(
      dnsPresetName:
          json['dns_preset']?.toString() ?? 'Cloudflare (1.1.1.1 / 1.0.0.1)',
      dnsPrimary: json['dns_primary']?.toString() ?? '1.1.1.1',
      dnsBackup: json['dns_backup']?.toString() ?? '1.0.0.1',
      disableIpv6: json['disable_ipv6'] is bool ? json['disable_ipv6'] as bool : true,
      udpRelay: json['udp_relay'] is bool ? json['udp_relay'] as bool : true,
      verifyTunnel:
          json['verify_tunnel'] is bool ? json['verify_tunnel'] as bool : true,
      demoMode: json['demo_mode'] is bool ? json['demo_mode'] as bool : false,
      freeKeysBackendUrl:
          json['free_keys_backend_url']?.toString() ?? 'http://10.0.2.2:8088',
      activeProfileId: json['active_profile_id']?.toString(),
    );
  }
}

class TrafficStats {
  final double rxSpeedBps;
  final double txSpeedBps;
  final int rxTotalBytes;
  final int txTotalBytes;
  final Duration uptime;
  final List<double> rxHistory;
  final List<double> txHistory;

  const TrafficStats({
    this.rxSpeedBps = 0,
    this.txSpeedBps = 0,
    this.rxTotalBytes = 0,
    this.txTotalBytes = 0,
    this.uptime = Duration.zero,
    this.rxHistory = const [],
    this.txHistory = const [],
  });

  static TrafficStats empty() => TrafficStats(
        rxHistory: List<double>.filled(18, 0.0),
        txHistory: List<double>.filled(18, 0.0),
      );

  String get rxSpeedFormatted => formatSpeed(rxSpeedBps);
  String get txSpeedFormatted => formatSpeed(txSpeedBps);
  String get rxTotalFormatted => formatBytes(rxTotalBytes);
  String get txTotalFormatted => formatBytes(txTotalBytes);

  String get durationFormatted {
    final hours = uptime.inHours;
    final mins = uptime.inMinutes.remainder(60).toString().padLeft(2, '0');
    final secs = uptime.inSeconds.remainder(60).toString().padLeft(2, '0');
    return hours > 0 ? '${hours.toString().padLeft(2, '0')}:$mins:$secs' : '$mins:$secs';
  }

  static String formatBytes(num bytes) {
    if (bytes <= 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    double val = bytes.toDouble();
    int idx = 0;
    while (val >= 1024 && idx < units.length - 1) {
      val /= 1024;
      idx++;
    }
    if (idx == 0) return '${val.toInt()} B';
    return '${val.toStringAsFixed(val >= 100 ? 1 : 2)} ${units[idx]}';
  }

  static String formatSpeed(double bps) {
    if (bps <= 0) return '0 B/s';
    return '${formatBytes(bps)}/s';
  }
}

enum LogLevel { info, ok, warn, error, debug }

class LogEntry {
  final DateTime timestamp;
  final String source;
  final LogLevel level;
  final String message;

  const LogEntry({
    required this.timestamp,
    required this.source,
    required this.level,
    required this.message,
  });

  String get timeFormatted {
    final h = timestamp.hour.toString().padLeft(2, '0');
    final m = timestamp.minute.toString().padLeft(2, '0');
    final s = timestamp.second.toString().padLeft(2, '0');
    return '$h:$m:$s';
  }

  String get levelTag {
    switch (level) {
      case LogLevel.ok:
        return 'OK';
      case LogLevel.warn:
        return 'WARN';
      case LogLevel.error:
        return 'ERR';
      case LogLevel.debug:
        return 'DBG';
      case LogLevel.info:
        return 'INFO';
    }
  }

  String toPlainLine() => '[$timeFormatted] [$source] $levelTag $message';
}
