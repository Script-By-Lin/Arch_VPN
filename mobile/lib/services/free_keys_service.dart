import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../models/free_key_region.dart';

/// Fetches published FREE region keys from the AuraLink Mobile Admin Backend
/// (`GET /api/mobile/free-keys`) and caches them locally for instant launch.
class FreeKeysService {
  static const String _cacheKey = 'auralink_mobile_free_keys_cache_v1';

  Future<List<FreeRegionKey>> loadCached() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_cacheKey);
      if (raw == null || raw.isEmpty) return [];
      final decoded = jsonDecode(raw) as List<dynamic>;
      return decoded
          .whereType<Map>()
          .map((e) => FreeRegionKey.fromJson(Map<String, dynamic>.from(e)))
          .toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> saveCache(List<FreeRegionKey> keys) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(
        _cacheKey,
        jsonEncode(keys.map((k) => k.toJson()).toList()),
      );
    } catch (_) {}
  }

  Future<List<FreeRegionKey>> fetchPublishedFreeKeys(
    String backendBaseUrl, {
    http.Client? client,
  }) async {
    final cleaned = backendBaseUrl.trim().replaceAll(RegExp(r'/+$'), '');
    if (cleaned.isEmpty) {
      throw Exception('Backend URL is not configured.');
    }

    final uri = Uri.parse('$cleaned/api/mobile/free-keys');
    final httpClient = client ?? http.Client();
    try {
      final resp = await httpClient.get(
        uri,
        headers: const {
          'Accept': 'application/json',
          'X-AuraLink-Client': 'mobile',
        },
      ).timeout(const Duration(seconds: 8));

      if (resp.statusCode != 200) {
        throw Exception('Backend returned HTTP ${resp.statusCode}');
      }

      final payload = jsonDecode(resp.body);
      if (payload is! Map<String, dynamic>) {
        throw Exception('Invalid response from free-keys backend.');
      }

      final rawList = (payload['keys'] as List<dynamic>?) ?? const [];
      final parsed = rawList
          .whereType<Map>()
          .map((e) => FreeRegionKey.fromJson(Map<String, dynamic>.from(e)))
          .toList();

      await saveCache(parsed);
      return parsed;
    } finally {
      if (client == null) {
        httpClient.close();
      }
    }
  }
}
