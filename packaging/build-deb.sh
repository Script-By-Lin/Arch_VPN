#!/usr/bin/env bash
# ==============================================================================
# Debian / Ubuntu .deb Package Builder for ShadowTun VPN
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

PKG_NAME="shadowtun"
VERSION="1.0.0"
ARCH="amd64"
BUILD_DIR="$ROOT_DIR/dist/deb-build/${PKG_NAME}_${VERSION}_${ARCH}"

rm -rf "$ROOT_DIR/dist/deb-build"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/opt/shadowtun"
mkdir -p "$BUILD_DIR/usr/local/bin"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$BUILD_DIR/etc/sudoers.d"

# Copy App Files
cp -r "$ROOT_DIR/core" "$BUILD_DIR/opt/shadowtun/"
cp -r "$ROOT_DIR/gui" "$BUILD_DIR/opt/shadowtun/"
cp -r "$ROOT_DIR/cli" "$BUILD_DIR/opt/shadowtun/"
cp -r "$ROOT_DIR/bin" "$BUILD_DIR/opt/shadowtun/"

# Symlinks
ln -sf "/opt/shadowtun/bin/shadowtun" "$BUILD_DIR/usr/local/bin/shadowtun"
ln -sf "/opt/shadowtun/bin/shadowtun" "$BUILD_DIR/usr/local/bin/shadowtun-vpn"
ln -sf "/opt/shadowtun/bin/vpn-core-helper" "$BUILD_DIR/usr/local/bin/vpn-core-helper"

# Desktop & Icons
cp "$ROOT_DIR/packaging/shadowtun.desktop" "$BUILD_DIR/usr/share/applications/"
cp "$ROOT_DIR/gui/assets/icon.svg" "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/shadowtun.svg"
cp "$ROOT_DIR/gui/assets/icon.png" "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps/shadowtun.png"

# Control file
cat <<EOF > "$BUILD_DIR/DEBIAN/control"
Package: ${PKG_NAME}
Version: ${VERSION}
Section: net
Priority: optional
Architecture: ${ARCH}
Depends: python3, python3-pyqt5, iproute2, curl, jq
Maintainer: ShadowTun Team <support@shadowtun.org>
Description: Cross-Distro Shadowsocks & tun2socks VPN Client for Linux
 ShadowTun VPN provides high-speed full-system tunneling over Shadowsocks with
 automatic ssconf:// key parsing, DNS leak protection, and a modern GUI/CLI.
EOF

# Postinst script for sudoers setup
cat <<'EOF' > "$BUILD_DIR/DEBIAN/postinst"
#!/bin/sh
set -e
cat << 'SUDO_EOF' > /etc/sudoers.d/shadowtun
ALL ALL=(ALL) NOPASSWD: /usr/local/bin/vpn-core-helper, /usr/bin/tun2socks, /usr/local/bin/tun2socks, /usr/bin/ip, /usr/bin/resolvectl, /usr/bin/pkill, /usr/bin/kill
SUDO_EOF
chmod 0440 /etc/sudoers.d/shadowtun
exit 0
EOF

chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# Build .deb
if command -v dpkg-deb >/dev/null 2>&1; then
  dpkg-deb --build "$BUILD_DIR" "$ROOT_DIR/dist/${PKG_NAME}_${VERSION}_${ARCH}.deb"
  echo "[✓] Built Debian package: dist/${PKG_NAME}_${VERSION}_${ARCH}.deb"
else
  echo "[!] dpkg-deb not found on this system. Prepared package structure in: $BUILD_DIR"
fi
