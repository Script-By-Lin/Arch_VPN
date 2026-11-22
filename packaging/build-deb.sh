#!/usr/bin/env bash
# ==============================================================================
# Debian / Ubuntu .deb Package Builder for AuraLink VPN
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

PKG_NAME="auralink"
VERSION="1.0.0"

# Auto-detect architecture (amd64 / arm64)
if command -v dpkg >/dev/null 2>&1; then
  ARCH="$(dpkg --print-architecture)"
else
  case "$(uname -m)" in
    x86_64|amd64) ARCH="amd64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    *) ARCH="all" ;;
  esac
fi

BUILD_DIR="$ROOT_DIR/dist/deb-build/${PKG_NAME}_${VERSION}_${ARCH}"

rm -rf "$ROOT_DIR/dist/deb-build"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/opt/auralink"
mkdir -p "$BUILD_DIR/usr/local/bin"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/pixmaps"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps"

# Copy App Files
cp -r "$ROOT_DIR/core" "$BUILD_DIR/opt/auralink/"
cp -r "$ROOT_DIR/gui" "$BUILD_DIR/opt/auralink/"
cp -r "$ROOT_DIR/cli" "$BUILD_DIR/opt/auralink/"
cp -r "$ROOT_DIR/bin" "$BUILD_DIR/opt/auralink/"
chmod 0755 "$BUILD_DIR/opt/auralink/bin/auralink" "$BUILD_DIR/opt/auralink/bin/vpn-core-helper" "$BUILD_DIR/opt/auralink/cli/main.py" "$BUILD_DIR/opt/auralink/gui/app.py"

# Symlinks
ln -sf "/opt/auralink/bin/auralink" "$BUILD_DIR/usr/local/bin/auralink"
ln -sf "/opt/auralink/bin/auralink" "$BUILD_DIR/usr/local/bin/auralink-vpn"
ln -sf "/opt/auralink/bin/vpn-core-helper" "$BUILD_DIR/usr/local/bin/vpn-core-helper"
ln -sf "/opt/auralink/bin/auralink" "$BUILD_DIR/usr/bin/auralink"

# Desktop & Icons
cp "$ROOT_DIR/packaging/auralink.desktop" "$BUILD_DIR/usr/share/applications/"
cp "$ROOT_DIR/gui/assets/icon.png" "$BUILD_DIR/usr/share/pixmaps/auralink.png"
cp "$ROOT_DIR/gui/assets/icon.svg" "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/auralink.svg"
for s in 16 22 24 32 48 64 128 256 512; do
  mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/${s}x${s}/apps"
  if [[ -f "$ROOT_DIR/gui/assets/icons/auralink_${s}x${s}.png" ]]; then
    cp "$ROOT_DIR/gui/assets/icons/auralink_${s}x${s}.png" "$BUILD_DIR/usr/share/icons/hicolor/${s}x${s}/apps/auralink.png"
  fi
done

# Control file
cat <<EOF > "$BUILD_DIR/DEBIAN/control"
Package: ${PKG_NAME}
Version: ${VERSION}
Section: net
Priority: optional
Architecture: ${ARCH}
Depends: python3, python3-pyqt5, iproute2, curl, jq, procps
Maintainer: AuraLink Team <support@auralink.org>
Description: Cross-Distro Shadowsocks & tun2socks VPN Client for Linux
 AuraLink VPN provides high-speed full-system tunneling over Shadowsocks with
 automatic ssconf:// key parsing, IPv6 leak blocking, DNS protection, and GUI/CLI.
EOF

# Postinst script for validated sudoers setup
cat <<'EOF' > "$BUILD_DIR/DEBIAN/postinst"
#!/bin/sh
set -e
mkdir -p /etc/sudoers.d
TMP_SUDO="$(mktemp)"
cat << 'SUDO_EOF' > "$TMP_SUDO"
ALL ALL=(ALL) NOPASSWD: /usr/local/bin/vpn-core-helper, /usr/bin/tun2socks, /usr/local/bin/tun2socks, /usr/bin/ip, /usr/sbin/ip, /sbin/ip, /bin/ip, /usr/sbin/sysctl, /usr/bin/sysctl, /sbin/sysctl, /usr/bin/resolvectl, /usr/bin/pkill, /usr/bin/kill, /bin/kill
SUDO_EOF
chmod 0440 "$TMP_SUDO"
if command -v visudo >/dev/null 2>&1; then
  visudo -cf "$TMP_SUDO" >/dev/null 2>&1 && mv -f "$TMP_SUDO" /etc/sudoers.d/auralink || rm -f "$TMP_SUDO"
else
  mv -f "$TMP_SUDO" /etc/sudoers.d/auralink
fi
chmod 0440 /etc/sudoers.d/auralink 2>/dev/null || true
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
exit 0
EOF

# Postrm cleanup
cat <<'EOF' > "$BUILD_DIR/DEBIAN/postrm"
#!/bin/sh
set -e
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
  rm -f /etc/sudoers.d/auralink
  if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
  fi
fi
exit 0
EOF

chmod 0755 "$BUILD_DIR/DEBIAN/postinst" "$BUILD_DIR/DEBIAN/postrm"

# Build .deb
mkdir -p "$ROOT_DIR/dist"
if command -v dpkg-deb >/dev/null 2>&1; then
  dpkg-deb --build "$BUILD_DIR" "$ROOT_DIR/dist/${PKG_NAME}_${VERSION}_${ARCH}.deb"
  echo "[✓] Built Debian package: dist/${PKG_NAME}_${VERSION}_${ARCH}.deb"
else
  echo "[!] dpkg-deb not found on this system. Prepared package structure in: $BUILD_DIR"
fi
