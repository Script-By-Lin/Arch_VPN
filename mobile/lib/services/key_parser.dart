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

/// Parses variable VPN key formats:
/// - `ss://` (SIP002 base64, legacy full-base64, plaintext `method:pass`, SS2022,
///   and OpenKeys.net bare UUID/password + query params such as `encryption=none&type=ws`)
/// - `vless://`, `trojan://`, `vmess://`, `ssr://`
/// - `ssconf://`, `http(s)://`, and raw JSON configurations — matching `core/config_manager.py`.
class VpnKeyParser {
  static final Random _rng = Random();
  static final RegExp _methodTokenRegex = RegExp(r'^[A-Za-z0-9._-]+$');

  static String _generateId() {
    const chars = 'abcdef0123456789';
    return List.generate(8, (_) => chars[_rng.nextInt(chars.length)]).join();
  }

  static String _safeDecodeComponent(String input) {
    try {
      return Uri.decodeComponent(input);
    } catch (_) {
      return input;
    }
  }

  static Map<String, String> _parseQueryParams(String queryStr) {
    final params = <String, String>{};
    if (queryStr.isEmpty) return params;
    for (final part in queryStr.split('&')) {
      if (part.isEmpty) continue;
      final eqIdx = part.indexOf('=');
      if (eqIdx == -1) {
        final k = _safeDecodeComponent(part);
        if (k.isNotEmpty) params[k] = '';
      } else {
        final k = _safeDecodeComponent(part.substring(0, eqIdx));
        final v = _safeDecodeComponent(part.substring(eqIdx + 1));
        if (k.isNotEmpty) params[k] = v;
      }
    }
    return params;
  }

  static String _decodeBase64Flexible(String input) {
    var normalized = input.trim().replaceAll('-', '+').replaceAll('_', '/');
    final rem = normalized.length % 4;
    if (rem != 0) {
      normalized += '=' * (4 - rem);
    }
    return utf8.decode(base64.decode(normalized));
  }

  static bool _isPrintableText(String text) {
    if (text.isEmpty) return false;
    for (final unit in text.runes) {
      if (unit < 32 || (unit > 126 && unit < 160)) {
        return false;
      }
    }
    return true;
  }

  static (String, String) _extractSsCredentials(
    String userInfo,
    Map<String, String> params,
  ) {
    final raw = userInfo.trim();
    if (raw.contains(':')) {
      final idx = raw.indexOf(':');
      return (
        _safeDecodeComponent(raw.substring(0, idx)).trim(),
        _safeDecodeComponent(raw.substring(idx + 1)),
      );
    }

    final unquoted = _safeDecodeComponent(raw);
    if (unquoted.contains(':')) {
      final idx = unquoted.indexOf(':');
      return (
        unquoted.substring(0, idx).trim(),
        unquoted.substring(idx + 1),
      );
    }

    // Attempt base64 decode only when it cleanly decodes to `valid_method:nonempty_password`
    try {
      final decoded = _decodeBase64Flexible(raw);
      final colonIdx = decoded.indexOf(':');
      if (colonIdx > 0 && _isPrintableText(decoded)) {
        final candMethod = decoded.substring(0, colonIdx);
        final candPass = decoded.substring(colonIdx + 1);
        if (candPass.isNotEmpty && _methodTokenRegex.hasMatch(candMethod)) {
          return (candMethod, candPass);
        }
      }
    } catch (_) {}

    // Bare UUID / token / password without method prefix (e.g. OpenKeys.net keys)
    final method = (params['method']?.trim().isNotEmpty == true
            ? params['method']!
            : params['cipher']?.trim().isNotEmpty == true
                ? params['cipher']!
                : params['encryption']?.trim().isNotEmpty == true
                    ? params['encryption']!
                    : 'chacha20-ietf-poly1305')
        .trim();
    return (method, unquoted);
  }

  static Future<VpnProfile> parse(
    String rawInput, {
    http.Client? httpClient,
  }) async {
    var trimmed = rawInput.trim();
    if (trimmed.isEmpty) {
      throw const KeyParseException('Key / URL cannot be empty.');
    }

    if (!trimmed.startsWith('{')) {
      trimmed = trimmed.replaceAll(RegExp(r'[\r\n]+'), '').trim();
    }
    final lower = trimmed.toLowerCase();

    if (lower.startsWith('ssconf://')) {
      return _parseRemoteSubscription(trimmed, isSsconf: true, client: httpClient);
    }
    if (lower.startsWith('http://') || lower.startsWith('https://')) {
      return _parseRemoteSubscription(trimmed, isSsconf: false, client: httpClient);
    }
    if (lower.startsWith('ss://')) {
      return parseSsUri(trimmed);
    }
    if (lower.startsWith('vless://') || lower.startsWith('trojan://')) {
      return parseVlessOrTrojanUri(trimmed);
    }
    if (lower.startsWith('vmess://')) {
      return parseVmessUri(trimmed);
    }
    if (lower.startsWith('ssr://')) {
      return parseSsrUri(trimmed);
    }
    if (trimmed.startsWith('{')) {
      return parseJsonString(trimmed);
    }

    throw const KeyParseException(
      'Unrecognized format. Expected ss://, vless://, trojan://, vmess://, ssr://, ssconf://, https://, or JSON.',
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
        profileName = _safeDecodeComponent(tag).trim();
      }
    }

    if (!urlPart.toLowerCase().startsWith('http://') &&
        !urlPart.toLowerCase().startsWith('https://')) {
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
      final bodyLower = body.toLowerCase();
      if (bodyLower.startsWith('ss://')) {
        return parseSsUri(body).copyWith(name: profileName);
      }
      if (bodyLower.startsWith('vless://') || bodyLower.startsWith('trojan://')) {
        return parseVlessOrTrojanUri(body).copyWith(name: profileName);
      }
      if (bodyLower.startsWith('vmess://')) {
        return parseVmessUri(body).copyWith(name: profileName);
      }
      if (bodyLower.startsWith('ssr://')) {
        return parseSsrUri(body).copyWith(name: profileName);
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
    final cleaned = rawInput.replaceAll(RegExp(r'[\r\n]+'), '').trim();
    var body = cleaned.substring('ss://'.length).trim();
    String profileName = 'Shadowsocks Server';

    if (body.contains('#')) {
      final idx = body.indexOf('#');
      final tag = body.substring(idx + 1);
      body = body.substring(0, idx);
      if (tag.isNotEmpty) {
        profileName = _safeDecodeComponent(tag).trim();
      }
    }

    var params = <String, String>{};
    if (body.contains('?')) {
      final qIdx = body.indexOf('?');
      final queryStr = body.substring(qIdx + 1);
      body = body.substring(0, qIdx);
      params = _parseQueryParams(queryStr);
    }

    String method;
    String password;
    String server;
    int serverPort;

    if (body.contains('@')) {
      // SIP002, plaintext method:pass, SS2022, or bare UUID/password@host:port
      final atIdx = body.lastIndexOf('@');
      final userInfo = body.substring(0, atIdx);
      var hostPort = body.substring(atIdx + 1);
      if (hostPort.endsWith('/')) {
        hostPort = hostPort.substring(0, hostPort.length - 1);
      }

      final creds = _extractSsCredentials(userInfo, params);
      method = creds.$1;
      password = creds.$2;

      final parsedHostPort = _splitHostPort(hostPort, defaultPort: 8388);
      server = parsedHostPort.$1;
      serverPort = parsedHostPort.$2;
    } else {
      // Legacy format: base64(method:password@host:port[?query][#tag])
      String decoded;
      try {
        decoded = _decodeBase64Flexible(body);
      } catch (_) {
        throw const KeyParseException('Invalid legacy ss:// base64 payload.');
      }
      if (decoded.contains('#') && profileName == 'Shadowsocks Server') {
        final idx = decoded.indexOf('#');
        final tag = decoded.substring(idx + 1);
        decoded = decoded.substring(0, idx);
        if (tag.isNotEmpty) {
          profileName = _safeDecodeComponent(tag).trim();
        }
      }
      if (decoded.contains('?')) {
        final qIdx = decoded.indexOf('?');
        final q2 = decoded.substring(qIdx + 1);
        decoded = decoded.substring(0, qIdx);
        params = {..._parseQueryParams(q2), ...params};
      }
      final atIdx = decoded.lastIndexOf('@');
      if (atIdx <= 0) {
        throw const KeyParseException('Invalid legacy ss:// base64 payload.');
      }
      final userInfo = decoded.substring(0, atIdx);
      final hostPort = decoded.substring(atIdx + 1);
      final creds = _extractSsCredentials(userInfo, params);
      method = creds.$1;
      password = creds.$2;

      final parsedHostPort = _splitHostPort(hostPort, defaultPort: 8388);
      server = parsedHostPort.$1;
      serverPort = parsedHostPort.$2;
    }

    if (server.isEmpty || password.isEmpty) {
      throw const KeyParseException('ss:// key missing server or password.');
    }

    if (profileName == 'Shadowsocks Server' && server.isNotEmpty) {
      profileName = server;
    }

    final extraConfig = <String, dynamic>{};
    if (params.isNotEmpty) {
      extraConfig['uri_params'] = params;
    }
    final rawPlugin = params['plugin']?.trim() ?? '';
    if (rawPlugin.isNotEmpty) {
      final semiIdx = rawPlugin.indexOf(';');
      if (semiIdx > 0) {
        extraConfig['plugin'] = rawPlugin.substring(0, semiIdx).trim();
        extraConfig['plugin_opts'] = rawPlugin.substring(semiIdx + 1).trim();
      } else {
        extraConfig['plugin'] = rawPlugin;
      }
    }

    final prefix = (params['prefix'] != null && params['prefix']!.isNotEmpty)
        ? params['prefix']
        : null;

    return VpnProfile(
      id: _generateId(),
      name: profileName,
      rawKey: cleaned,
      sourceType: 'ss',
      server: server,
      serverPort: serverPort,
      method: method.isNotEmpty ? method : 'chacha20-ietf-poly1305',
      password: password,
      prefix: prefix,
      extraConfig: extraConfig,
    );
  }

  static VpnProfile parseVlessOrTrojanUri(String rawInput) {
    final cleaned = rawInput.replaceAll(RegExp(r'[\r\n]+'), '').trim();
    final isVless = cleaned.toLowerCase().startsWith('vless://');
    final scheme = isVless ? 'vless' : 'trojan';
    var body = cleaned.substring(scheme.length + 3).trim();
    String profileName = isVless ? 'VLESS Server' : 'Trojan Server';

    if (body.contains('#')) {
      final idx = body.indexOf('#');
      final tag = body.substring(idx + 1);
      body = body.substring(0, idx);
      if (tag.isNotEmpty) {
        profileName = _safeDecodeComponent(tag).trim();
      }
    }

    var params = <String, String>{};
    if (body.contains('?')) {
      final qIdx = body.indexOf('?');
      final queryStr = body.substring(qIdx + 1);
      body = body.substring(0, qIdx);
      params = _parseQueryParams(queryStr);
    }

    final atIdx = body.lastIndexOf('@');
    if (atIdx <= 0) {
      throw KeyParseException('Invalid $scheme:// URI: missing credentials.');
    }
    final password = _safeDecodeComponent(body.substring(0, atIdx)).trim();
    final hostPort = body.substring(atIdx + 1);
    final parsedHostPort = _splitHostPort(hostPort, defaultPort: 443);
    final server = parsedHostPort.$1;
    final serverPort = parsedHostPort.$2;

    if (server.isEmpty || password.isEmpty) {
      throw KeyParseException('$scheme:// key missing server or credential.');
    }

    if ((profileName == 'VLESS Server' || profileName == 'Trojan Server') &&
        server.isNotEmpty) {
      profileName = server;
    }

    final method = (params['encryption']?.trim().isNotEmpty == true
            ? params['encryption']!
            : params['method']?.trim().isNotEmpty == true
                ? params['method']!
                : params['security']?.trim().isNotEmpty == true
                    ? params['security']!
                    : scheme)
        .trim();

    return VpnProfile(
      id: _generateId(),
      name: profileName,
      rawKey: cleaned,
      sourceType: scheme,
      server: server,
      serverPort: serverPort,
      method: method,
      password: password,
      prefix: params['prefix']?.isNotEmpty == true ? params['prefix'] : null,
      extraConfig: params.isNotEmpty ? {'uri_params': params} : const {},
    );
  }

  static VpnProfile parseVmessUri(String rawInput) {
    final cleaned = rawInput.replaceAll(RegExp(r'[\r\n]+'), '').trim();
    var body = cleaned.substring('vmess://'.length).trim();
    String profileName = 'VMess Server';

    if (body.contains('#')) {
      final idx = body.indexOf('#');
      final tag = body.substring(idx + 1);
      body = body.substring(0, idx);
      if (tag.isNotEmpty) {
        profileName = _safeDecodeComponent(tag).trim();
      }
    }

    if (!body.contains('@')) {
      try {
        final decoded = jsonDecode(_decodeBase64Flexible(body));
        if (decoded is! Map<String, dynamic>) {
          throw const KeyParseException('vmess:// payload must decode to a JSON object.');
        }
        final server = (decoded['add'] ?? decoded['server'] ?? '').toString().trim();
        final password = (decoded['id'] ?? decoded['password'] ?? '').toString().trim();
        if (server.isEmpty || password.isEmpty) {
          throw const KeyParseException('vmess:// key missing required server or id.');
        }
        final port = int.tryParse((decoded['port'] ?? 443).toString()) ?? 443;
        final method = (decoded['scy'] ?? decoded['cipher'] ?? 'auto').toString().trim();
        final remarks = (decoded['ps'] ?? '').toString().trim();
        return VpnProfile(
          id: _generateId(),
          name: remarks.isNotEmpty ? remarks : (profileName != 'VMess Server' ? profileName : server),
          rawKey: cleaned,
          sourceType: 'vmess',
          server: server,
          serverPort: port,
          method: method.isNotEmpty ? method : 'auto',
          password: password,
          extraConfig: {'vmess': decoded},
        );
      } on KeyParseException {
        rethrow;
      } catch (e) {
        throw KeyParseException('Invalid vmess:// payload: $e');
      }
    }

    var params = <String, String>{};
    if (body.contains('?')) {
      final qIdx = body.indexOf('?');
      params = _parseQueryParams(body.substring(qIdx + 1));
      body = body.substring(0, qIdx);
    }
    final atIdx = body.lastIndexOf('@');
    final password = _safeDecodeComponent(body.substring(0, atIdx)).trim();
    final parsedHostPort = _splitHostPort(body.substring(atIdx + 1), defaultPort: 443);
    final server = parsedHostPort.$1;
    final serverPort = parsedHostPort.$2;
    if (server.isEmpty || password.isEmpty) {
      throw const KeyParseException('vmess:// key missing server or id.');
    }
    final method = params['encryption'] ?? params['cipher'] ?? 'auto';
    return VpnProfile(
      id: _generateId(),
      name: profileName == 'VMess Server' ? server : profileName,
      rawKey: cleaned,
      sourceType: 'vmess',
      server: server,
      serverPort: serverPort,
      method: method.isNotEmpty ? method : 'auto',
      password: password,
      extraConfig: params.isNotEmpty ? {'uri_params': params} : const {},
    );
  }

  static VpnProfile parseSsrUri(String rawInput) {
    final cleaned = rawInput.replaceAll(RegExp(r'[\r\n]+'), '').trim();
    final body = cleaned.substring('ssr://'.length).trim();
    String decoded;
    try {
      decoded = _decodeBase64Flexible(body);
    } catch (e) {
      throw KeyParseException('Invalid ssr:// base64 payload: $e');
    }

    var mainPart = decoded;
    var params = <String, String>{};
    if (decoded.contains('/?')) {
      final idx = decoded.indexOf('/?');
      mainPart = decoded.substring(0, idx);
      params = _parseQueryParams(decoded.substring(idx + 2));
    } else if (decoded.contains('?')) {
      final idx = decoded.indexOf('?');
      mainPart = decoded.substring(0, idx);
      params = _parseQueryParams(decoded.substring(idx + 1));
    }

    final parts = mainPart.split(':');
    if (parts.length < 6) {
      throw const KeyParseException('Invalid ssr:// payload structure.');
    }
    final server = parts[0].trim();
    final port = int.tryParse(parts[1].trim());
    if (port == null || port <= 0 || port > 65535) {
      throw KeyParseException('Invalid server port in ssr:// URI: ${parts[1]}');
    }
    final method = parts[3].trim().isNotEmpty ? parts[3].trim() : 'chacha20-ietf-poly1305';
    String password;
    try {
      password = _decodeBase64Flexible(parts[5]);
    } catch (_) {
      password = parts[5];
    }
    var name = server;
    if (params['remarks'] != null && params['remarks']!.isNotEmpty) {
      try {
        final r = _decodeBase64Flexible(params['remarks']!).trim();
        if (r.isNotEmpty) name = r;
      } catch (_) {
        name = params['remarks']!.trim();
      }
    }
    if (server.isEmpty || password.isEmpty) {
      throw const KeyParseException('ssr:// key missing server or password.');
    }
    return VpnProfile(
      id: _generateId(),
      name: name,
      rawKey: cleaned,
      sourceType: 'ssr',
      server: server,
      serverPort: port,
      method: method,
      password: password,
      extraConfig: params.isNotEmpty ? {'uri_params': params} : const {},
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
            decoded['ps']?.toString() ??
            decoded['server']?.toString() ??
            decoded['add']?.toString() ??
            'Custom JSON Server',
      );
    } on KeyParseException {
      rethrow;
    } catch (e) {
      throw KeyParseException('Invalid JSON configuration: $e');
    }
  }

  static (String, int) _splitHostPort(String hostPort, {int defaultPort = 8388}) {
    final cleaned = hostPort.trim().split('?').first.trim().replaceAll(RegExp(r'/+$'), '');
    // Handle IPv6 bracketed [::1]:8388 or host:port
    if (cleaned.startsWith('[')) {
      final closeIdx = cleaned.indexOf(']');
      if (closeIdx == -1) {
        throw KeyParseException('Malformed IPv6 host in $cleaned');
      }
      final host = cleaned.substring(1, closeIdx);
      final rest = cleaned.substring(closeIdx + 1);
      final port = rest.startsWith(':')
          ? int.tryParse(rest.substring(1).split('/').first)
          : defaultPort;
      if (port == null || port <= 0 || port > 65535) {
        throw KeyParseException('Invalid server port in $cleaned');
      }
      return (host, port);
    }
    final colonIdx = cleaned.lastIndexOf(':');
    if (colonIdx == -1) {
      return (cleaned.split('/').first.trim(), defaultPort);
    }
    final host = cleaned.substring(0, colonIdx).trim();
    final portStr = cleaned.substring(colonIdx + 1).split('/').first.trim();
    final port = portStr.isEmpty ? defaultPort : int.tryParse(portStr);
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
    final server = (map['server'] ?? map['add'])?.toString().trim() ?? '';
    final password = (map['password'] ?? map['id'])?.toString() ?? '';
    if (server.isEmpty || password.isEmpty) {
      throw const KeyParseException(
        'VPN configuration missing required fields (server, password).',
      );
    }

    final portRaw = map['server_port'] ?? map['port'];
    final serverPort = (portRaw is int)
        ? portRaw
        : int.tryParse(portRaw?.toString() ?? '443') ?? 443;
    final rawMethod = (map['method'] ?? map['encryption'] ?? map['scy'])?.toString().trim() ?? '';
    final method = rawMethod.isNotEmpty ? rawMethod : 'chacha20-ietf-poly1305';
    final prefix = map['prefix']?.toString();
    final rawRemarks = (map['remarks'] ?? map['ps'])?.toString().trim() ?? '';
    final name = rawRemarks.isNotEmpty ? rawRemarks : fallbackName;

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
