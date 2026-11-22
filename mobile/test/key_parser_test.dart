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

    test('parses bare UUID ss:// key with query params (OpenKeys.net format)', () async {
      const uri =
          'ss://4dc0eec9-f0e1-4755-be7e-7ba628522d1b@91.99.145.207:443?encryption=none&path=%2F&security=none&type=ws#Germany%20710%20/%20OpenKeys.net';

      final profile = await VpnKeyParser.parse(uri);
      expect(profile.sourceType, 'ss');
      expect(profile.server, '91.99.145.207');
      expect(profile.serverPort, 443);
      expect(profile.password, '4dc0eec9-f0e1-4755-be7e-7ba628522d1b');
      expect(profile.method, 'none');
      expect(profile.name, 'Germany 710 / OpenKeys.net');

      final ssConfig = profile.toShadowsocksConfig(udpRelay: true);
      expect(ssConfig['server'], '91.99.145.207');
      expect(ssConfig['password'], '4dc0eec9-f0e1-4755-be7e-7ba628522d1b');
      expect(ssConfig['method'], 'none');
      expect(ssConfig.containsKey('uri_params'), isFalse);
    });

    test('parses plaintext SS2022, SIP002 plugin, vless://, trojan://, and vmess://', () async {
      final ss2022 = await VpnKeyParser.parse(
        'ss://2022-blake3-aes-128-gcm:srvKey:usrKey@198.51.100.5:8443?plugin=v2ray-plugin%3Bmode%3Dwebsocket#SS2022',
      );
      expect(ss2022.method, '2022-blake3-aes-128-gcm');
      expect(ss2022.password, 'srvKey:usrKey');
      final ssCfg = ss2022.toShadowsocksConfig();
      expect(ssCfg['plugin'], 'v2ray-plugin');
      expect(ssCfg['plugin_opts'], 'mode=websocket');

      final vless = await VpnKeyParser.parse(
        'vless://4dc0eec9-f0e1-4755-be7e-7ba628522d1b@91.99.145.207:443?encryption=none&security=tls&type=ws#VLESS-DE',
      );
      expect(vless.sourceType, 'vless');
      expect(vless.server, '91.99.145.207');
      expect(vless.method, 'none');
      expect(vless.name, 'VLESS-DE');

      final trojan = await VpnKeyParser.parse(
        'trojan://secretPass@203.0.113.10:443?security=tls&sni=example.com#Trojan-JP',
      );
      expect(trojan.sourceType, 'trojan');
      expect(trojan.password, 'secretPass');
      expect(trojan.name, 'Trojan-JP');

      final vmessB64 = base64Encode(utf8.encode(
        '{"v":"2","ps":"VMess-SG","add":"198.51.100.8","port":"443","id":"11111111-2222-3333-4444-555555555555","scy":"auto"}',
      ));
      final vmess = await VpnKeyParser.parse('vmess://$vmessB64');
      expect(vmess.sourceType, 'vmess');
      expect(vmess.server, '198.51.100.8');
      expect(vmess.name, 'VMess-SG');
    });
  });
}
