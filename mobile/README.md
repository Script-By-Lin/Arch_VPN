# AuraLink Daylight — Flutter Mobile VPN App (Android & iOS)

Cross-platform Flutter mobile client for **AuraLink VPN**, sharing the same Daylight aesthetic, Shadowsocks (`ss://`, `ssconf://`, JSON) compatibility, 5-stage connection pipeline, instant cancel-while-connecting, and IPv6 Leak Shield as the Linux desktop client.

---

## Features

- **Daylight Light Theme**: Frosted alabaster UI (`#F1F5F9` / `#FFFFFF`), animated orbital connect/cancel button, interactive 4-hop tunnel pipeline (`Mobile Apps → TUN L3 → sslocal → VPN Node`), and dual Download/Upload live sparkline cards.
- **5-Stage Verified Connection Pipeline**:
  1. `1/5 Resolving Node`
  2. `2/5 SOCKS5 Core` (`mode: tcp_and_udp` + `no_delay: true` for fast DNS & QUIC)
  3. `3/5 Virtual TUN & IPv6 Shield`
  4. `4/5 Routes & DNS` (Cloudflare, Google, Quad9, AdGuard presets)
  5. `5/5 Verifying Net` (HTTP 204 internet & DNS probe before flipping to green)
- **Instant Cancel While Connecting**: Tapping the circular button while connecting immediately cancels via lock-free cancellation flags and restores network routes cleanly.
- **Clean Line-by-Line Log Stream**: Color-coded monospace terminal with `Wrap: Off/On`, `Copy`, and `Clear` controls.
- **Native Engine + Demo Fallback**: Includes native Android `VpnService` (Kotlin) and iOS `NEPacketTunnelProvider` (Swift) bridges, plus an automatic Demo Mode fallback so you can run and preview the entire app immediately even before bundling native `.so` / `.xcframework` binaries.

---

## Quick Start

### 1. Install Flutter SDK & Fetch Packages
```bash
cd mobile
flutter pub get
flutter test
```

### 2. Run in Preview / Demo Mode (Android Emulator, iOS Simulator, or Physical Device)
```bash
flutter run
```
*(If `libsslocal.so` / `libtun2socks.so` or the iOS `PacketTunnel.appex` are not bundled yet, the app automatically runs in Demo Mode so you can test key importing, ping latency checks, the 5-stage animated pipeline, cancel-while-connecting, and log stream right away.)*

---

## Enabling Live Native VPN Tunnels

### Android (`VpnService` + `shadowsocks-rust` + `tun2socks`)
1. Place ARM64 / ARMv7 / x86_64 binaries named `libsslocal.so` and `libtun2socks.so` inside:
   - `android/app/src/main/jniLibs/arm64-v8a/`
   - `android/app/src/main/jniLibs/armeabi-v7a/` (optional)
   - `android/app/src/main/jniLibs/x86_64/` (for emulators)
2. `android/app/build.gradle` already sets `jniLibs.useLegacyPackaging = true` and `AndroidManifest.xml` sets `extractNativeLibs="true"`, so `AuraLinkVpnService.kt` automatically detects and launches both binaries with full-tunnel `0.0.0.0/0` routing and IPv6 leak blocking.
3. Build release APK:
   ```bash
   flutter build apk --release
   ```

### iOS (`NEPacketTunnelProvider`)
1. Open `mobile/ios/Runner.xcworkspace` in Xcode on macOS.
2. Add a **Network Extension → Packet Tunnel Provider** target named `PacketTunnel` with bundle ID `com.auralink.vpn.PacketTunnel`, enable the **Network Extensions (Packet Tunnel)** capability on both `Runner` and `PacketTunnel`, and include `ios/PacketTunnel/PacketTunnelProvider.swift`.
3. Link your Shadowsocks/tun2socks native framework (e.g., `Libbox.xcframework` or `Tun2SocksKit.xcframework`) in `PacketTunnelProvider.startNativePacketForwarder(config:)`.
4. Build & sign in Xcode or run `flutter build ipa`.
