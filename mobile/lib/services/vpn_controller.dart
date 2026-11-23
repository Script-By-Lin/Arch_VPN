import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import '../models/free_key_region.dart';
import '../models/vpn_models.dart';
import 'free_keys_service.dart';
import 'key_parser.dart';
import 'storage_service.dart';
import 'vpn_platform_channel.dart';

/// Central state & VPN lifecycle controller with:
/// - 5-stage connection pipeline (Resolving -> SOCKS5 Core -> TUN & IPv6 Shield -> Routes & DNS -> Verifying Net)
/// - Lock-free instant Cancel-While-Connecting
/// - Native Android/iOS MethodChannel bridge + Demo Mode fallback
/// - Mobile-only Free Region Keys feed synced from the Admin Backend
/// - Real-time traffic sparklines and clean line-by-line log stream
class VpnController extends ChangeNotifier {
  final StorageService _storage;
  final VpnPlatformChannel _platform;
  final FreeKeysService _freeKeysService;

  VpnController({
    StorageService? storage,
    VpnPlatformChannel? platform,
    FreeKeysService? freeKeysService,
  })  : _storage = storage ?? StorageService(),
        _platform = platform ?? VpnPlatformChannel(),
        _freeKeysService = freeKeysService ?? FreeKeysService();

  List<VpnProfile> _profiles = [];
  List<FreeRegionKey> _freeRegionKeys = [];
  final Set<String> _pingingFreeKeyIds = {};
  final Set<String> _pingingProfileIds = {};
  bool _loadingFreeKeys = false;
  String? _freeKeysError;
  VpnSettings _settings = const VpnSettings();
  VpnConnectionState _state = VpnConnectionState.disconnected;
  ConnectionStage _stage = ConnectionStage.idle;
  String _stageLabel = 'Direct Physical Route';
  String _statusMessage = 'System using standard mobile route';
  String _lastError = '';
  bool _nativeEngineAvailable = false;
  bool _ipv6ShieldActive = false;
  bool _tunnelVerified = false;
  int? _verifyLatencyMs;
  bool _cancelRequested = false;

  TrafficStats _stats = TrafficStats.empty();
  final List<LogEntry> _logs = [];
  bool _logWrap = false;

  DateTime? _connectedAt;
  Timer? _demoStatsTimer;
  StreamSubscription<Map<String, dynamic>>? _eventSub;
  StreamSubscription<Map<String, dynamic>>? _statsSub;
  StreamSubscription<String>? _logSub;
  final Random _rng = Random();

  // Getters
  List<VpnProfile> get profiles => List.unmodifiable(_profiles);
  List<FreeRegionKey> get freeRegionKeys => List.unmodifiable(_freeRegionKeys);
  bool isFreeKeyPinging(String keyId) => _pingingFreeKeyIds.contains(keyId);
  bool isProfilePinging(String profileId) => _pingingProfileIds.contains(profileId);
  bool get loadingFreeKeys => _loadingFreeKeys;
  String? get freeKeysError => _freeKeysError;
  VpnSettings get settings => _settings;
  VpnConnectionState get state => _state;
  ConnectionStage get stage => _stage;
  String get stageLabel => _stageLabel;
  String get statusMessage => _statusMessage;
  String get lastError => _lastError;
  bool get nativeEngineAvailable => _nativeEngineAvailable;
  bool get isUsingDemoEngine => _settings.demoMode || !_nativeEngineAvailable;
  bool get ipv6ShieldActive => _ipv6ShieldActive;
  bool get tunnelVerified => _tunnelVerified;
  int? get verifyLatencyMs => _verifyLatencyMs;
  TrafficStats get stats => _stats;
  List<LogEntry> get logs => List.unmodifiable(_logs);
  bool get logWrap => _logWrap;

  VpnProfile? get activeProfile {
    if (_profiles.isEmpty) return null;
    if (_settings.activeProfileId != null) {
      for (final p in _profiles) {
        if (p.id == _settings.activeProfileId) return p;
      }
    }
    return _profiles.first;
  }

  Future<void> initialize() async {
    _profiles = await _storage.loadProfiles();
    _settings = await _storage.loadSettings();
    _freeRegionKeys = await _freeKeysService.loadCached();
    _nativeEngineAvailable = await _platform.hasNativeEngine();

    if (_profiles.isEmpty) {
      // Seed a clear sample profile so users can test UI immediately or replace with their own key
      _profiles = [
        const VpnProfile(
          id: 'demo-tokyo',
          name: 'Tokyo-Fast-01 (Sample)',
          rawKey: '',
          sourceType: 'ss',
          server: '198.51.100.42',
          serverPort: 8443,
          method: 'chacha20-ietf-poly1305',
          password: 'sample-replace-with-your-key',
        ),
      ];
      _settings = _settings.copyWith(activeProfileId: _profiles.first.id);
    }

    _bindPlatformStreams();

    final nativeStatus = await _platform.getStatus();
    if (nativeStatus['state'] == 'CONNECTED') {
      _state = VpnConnectionState.connected;
      _stage = ConnectionStage.connected;
      _ipv6ShieldActive = _settings.disableIpv6;
      _stageLabel = 'Live Flow Active';
      _statusMessage = 'Virtual TUN active • routed via ${activeProfile?.name ?? 'Node'}';
    }

    addLog(
      'system',
      LogLevel.info,
      _nativeEngineAvailable
          ? 'AuraLink Daylight Mobile ready (Native VPN engine detected).'
          : 'AuraLink Daylight Mobile ready (Demo Mode active — add native libs for live kernel TUN).',
    );
    notifyListeners();
    unawaited(fetchFreeRegionKeys(silent: true));
  }

  /// Fetches published FREE region keys from the Mobile Admin Backend.
  Future<void> fetchFreeRegionKeys({bool silent = false}) async {
    _loadingFreeKeys = true;
    if (!silent) _freeKeysError = null;
    notifyListeners();

    try {
      final prevPings = {
        for (final k in _freeRegionKeys)
          if (k.lastPingMs != null) k.id: k.lastPingMs!,
      };
      final fetched = await _freeKeysService.fetchPublishedFreeKeys(
        _settings.freeKeysBackendUrl,
      );
      _freeRegionKeys = fetched
          .map((k) => prevPings.containsKey(k.id) ? k.copyWith(lastPingMs: prevPings[k.id]) : k)
          .toList();
      _freeKeysError = null;
      addLog(
        'free-keys',
        LogLevel.ok,
        'Synced ${fetched.length} published free region key(s) from admin backend.',
      );
    } catch (e) {
      if (!silent) {
        _freeKeysError = e.toString().replaceFirst('Exception: ', '');
        addLog('free-keys', LogLevel.warn, 'Could not fetch free keys: $_freeKeysError');
      }
    } finally {
      _loadingFreeKeys = false;
      notifyListeners();
    }
  }

  /// Resolves an IPv4 address first (avoiding Android IPv6 blackhole timeouts),
  /// measures pure TCP handshake RTT, retries once on transient radio wake-up drop,
  /// and optionally falls back to local SOCKS5 when VPN is active.
  Future<(int?, String?)> _measureTcpLatency(
    String rawHost,
    int port, {
    Duration timeout = const Duration(seconds: 6),
  }) async {
    var host = rawHost.trim();
    if (host.startsWith('[') && host.endsWith(']')) {
      host = host.substring(1, host.length - 1);
    }
    if (host.isEmpty || port <= 0 || port > 65535) {
      return (null, 'Invalid target $rawHost:$port');
    }

    // 1. Resolve address (prefer IPv4 to prevent IPv6 blackhole timeouts on mobile)
    InternetAddress? targetAddr = InternetAddress.tryParse(host);
    if (targetAddr == null) {
      try {
        final v4 = await InternetAddress.lookup(host, type: InternetAddressType.IPv4)
            .timeout(const Duration(seconds: 4));
        if (v4.isNotEmpty) targetAddr = v4.first;
      } catch (_) {}
      if (targetAddr == null) {
        try {
          final any = await InternetAddress.lookup(host)
              .timeout(const Duration(seconds: 4));
          if (any.isNotEmpty) targetAddr = any.first;
        } catch (e) {
          return (null, 'DNS lookup failed: $e');
        }
      }
    }

    if (targetAddr == null) {
      return (null, 'Unable to resolve $host');
    }

    // 2. Direct TCP handshake with 1 quick retry for mobile radio wake-up
    String? lastErr;
    for (int attempt = 0; attempt < 2; attempt++) {
      final attemptTimeout = attempt == 0 ? timeout : const Duration(seconds: 4);
      final sw = Stopwatch()..start();
      Socket? sock;
      try {
        sock = await Socket.connect(targetAddr, port, timeout: attemptTimeout);
        sw.stop();
        sock.destroy();
        return (sw.elapsedMilliseconds.clamp(1, 99999), null);
      } catch (e) {
        sw.stop();
        try {
          sock?.destroy();
        } catch (_) {}
        lastErr = e.toString();
      }
    }

    // 3. If VPN is already connected via native sslocal, test via local SOCKS5 as fallback
    if (_state == VpnConnectionState.connected && !isUsingDemoEngine) {
      final socksMs = await _measureViaLocalSocks5(host, port);
      if (socksMs != null) {
        return (socksMs, null);
      }
    }

    return (null, lastErr ?? 'Connection timed out');
  }

  Future<int?> _measureViaLocalSocks5(String host, int port) async {
    Socket? sock;
    try {
      sock = await Socket.connect(
        InternetAddress.loopbackIPv4,
        1080,
        timeout: const Duration(seconds: 2),
      );
      final iter = StreamIterator<List<int>>(sock);
      Future<List<int>> readAtLeast(int count, Duration limit) async {
        final buf = <int>[];
        final deadline = DateTime.now().add(limit);
        while (buf.length < count) {
          final rem = deadline.difference(DateTime.now());
          if (rem.isNegative) throw TimeoutException('SOCKS5 read timeout');
          final hasNext = await iter.moveNext().timeout(rem);
          if (!hasNext) throw const SocketException('SOCKS5 closed');
          buf.addAll(iter.current);
        }
        return buf;
      }

      // Greeting: VER=5, NMETHODS=1, NO_AUTH=0
      sock.add(const [0x05, 0x01, 0x00]);
      await sock.flush();
      final greet = await readAtLeast(2, const Duration(seconds: 2));
      if (greet[0] != 0x05 || greet[1] != 0x00) return null;

      // CONNECT request with domain ATYP=0x03
      final hostBytes = utf8.encode(host);
      if (hostBytes.length > 255) return null;
      final req = <int>[
        0x05,
        0x01,
        0x00,
        0x03,
        hostBytes.length,
        ...hostBytes,
        (port >> 8) & 0xFF,
        port & 0xFF,
      ];
      final sw = Stopwatch()..start();
      sock.add(req);
      await sock.flush();
      final rep = await readAtLeast(4, const Duration(seconds: 5));
      sw.stop();
      if (rep[0] == 0x05 && rep[1] == 0x00) {
        return sw.elapsedMilliseconds.clamp(1, 99999);
      }
      return null;
    } catch (_) {
      return null;
    } finally {
      try {
        sock?.destroy();
      } catch (_) {}
    }
  }

  Future<int?> pingFreeRegionKey(String keyId) async {
    final idx = _freeRegionKeys.indexWhere((k) => k.id == keyId);
    if (idx == -1) return null;
    final item = _freeRegionKeys[idx];

    _pingingFreeKeyIds.add(keyId);
    notifyListeners();

    String targetHost = item.server;
    int targetPort = item.serverPort;

    try {
      // Resolve remote ssconf:// or subscription URL to its actual VPN node host:port
      if ((item.sourceType == 'ssconf' || item.sourceType == 'url') &&
          item.rawKey.isNotEmpty) {
        try {
          final resolved = await VpnKeyParser.parse(item.rawKey);
          targetHost = resolved.server;
          targetPort = resolved.serverPort;
        } catch (_) {}
      }

      final (ms, err) = await _measureTcpLatency(targetHost, targetPort);
      final curIdx = _freeRegionKeys.indexWhere((k) => k.id == keyId);
      if (curIdx != -1) {
        _freeRegionKeys[curIdx] = _freeRegionKeys[curIdx].copyWith(
          lastPingMs: ms ?? -1,
        );
      }
      if (ms != null) {
        addLog('ping', LogLevel.info, '${item.flag} ${item.label} responded in ${ms}ms');
      } else {
        addLog(
          'ping',
          LogLevel.warn,
          'Ping timeout for ${item.flag} ${item.label} ($targetHost:$targetPort): $err',
        );
      }
      return ms;
    } finally {
      _pingingFreeKeyIds.remove(keyId);
      notifyListeners();
    }
  }

  Future<void> pingAllFreeRegionKeys() async {
    final keys = List<FreeRegionKey>.from(_freeRegionKeys);
    await Future.wait(keys.map((item) => pingFreeRegionKey(item.id)));
  }

  /// Connects directly to a published FREE region card in one tap.
  Future<bool> connectToFreeRegionKey(FreeRegionKey item) async {
    VpnProfile targetProfile;
    if (item.sourceType == 'ssconf' || item.sourceType == 'url') {
      targetProfile = (await VpnKeyParser.parse(item.rawKey)).copyWith(
        name: '${item.flag} ${item.label}',
      );
    } else {
      targetProfile = item.toVpnProfile();
    }

    final existingIdx = _profiles.indexWhere((p) => p.id == targetProfile.id);
    if (existingIdx >= 0) {
      _profiles[existingIdx] = targetProfile;
    } else {
      if (_profiles.length == 1 && _profiles.first.id == 'demo-tokyo') {
        _profiles.clear();
      }
      _profiles.insert(0, targetProfile);
    }

    final wasConnected = _state == VpnConnectionState.connected;
    _settings = _settings.copyWith(activeProfileId: targetProfile.id);
    await _storage.saveProfiles(_profiles);
    await _storage.saveSettings(_settings);
    notifyListeners();

    if (wasConnected) {
      await disconnect();
    }
    return connect();
  }

  Future<void> updateFreeKeysBackendUrl(String url) async {
    final cleaned = url.trim().replaceAll(RegExp(r'/+$'), '');
    if (cleaned.isEmpty) return;
    _settings = _settings.copyWith(freeKeysBackendUrl: cleaned);
    await _storage.saveSettings(_settings);
    addLog('free-keys', LogLevel.info, 'Free Keys Admin Backend set to $cleaned');
    notifyListeners();
    await fetchFreeRegionKeys();
  }

  void _bindPlatformStreams() {
    try {
      _eventSub = _platform.eventStream.listen((event) {
        final type = event['type']?.toString() ?? '';
        final msg = event['message']?.toString() ?? '';
        if (type == 'stage_changed') {
          _stage = _parseStage(event['stage']?.toString() ?? '');
          _stageLabel = event['stage_label']?.toString() ?? _stageLabel;
          if (msg.isNotEmpty) _statusMessage = msg;
          addLog('tunnel', LogLevel.info, '$_stageLabel — $msg');
        } else if (type == 'connected') {
          _state = VpnConnectionState.connected;
          _stage = ConnectionStage.connected;
          _connectedAt = DateTime.now();
          _ipv6ShieldActive = event['ipv6_disabled'] == true;
          _tunnelVerified = event['verified'] != false;
          _verifyLatencyMs =
              event['verify_latency_ms'] is int ? event['verify_latency_ms'] as int : null;
          final profName = activeProfile?.name ?? 'VPN Node';
          final latPart = _verifyLatencyMs != null ? ' • verified ${_verifyLatencyMs}ms' : '';
          _stageLabel = 'Live Flow Active';
          _statusMessage =
              'TUN active • ${_ipv6ShieldActive ? 'IPv6 disabled' : 'IPv6 active'}$latPart • $profName';
          addLog('connect', LogLevel.ok, msg.isNotEmpty ? msg : 'VPN tunnel established.');
        } else if (type == 'disconnected') {
          _resetToDisconnected(msg.isNotEmpty ? msg : 'VPN Disconnected');
        } else if (type == 'error') {
          _state = VpnConnectionState.error;
          _stage = ConnectionStage.error;
          _lastError = event['error']?.toString() ?? msg;
          _statusMessage = _lastError;
          _ipv6ShieldActive = false;
          addLog('error', LogLevel.error, _lastError);
        }
        notifyListeners();
      }, onError: (_) {});

      _statsSub = _platform.statsStream.listen((payload) {
        if (_state != VpnConnectionState.connected) return;
        final rxSpeed = (payload['rx_speed_bps'] as num?)?.toDouble() ?? 0.0;
        final txSpeed = (payload['tx_speed_bps'] as num?)?.toDouble() ?? 0.0;
        final rxTotal = (payload['rx_bytes'] as num?)?.toInt() ?? 0;
        final txTotal = (payload['tx_bytes'] as num?)?.toInt() ?? 0;
        final uptime = _connectedAt != null
            ? DateTime.now().difference(_connectedAt!)
            : Duration.zero;
        _pushTrafficSample(
          rxSpeed: rxSpeed,
          txSpeed: txSpeed,
          rxTotal: rxTotal,
          txTotal: txTotal,
          uptime: uptime,
        );
      }, onError: (_) {});

      _logSub = _platform.logStream.listen((raw) {
        addLog('daemon', LogLevel.debug, raw);
      }, onError: (_) {});
    } catch (_) {
      // Ignore on environments without platform event channels (e.g., unit tests).
    }
  }

  ConnectionStage _parseStage(String name) {
    switch (name) {
      case 'resolving':
        return ConnectionStage.resolving;
      case 'sslocal':
        return ConnectionStage.sslocal;
      case 'tun0':
        return ConnectionStage.tun0;
      case 'routing':
        return ConnectionStage.routing;
      case 'verifying':
        return ConnectionStage.verifying;
      case 'connected':
        return ConnectionStage.connected;
      case 'teardown':
        return ConnectionStage.teardown;
      case 'error':
        return ConnectionStage.error;
      default:
        return ConnectionStage.idle;
    }
  }

  void addLog(String source, LogLevel level, String message) {
    _logs.add(LogEntry(
      timestamp: DateTime.now(),
      source: source,
      level: level,
      message: message.trim(),
    ));
    if (_logs.length > 500) {
      _logs.removeRange(0, _logs.length - 500);
    }
    notifyListeners();
  }

  void clearLogs() {
    _logs.clear();
    notifyListeners();
  }

  void toggleLogWrap() {
    _logWrap = !_logWrap;
    notifyListeners();
  }

  Future<VpnProfile> importKey(String rawInput) async {
    addLog('import', LogLevel.info, 'Parsing key / subscription...');
    final parsed = await VpnKeyParser.parse(rawInput);

    // Deduplicate by server+port+name
    final existingIdx = _profiles.indexWhere(
      (p) => p.server == parsed.server && p.serverPort == parsed.serverPort && p.name == parsed.name,
    );
    if (existingIdx >= 0) {
      _profiles[existingIdx] = parsed;
    } else {
      // Remove sample placeholder once user imports their first real profile
      if (_profiles.length == 1 && _profiles.first.id == 'demo-tokyo') {
        _profiles.clear();
      }
      _profiles.insert(0, parsed);
    }

    _settings = _settings.copyWith(activeProfileId: parsed.id);
    await _storage.saveProfiles(_profiles);
    await _storage.saveSettings(_settings);
    addLog('import', LogLevel.ok, 'Imported ${parsed.name} (${parsed.server}:${parsed.serverPort})');
    notifyListeners();

    // Measure ping in background
    unawaited(pingProfile(parsed.id));
    return parsed;
  }

  Future<void> selectProfile(String profileId) async {
    final wasConnected = _state == VpnConnectionState.connected;
    _settings = _settings.copyWith(activeProfileId: profileId);
    await _storage.saveSettings(_settings);
    addLog('profile', LogLevel.info, 'Active node switched to ${activeProfile?.name ?? profileId}');
    notifyListeners();

    if (wasConnected) {
      await disconnect();
      await connect();
    }
  }

  Future<void> deleteProfile(String profileId) async {
    final isTargetActive = activeProfile?.id == profileId;
    if (isTargetActive &&
        (_state == VpnConnectionState.connected || _state == VpnConnectionState.connecting)) {
      await disconnect();
    }

    _profiles.removeWhere((p) => p.id == profileId);
    if (_settings.activeProfileId == profileId) {
      _settings = _settings.copyWith(
        activeProfileId: _profiles.isNotEmpty ? _profiles.first.id : null,
        clearActiveProfile: _profiles.isEmpty,
      );
    }
    await _storage.saveProfiles(_profiles);
    await _storage.saveSettings(_settings);
    addLog('profile', LogLevel.warn, 'Deleted profile $profileId');
    notifyListeners();
  }

  Future<void> updateDnsPreset(DnsPreset preset) async {
    _settings = _settings.copyWith(
      dnsPresetName: preset.name,
      dnsPrimary: preset.primary,
      dnsBackup: preset.secondary,
    );
    await _storage.saveSettings(_settings);
    addLog('dns', LogLevel.info, 'Upstream DNS set to ${preset.name}');
    notifyListeners();
  }

  Future<void> updateSettings({
    bool? disableIpv6,
    bool? udpRelay,
    bool? verifyTunnel,
    bool? demoMode,
  }) async {
    _settings = _settings.copyWith(
      disableIpv6: disableIpv6,
      udpRelay: udpRelay,
      verifyTunnel: verifyTunnel,
      demoMode: demoMode,
    );
    await _storage.saveSettings(_settings);
    notifyListeners();
  }

  /// Measures TCP handshake latency to the VPN server.
  Future<int?> pingProfile(String profileId) async {
    final idx = _profiles.indexWhere((p) => p.id == profileId);
    if (idx == -1) return null;
    final prof = _profiles[idx];

    _pingingProfileIds.add(profileId);
    notifyListeners();

    try {
      final (ms, err) = await _measureTcpLatency(prof.server, prof.serverPort);
      final curIdx = _profiles.indexWhere((p) => p.id == profileId);
      if (curIdx != -1) {
        _profiles[curIdx] = _profiles[curIdx].copyWith(lastPingMs: ms ?? -1);
      }
      if (ms != null) {
        addLog('ping', LogLevel.info, '${prof.name} responded in ${ms}ms');
      } else {
        addLog(
          'ping',
          LogLevel.warn,
          'Timeout reaching ${prof.name} (${prof.server}:${prof.serverPort}): $err',
        );
      }
      return ms;
    } finally {
      _pingingProfileIds.remove(profileId);
      notifyListeners();
    }
  }

  Future<void> pingAllProfiles() async {
    final list = List<VpnProfile>.from(_profiles);
    await Future.wait(list.map((p) => pingProfile(p.id)));
  }

  /// Toggles connection state:
  /// - Disconnected / Error -> Connect
  /// - Connecting -> Cancel immediately
  /// - Connected -> Disconnect
  Future<void> toggleConnection() async {
    if (_state == VpnConnectionState.connected) {
      await disconnect();
    } else if (_state == VpnConnectionState.connecting) {
      await cancelConnect();
    } else if (_state == VpnConnectionState.disconnected ||
        _state == VpnConnectionState.error) {
      await connect();
    }
  }

  Future<bool> connect() async {
    if (_state == VpnConnectionState.connecting ||
        _state == VpnConnectionState.connected) {
      return true;
    }
    final profile = activeProfile;
    if (profile == null) {
      _state = VpnConnectionState.error;
      _stage = ConnectionStage.error;
      _lastError = 'No server profile available. Import a key first.';
      _statusMessage = _lastError;
      addLog('error', LogLevel.error, _lastError);
      notifyListeners();
      return false;
    }

    _cancelRequested = false;
    _lastError = '';
    _tunnelVerified = false;
    _verifyLatencyMs = null;
    _state = VpnConnectionState.connecting;
    _stage = ConnectionStage.resolving;
    _stageLabel = '1/5: Resolving Node';
    _statusMessage = 'Preparing tunnel to ${profile.name}...';
    notifyListeners();

    if (!isUsingDemoEngine) {
      return _connectNative(profile);
    }
    return _connectDemoPipeline(profile);
  }

  Future<bool> _connectNative(VpnProfile profile) async {
    try {
      final permitted = await _platform.prepareVpn();
      if (_cancelRequested) {
        _resetToDisconnected('Connection cancelled by user');
        return false;
      }
      if (!permitted) {
        throw Exception('VPN permission was denied by the operating system.');
      }

      addLog(
        'connect',
        LogLevel.info,
        'Handing off ${profile.name} (${_settings.udpRelay ? 'TCP+UDP' : 'TCP'}) to native VpnService...',
      );
      final ok = await _platform.startVpn(profile: profile, settings: _settings);
      if (!ok && !_cancelRequested) {
        throw Exception('Native VPN engine failed to start.');
      }
      return ok;
    } catch (e) {
      if (_cancelRequested) {
        _resetToDisconnected('Connection cancelled by user');
        return false;
      }
      _state = VpnConnectionState.error;
      _stage = ConnectionStage.error;
      _lastError = e.toString().replaceFirst('Exception: ', '');
      _statusMessage = _lastError;
      addLog('error', LogLevel.error, _lastError);
      notifyListeners();
      return false;
    }
  }

  /// Runs the authentic 5-stage Daylight connection pipeline with live cancellation
  /// and optional real HTTP 204 verification probe when running in Demo / Preview Mode.
  Future<bool> _connectDemoPipeline(VpnProfile profile) async {
    final stages = [
      (
        ConnectionStage.resolving,
        '1/5: Resolving Node',
        'Resolving ${profile.server}:${profile.serverPort}...',
        320
      ),
      (
        ConnectionStage.sslocal,
        '2/5: SOCKS5 Core',
        'Starting sslocal (${_settings.udpRelay ? 'TCP+UDP' : 'TCP'} + TCP_NODELAY)...',
        360
      ),
      (
        ConnectionStage.tun0,
        '3/5: Virtual TUN',
        'Provisioning TUN L3 (10.0.0.2/24)${_settings.disableIpv6 ? ' & IPv6 Shield' : ''}...',
        340
      ),
      (
        ConnectionStage.routing,
        '4/5: Routes & DNS',
        'Applying 0.0.0.0/0 route & DNS ${_settings.dnsPrimary} (cache flushed)...',
        300
      ),
    ];

    for (final step in stages) {
      if (_cancelRequested) {
        _resetToDisconnected('Connection cancelled by user');
        return false;
      }
      _stage = step.$1;
      _stageLabel = step.$2;
      _statusMessage = step.$3;
      addLog('stage', LogLevel.info, '${step.$2} • ${step.$3}');
      notifyListeners();

      if (!await _cancellableDelay(Duration(milliseconds: step.$4))) {
        _resetToDisconnected('Connection cancelled by user');
        return false;
      }
    }

    if (_settings.verifyTunnel) {
      _stage = ConnectionStage.verifying;
      _stageLabel = '5/5: Verifying Net';
      _statusMessage = 'Checking internet & DNS flow through tunnel...';
      addLog('verify', LogLevel.info, 'Probing cp.cloudflare.com/generate_204...');
      notifyListeners();

      final probeLat = await _runConnectivityProbe();
      if (_cancelRequested) {
        _resetToDisconnected('Connection cancelled by user');
        return false;
      }
      _tunnelVerified = probeLat != null;
      _verifyLatencyMs = probeLat;
      if (probeLat != null) {
        addLog('verify', LogLevel.ok, 'Internet & DNS verified (${probeLat}ms)');
      } else {
        addLog('verify', LogLevel.warn, 'Demo probe offline — continuing in preview mode');
      }
    }

    _connectedAt = DateTime.now();
    _ipv6ShieldActive = _settings.disableIpv6;
    _state = VpnConnectionState.connected;
    _stage = ConnectionStage.connected;
    _stageLabel = 'Live Flow Active';
    final latPart = _verifyLatencyMs != null ? ' • verified ${_verifyLatencyMs}ms' : '';
    _statusMessage =
        'TUN active • ${_ipv6ShieldActive ? 'IPv6 disabled' : 'IPv6 active'}$latPart • ${profile.name}';
    addLog('connect', LogLevel.ok, 'Connected via ${profile.name} (Demo Engine)');
    _startDemoTelemetry();
    notifyListeners();
    return true;
  }

  Future<int?> _runConnectivityProbe() async {
    final sw = Stopwatch()..start();
    try {
      final resp = await http
          .get(Uri.parse('http://cp.cloudflare.com/generate_204'))
          .timeout(const Duration(seconds: 3));
      sw.stop();
      if (resp.statusCode >= 200 && resp.statusCode < 400) {
        return sw.elapsedMilliseconds;
      }
    } catch (_) {
      await _cancellableDelay(const Duration(milliseconds: 350));
    }
    return null;
  }

  Future<bool> _cancellableDelay(Duration total) async {
    const stepMs = 40;
    var elapsed = 0;
    while (elapsed < total.inMilliseconds) {
      if (_cancelRequested) return false;
      final waitMs = min(stepMs, total.inMilliseconds - elapsed);
      await Future<void>.delayed(Duration(milliseconds: waitMs));
      elapsed += waitMs;
    }
    return !_cancelRequested;
  }

  /// Instant lock-free cancellation while connecting.
  Future<void> cancelConnect() async {
    if (_state != VpnConnectionState.connecting) return;
    _cancelRequested = true;
    _state = VpnConnectionState.disconnecting;
    _stage = ConnectionStage.teardown;
    _stageLabel = 'Cancelling Connection';
    _statusMessage = 'Aborting handshake & restoring network...';
    addLog('cancel', LogLevel.warn, 'Cancelling in-flight connection...');
    notifyListeners();

    if (!isUsingDemoEngine) {
      await _platform.cancelConnect();
    }
  }

  Future<void> disconnect() async {
    if (_state == VpnConnectionState.disconnected) return;
    if (_state == VpnConnectionState.connecting) {
      await cancelConnect();
      return;
    }

    _state = VpnConnectionState.disconnecting;
    _stage = ConnectionStage.teardown;
    _stageLabel = 'Restoring Routes & IPv6';
    _statusMessage = 'Tearing down TUN interface & restoring DNS...';
    addLog('disconnect', LogLevel.info, 'Terminating VPN tunnel...');
    notifyListeners();

    _demoStatsTimer?.cancel();
    _demoStatsTimer = null;

    if (!isUsingDemoEngine) {
      await _platform.stopVpn();
    } else {
      await Future<void>.delayed(const Duration(milliseconds: 280));
    }

    _resetToDisconnected('VPN Disconnected • Routes, DNS & IPv6 restored');
  }

  void _resetToDisconnected(String message) {
    _demoStatsTimer?.cancel();
    _demoStatsTimer = null;
    _cancelRequested = false;
    _connectedAt = null;
    _ipv6ShieldActive = false;
    _tunnelVerified = false;
    _verifyLatencyMs = null;
    _state = VpnConnectionState.disconnected;
    _stage = ConnectionStage.idle;
    _stageLabel = 'Direct Physical Route';
    _statusMessage = 'System using standard mobile route';
    _stats = TrafficStats.empty();
    addLog('disconnect', LogLevel.info, message);
    notifyListeners();
  }

  void _startDemoTelemetry() {
    _demoStatsTimer?.cancel();
    int rxTotal = 0;
    int txTotal = 0;

    _demoStatsTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (_state != VpnConnectionState.connected) return;
      final rxBps = (120000 + _rng.nextInt(2600000)).toDouble();
      final txBps = (24000 + _rng.nextInt(480000)).toDouble();
      rxTotal += rxBps.toInt();
      txTotal += txBps.toInt();
      final uptime = _connectedAt != null
          ? DateTime.now().difference(_connectedAt!)
          : Duration.zero;
      _pushTrafficSample(
        rxSpeed: rxBps,
        txSpeed: txBps,
        rxTotal: rxTotal,
        txTotal: txTotal,
        uptime: uptime,
      );
    });
  }

  void _pushTrafficSample({
    required double rxSpeed,
    required double txSpeed,
    required int rxTotal,
    required int txTotal,
    required Duration uptime,
  }) {
    final nextRx = List<double>.from(_stats.rxHistory)..add(rxSpeed);
    final nextTx = List<double>.from(_stats.txHistory)..add(txSpeed);
    while (nextRx.length > 18) {
      nextRx.removeAt(0);
    }
    while (nextTx.length > 18) {
      nextTx.removeAt(0);
    }
    _stats = TrafficStats(
      rxSpeedBps: rxSpeed,
      txSpeedBps: txSpeed,
      rxTotalBytes: rxTotal,
      txTotalBytes: txTotal,
      uptime: uptime,
      rxHistory: nextRx,
      txHistory: nextTx,
    );
    notifyListeners();
  }

  @override
  void dispose() {
    _demoStatsTimer?.cancel();
    _eventSub?.cancel();
    _statsSub?.cancel();
    _logSub?.cancel();
    super.dispose();
  }
}
