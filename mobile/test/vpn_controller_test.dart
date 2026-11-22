import 'package:auralink_vpn/models/free_key_region.dart';
import 'package:auralink_vpn/models/vpn_models.dart';
import 'package:auralink_vpn/services/free_keys_service.dart';
import 'package:auralink_vpn/services/storage_service.dart';
import 'package:auralink_vpn/services/vpn_controller.dart';
import 'package:auralink_vpn/services/vpn_platform_channel.dart';
import 'package:flutter_test/flutter_test.dart';

class _MemoryStorage extends StorageService {
  List<VpnProfile> _profiles = [];
  VpnSettings _settings = const VpnSettings(demoMode: true, verifyTunnel: false);

  @override
  Future<List<VpnProfile>> loadProfiles() async => _profiles;

  @override
  Future<void> saveProfiles(List<VpnProfile> profiles) async => _profiles = profiles;

  @override
  Future<VpnSettings> loadSettings() async => _settings;

  @override
  Future<void> saveSettings(VpnSettings settings) async => _settings = settings;
}

class _StubPlatform extends VpnPlatformChannel {
  @override
  Future<bool> hasNativeEngine() async => false;

  @override
  Future<Map<String, dynamic>> getStatus() async => const {};
}

class _StubFreeKeysService extends FreeKeysService {
  final List<FreeRegionKey> sampleKeys = const [
    FreeRegionKey(
      id: 'jp1',
      region: 'Japan',
      countryCode: 'JP',
      flag: '🇯🇵',
      city: 'Tokyo',
      label: 'Tokyo Free #1',
      rawKey: 'ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpwYXNzQDEuMi4zLjQ6NDQz#TokyoFree1',
      sourceType: 'ss',
      server: '1.2.3.4',
      serverPort: 443,
      method: 'chacha20-ietf-poly1305',
      password: 'pass',
    ),
  ];

  @override
  Future<List<FreeRegionKey>> loadCached() async => const [];

  @override
  Future<List<FreeRegionKey>> fetchPublishedFreeKeys(
    String backendBaseUrl, {
    dynamic client,
  }) async =>
      sampleKeys;
}

void main() {
  test('VpnController connects, cancels mid-connect, and connects to Free Region Cards', () async {
    final ctrl = VpnController(
      storage: _MemoryStorage(),
      platform: _StubPlatform(),
      freeKeysService: _StubFreeKeysService(),
    );
    await ctrl.initialize();

    // Verify Free Region Keys synced from Admin Backend
    await ctrl.fetchFreeRegionKeys();
    expect(ctrl.freeRegionKeys.length, 1);
    expect(ctrl.freeRegionKeys.first.region, 'Japan');

    // Start connecting, then cancel mid-flight
    final connectFuture = ctrl.connect();
    await Future<void>.delayed(const Duration(milliseconds: 120));
    expect(ctrl.state, VpnConnectionState.connecting);

    await ctrl.cancelConnect();
    final connected = await connectFuture;
    expect(connected, isFalse);
    expect(ctrl.state, VpnConnectionState.disconnected);
    expect(ctrl.lastError, isEmpty);

    // One-tap connect via published Free Region Card
    final ok = await ctrl.connectToFreeRegionKey(ctrl.freeRegionKeys.first);
    expect(ok, isTrue);
    expect(ctrl.state, VpnConnectionState.connected);
    expect(ctrl.activeProfile?.id, 'free-jp1');
    expect(ctrl.ipv6ShieldActive, isTrue);

    await ctrl.disconnect();
    expect(ctrl.state, VpnConnectionState.disconnected);
    expect(ctrl.ipv6ShieldActive, isFalse);
  });
}
