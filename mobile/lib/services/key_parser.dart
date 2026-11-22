import 'dart:convert';
import 'dart:math';

import 'package:http/http.dart' as http;

import '../models/vpn_models.dart';

class KeyParseException implements Exception {
  final String message;
  const KeyParseException(this.message);

  @override
  String toString() => message;
}

/// Parses Shadowsocks `ss://` (SIP002 & legacy base64), `ssconf://`, `http(s)://`,
/// and raw JSON configurations — matching `core/config_manager.py`.
class VpnKeyParser {
  static final Random _rng = Random();

  static String _generateId() {
    const chars = 'abcdef0123456789';
    return List.generate(8, (_) => chars[_rng.nextInt(chars.length)]).join();
  }

  static String _decodeBase64Flexible(String input) {
    var normalized = input.trim().replaceAll('-', '+').replaceAll('_', '/');
    final rem = normalized.length % 4;
    if (rem != 0) {
      normalized += '=' * (4 - rem);
    }
    return utf8.decode(base64.decode(normalized));
  }

  static Future<VpnProfile> parse(
    String rawInput, {
    http.Client? httpClient,
  }) async {
    final trimmed = rawInput.trim();
    if (trimmed.isEmpty) {
      throw const KeyParseException('Key / URL cannot be empty.');
    }

    if (trimmed.startsWith('ssconf://')) {
      return _parseRemoteSubscription(trimmed, isSsconf: true, client: httpClient);
    }
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
      return _parseRemoteSubscription(trimmed, isSsconf: false, client: httpClient);
    }
    if (trimmed.startsWith('ss://')) {
      return parseSsUri(trimmed);
    }
    if (trimmed.startsWith('{')) {
      return parseJsonString(trimmed);
    }

    throw const KeyParseException(
      'Unrecognized format. Expected ssconf://..., ss://..., https://..., or JSON.',
    );
  }

  static Future<VpnProfile> _parseRemoteSubscription(
    String rawInput, {
    required bool isSsconf,
    http.Client? client,
  }) async {
    var urlPart = isSsconf ? rawInput.substring('ssconf://'.length) : rawInput;
    String profileName = isSsconf ? 'AuraLink Server' : 'Subscription Server';

    if (urlPart.contains('#')) {
      final idx = urlPart.indexOf('#');
      final tag = urlPart.substring(idx + 1);
      urlPart = urlPart.substring(0, idx);
      if (tag.isNotEmpty) {
        profileName = Uri.decodeComponent(tag);
      }
    }

    if (!urlPart.startsWith('http://') && !urlPart.startsWith('https://')) {
      urlPart = 'https://$urlPart';
    }

    final uri = Uri.tryParse(urlPart);
    if (uri == null || !uri.hasAuthority) {
      throw KeyParseException('Invalid subscription URL: $urlPart');
    }
    if (!isSsconf && profileName == 'Subscription Server') {
      profileName = uri.host;
    }

    final httpClient = client ?? http.Client();
    try {
      final resp = await httpClient.get(
        uri,
        headers: const {'User-Agent': 'AuraLink-Mobile/1.0'},
      ).timeout(const Duration(seconds: 12));

      if (resp.statusCode < 200 || resp.statusCode >= 300) {
        throw KeyParseException('Subscription HTTP ${resp.statusCode} from ${uri.host}');
      }

      final body = resp.body.trim();
      if (body.startsWith('ss://')) {
        final parsed = parseSsUri(body);
        return parsed.copyWith(name: profileName);
      }

      final decoded = jsonDecode(body);
      if (decoded is! Map<String, dynamic>) {
        throw const KeyParseException('Subscription response is not a valid JSON object.');
      }
      if (decoded.containsKey('error')) {
        final err = decoded['error'];
        if (err is Map && err['message'] != null) {
          throw KeyParseException('Subscription Error: ${err['message']}');
        }
        throw KeyParseException('Subscription Error: $err');
      }

      return _buildFromConfigMap(
        decoded,
        rawKey: rawInput,
        sourceType: isSsconf ? 'ssconf' : 'url',
        fallbackName: profileName,
      );
    } on KeyParseException {
      rethrow;
    } catch (e) {
      throw KeyParseException('Failed to fetch config from $urlPart: $e');
    } finally {
      if (client == null) {
        httpClient.close();
      }
    }
  }

  static VpnProfile parseSsUri(String rawInput) {
    var body = rawInput.substring('ss://'.length).trim();
    String profileName = 'Shadowsocks Server';

    if (body.contains('#')) {
      final idx = body.indexOf('#');
      final tag = body.substring(idx + 1);
      body = body.substring(0, idx);
      if (tag.isNotEmpty) {
        profileName = Uri.decodeComponent(tag);
      }
    }

    String? prefix;
    if (body.contains('?')) {
      final qIdx = body.indexOf('?');
      final queryStr = body.substring(qIdx + 1);
      body = body.substring(0, qIdx);
      final params = Uri.splitQueryString(queryStr);
      if (params['prefix'] != null && params['prefix']!.isNotEmpty) {
        prefix = params['prefix'];
      }
    }

    String method;
    String password;
    String server;
    int serverPort;

    if (body.contains('@')) {
      // SIP002: base64(method:password)@host:port
      final atIdx = body.lastIndexOf('@');
      final userInfo = body.substring(0, atIdx);
      var hostPort = body.substring(atIdx + 1);
      if (hostPort.endsWith('/')) {
        hostPort = hostPort.substring(0, hostPort.length - 1);
      }

      String decodedUser;
      try {
        decodedUser = _decodeBase64Flexible(userInfo);
      } catch (_) {
        decodedUser = Uri.decodeComponent(userInfo);
      }

      final colonIdx = decodedUser.indexOf(':');
      if (colonIdx <= 0) {
        throw const KeyParseException('Invalid Shadowsocks credentials in ss:// URI.');
      }
      method = decodedUser.substring(0, colonIdx);
      password = decodedUser.substring(colonIdx + 1);

      final parsedHostPort = _splitHostPort(hostPort);
      server = parsedHostPort.$1;
      serverPort = parsedHostPort.$2;
    } else {
      // Legacy format: base64(method:password@host:port)
      final decoded = _decodeBase64Flexible(body);
      final atIdx = decoded.lastIndexOf('@');
      if (atIdx <= 0) {
        throw const KeyParseException('Invalid legacy ss:// base64 payload.');
      }
      final userInfo = decoded.substring(0, atIdx);
      final hostPort = decoded.substring(atIdx + 1);
      final colonIdx = userInfo.indexOf(':');
      if (colonIdx <= 0) {
        throw const KeyParseException('Invalid method:password in legacy ss:// URI.');
      }
      method = userInfo.substring(0, colonIdx);
      password = userInfo.substring(colonIdx + 1);

      final parsedHostPort = _splitHostPort(hostPort);
      server = parsedHostPort.$1;
      serverPort = parsedHostPort.$2;
    }

    if (profileName == 'Shadowsocks Server' && server.isNotEmpty) {
      profileName = server;
    }

    return VpnProfile(
      id: _generateId(),
      name: profileName,
      rawKey: rawInput,
      sourceType: 'ss',
      server: server,
      serverPort: serverPort,
      method: method,
      password: password,
      prefix: prefix,
    );
  }

  static VpnProfile parseJsonString(String rawJson) {
    try {
      final decoded = jsonDecode(rawJson);
      if (decoded is! Map<String, dynamic>) {
        throw const KeyParseException('JSON config must be an object.');
      }
      return _buildFromConfigMap(
        decoded,
        rawKey: rawJson,
        sourceType: 'json',
        fallbackName: decoded['remarks']?.toString() ??
            decoded['server']?.toString() ??
            'Custom JSON Server',
      );
    } on KeyParseException {
      rethrow;
    } catch (e) {
      throw KeyParseException('Invalid JSON configuration: $e');
    }
  }

  static (String, int) _splitHostPort(String hostPort) {
    // Handle IPv6 bracketed [::1]:8388 or host:port
    if (hostPort.startsWith('[')) {
      final closeIdx = hostPort.indexOf(']');
      if (closeIdx == -1) {
        throw KeyParseException('Malformed IPv6 host in $hostPort');
      }
      final host = hostPort.substring(1, closeIdx);
      final rest = hostPort.substring(closeIdx + 1);
      final port = rest.startsWith(':') ? int.tryParse(rest.substring(1)) ?? 8388 : 8388;
      return (host, port);
    }
    final colonIdx = hostPort.lastIndexOf(':');
    if (colonIdx == -1) {
      return (hostPort, 8388);
    }
    final host = hostPort.substring(0, colonIdx);
    final portStr = hostPort.substring(colonIdx + 1).split('/').first;
    final port = int.tryParse(portStr);
    if (port == null || port <= 0 || port > 65535) {
      throw KeyParseException('Invalid server port: $portStr');
    }
    return (host, port);
  }

  static VpnProfile _buildFromConfigMap(
    Map<String, dynamic> map, {
    required String rawKey,
    required String sourceType,
    required String fallbackName,
  }) {
    final server = map['server']?.toString().trim() ?? '';
    final password = map['password']?.toString() ?? '';
    if (server.isEmpty || password.isEmpty) {
      throw const KeyParseException(
        'Shadowsocks configuration missing required fields (server, password).',
      );
    }

    final portRaw = map['server_port'];
    final serverPort = (portRaw is int)
        ? portRaw
        : int.tryParse(portRaw?.toString() ?? '443') ?? 443;
    final method = map['method']?.toString().trim().isNotEmpty == true
        ? map['method'].toString().trim()
        : 'chacha20-ietf-poly1305';
    final prefix = map['prefix']?.toString();
    final name = map['remarks']?.toString().trim().isNotEmpty == true
        ? map['remarks'].toString().trim()
        : fallbackName;

    return VpnProfile(
      id: _generateId(),
      name: name,
      rawKey: rawKey,
      sourceType: sourceType,
      server: server,
      serverPort: serverPort,
      method: method,
      password: password,
      prefix: prefix,
      extraConfig: Map<String, dynamic>.from(map),
    );
  }
}
