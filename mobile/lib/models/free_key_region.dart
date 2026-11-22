import 'vpn_models.dart';

/// A free VPN key published by the Admin Backend, displayed as a Region Card in Mobile only.
class FreeRegionKey {
  final String id;
  final String region;
  final String countryCode;
  final String flag;
  final String city;
  final String label;
  final String rawKey;
  final String sourceType;
  final String server;
  final int serverPort;
  final String method;
  final String password;
  final String? prefix;
  final String tier;
  final String updatedAt;
  final int? lastPingMs;

  const FreeRegionKey({
    required this.id,
    required this.region,
    required this.countryCode,
    required this.flag,
    required this.city,
    required this.label,
    required this.rawKey,
    required this.sourceType,
    required this.server,
    required this.serverPort,
    required this.method,
    required this.password,
    this.prefix,
    this.tier = 'FREE',
    this.updatedAt = '',
    this.lastPingMs,
  });

  String get profileId => 'free-$id';

  FreeRegionKey copyWith({int? lastPingMs}) {
    return FreeRegionKey(
      id: id,
      region: region,
      countryCode: countryCode,
      flag: flag,
      city: city,
      label: label,
      rawKey: rawKey,
      sourceType: sourceType,
      server: server,
      serverPort: serverPort,
      method: method,
      password: password,
      prefix: prefix,
      tier: tier,
      updatedAt: updatedAt,
      lastPingMs: lastPingMs ?? this.lastPingMs,
    );
  }

  /// Converts this published free region key into a runnable `VpnProfile`.
  VpnProfile toVpnProfile() {
    return VpnProfile(
      id: profileId,
      name: '$flag $label',
      rawKey: rawKey,
      sourceType: sourceType,
      server: server,
      serverPort: serverPort,
      method: method,
      password: password,
      prefix: prefix,
      lastPingMs: lastPingMs,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'region': region,
        'country_code': countryCode,
        'flag': flag,
        'city': city,
        'label': label,
        'raw_key': rawKey,
        'source_type': sourceType,
        'server': server,
        'server_port': serverPort,
        'method': method,
        'password': password,
        'prefix': prefix,
        'tier': tier,
        'updated_at': updatedAt,
      };

  factory FreeRegionKey.fromJson(Map<String, dynamic> json) {
    return FreeRegionKey(
      id: json['id']?.toString() ?? '',
      region: json['region']?.toString() ?? 'Global',
      countryCode: json['country_code']?.toString() ?? 'XX',
      flag: json['flag']?.toString() ?? '🌐',
      city: json['city']?.toString() ?? '',
      label: json['label']?.toString() ?? 'Free VPN Node',
      rawKey: json['raw_key']?.toString() ?? '',
      sourceType: json['source_type']?.toString() ?? 'ss',
      server: json['server']?.toString() ?? '',
      serverPort: (json['server_port'] is int)
          ? json['server_port'] as int
          : int.tryParse(json['server_port']?.toString() ?? '443') ?? 443,
      method: json['method']?.toString() ?? 'chacha20-ietf-poly1305',
      password: json['password']?.toString() ?? '',
      prefix: json['prefix']?.toString(),
      tier: json['tier']?.toString() ?? 'FREE',
      updatedAt: json['updated_at']?.toString() ?? '',
    );
  }
}
