import 'dart:convert';

import 'package:auralink_vpn/services/key_parser.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('VpnKeyParser', () {
    test('parses SIP002 ss:// URI with tag and Outline prefix', () {
      final userInfo = base64Url.encode(utf8.encode('chacha20-ietf-poly1305:mySecretPass'));
      final uri = 'ss://$userInfo@77.83.241.82:80/?prefix=%16%03%01#Tokyo%20Fast%2001';

      final profile = VpnKeyParser.parseSsUri(uri);
      expect(profile.server, '77.83.241.82');
      expect(profile.serverPort, 80);
      expect(profile.method, 'chacha20-ietf-poly1305');
      expect(profile.password, 'mySecretPass');
      expect(profile.name, 'Tokyo Fast 01');
      expect(profile.prefix, isNotNull);

      final ssConfig = profile.toShadowsocksConfig(udpRelay: true);
      expect(ssConfig['mode'], 'tcp_and_udp');
      expect(ssConfig['no_delay'], isTrue);
      expect(ssConfig['local_port'], 1080);
    });

    test('parses legacy full-base64 ss:// URI', () {
      final raw = base64Url.encode(utf8.encode('aes-256-gcm:pass123@1.2.3.4:8388'));
      final profile = VpnKeyParser.parseSsUri('ss://$raw#LegacyNode');
      expect(profile.server, '1.2.3.4');
      expect(profile.serverPort, 8388);
      expect(profile.method, 'aes-256-gcm');
      expect(profile.password, 'pass123');
      expect(profile.name, 'LegacyNode');
    });

    test('parses raw Shadowsocks JSON config', () {
      const jsonStr = '''
      {
        "server": "198.51.100.10",
        "server_port": 443,
        "password": "pw",
        "method": "chacha20-ietf-poly1305",
        "remarks": "Singapore-01"
      }
      ''';
      final profile = VpnKeyParser.parseJsonString(jsonStr);
      expect(profile.name, 'Singapore-01');
      expect(profile.server, '198.51.100.10');
      expect(profile.serverPort, 443);
    });
  });
}
