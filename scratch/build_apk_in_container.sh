#!/usr/bin/env bash
set -euo pipefail

cd /workspace

echo "=== [1/6] Flutter & Android SDK Version ==="
flutter --version

echo "=== [2/6] Bootstrapping Gradle Wrapper if missing ==="
if [[ ! -x android/gradlew || ! -f android/gradle/wrapper/gradle-wrapper.properties ]]; then
  rm -rf /tmp/fl_tpl
  flutter create --platforms=android --org com.auralink --project-name auralink_vpn /tmp/fl_tpl >/dev/null
  mkdir -p android/gradle/wrapper
  cp /tmp/fl_tpl/android/gradlew android/gradlew
  cp /tmp/fl_tpl/android/gradlew.bat android/gradlew.bat
  cp -r /tmp/fl_tpl/android/gradle/wrapper/* android/gradle/wrapper/
  chmod +x android/gradlew
  rm -rf /tmp/fl_tpl
fi

echo "=== [3/6] Bundling Android ARM64 Native Binaries (libsslocal.so & libtun2socks.so) ==="
JNI_ARM64="android/app/src/main/jniLibs/arm64-v8a"
mkdir -p "$JNI_ARM64"

if [[ ! -f "$JNI_ARM64/libsslocal.so" ]]; then
  TMP_SS="$(mktemp -d)"
  curl -fsSL "https://github.com/shadowsocks/shadowsocks-rust/releases/download/v1.25.0/shadowsocks-v1.25.0.aarch64-linux-android.tar.xz" -o "$TMP_SS/ss.tar.xz"
  tar -xJf "$TMP_SS/ss.tar.xz" -C "$TMP_SS"
  SS_BIN="$(find "$TMP_SS" -type f -name sslocal | head -n 1)"
  cp "$SS_BIN" "$JNI_ARM64/libsslocal.so"
  chmod 0755 "$JNI_ARM64/libsslocal.so"
  rm -rf "$TMP_SS"
  echo "  [OK] Bundled $JNI_ARM64/libsslocal.so (aarch64-linux-android)"
fi

if [[ ! -f "$JNI_ARM64/libtun2socks.so" ]]; then
  TMP_TUN="$(mktemp -d)"
  curl -fsSL "https://github.com/xjasonlyu/tun2socks/releases/download/v2.5.2/tun2socks-linux-arm64.zip" -o "$TMP_TUN/tun.zip"
  unzip -q "$TMP_TUN/tun.zip" -d "$TMP_TUN"
  TUN_BIN="$(find "$TMP_TUN" -type f -name 'tun2socks*' | head -n 1)"
  cp "$TUN_BIN" "$JNI_ARM64/libtun2socks.so"
  chmod 0755 "$JNI_ARM64/libtun2socks.so"
  rm -rf "$TMP_TUN"
  echo "  [OK] Bundled $JNI_ARM64/libtun2socks.so"
fi

echo "=== [4/6] Running flutter pub get & flutter analyze ==="
flutter pub get
flutter analyze

echo "=== [5/6] Running flutter test ==="
flutter test

echo "=== [6/6] Building Android Release APK ==="
flutter build apk --release

echo "=== [DONE] Verifying APK artifact ==="
ls -lh build/app/outputs/flutter-apk/app-release.apk
unzip -l build/app/outputs/flutter-apk/app-release.apk | grep -E "libsslocal\.so|libtun2socks\.so|libflutter\.so" || true
