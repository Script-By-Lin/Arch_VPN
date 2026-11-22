import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../models/vpn_models.dart';

class StorageService {
  static const String _profilesKey = 'auralink_profiles_v1';
  static const String _settingsKey = 'auralink_settings_v1';

  Future<List<VpnProfile>> loadProfiles() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_profilesKey);
    if (raw == null || raw.isEmpty) return [];
    try {
      final list = jsonDecode(raw) as List<dynamic>;
      return list
          .whereType<Map>()
          .map((e) => VpnProfile.fromJson(Map<String, dynamic>.from(e)))
          .toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> saveProfiles(List<VpnProfile> profiles) async {
    final prefs = await SharedPreferences.getInstance();
    final encoded = jsonEncode(profiles.map((p) => p.toJson()).toList());
    await prefs.setString(_profilesKey, encoded);
  }

  Future<VpnSettings> loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_settingsKey);
    if (raw == null || raw.isEmpty) return const VpnSettings();
    try {
      final map = jsonDecode(raw) as Map<String, dynamic>;
      return VpnSettings.fromJson(map);
    } catch (_) {
      return const VpnSettings();
    }
  }

  Future<void> saveSettings(VpnSettings settings) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_settingsKey, jsonEncode(settings.toJson()));
  }
}
