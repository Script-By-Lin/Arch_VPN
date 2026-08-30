#!/usr/bin/env bash
# ==============================================================================
# Fedora / RHEL / openSUSE RPM Spec & Builder for ShadowTun VPN
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

PKG_NAME="shadowtun"
VERSION="1.0.0"
RPMBUILD_DIR="$ROOT_DIR/dist/rpmbuild"

rm -rf "$RPMBUILD_DIR"
mkdir -p "$RPMBUILD_DIR"/{SPECS,SOURCES,BUILD,RPMS,SRPMS}

cat <<EOF > "$RPMBUILD_DIR/SPECS/shadowtun.spec"
Name:           ${PKG_NAME}
Version:        ${VERSION}
Release:        1%{?dist}
Summary:        Cross-Distro Shadowsocks & tun2socks VPN Client for Linux
License:        GPLv3
URL:            https://github.com/shadowtun/shadowtun-linux
Requires:       python3, python3-qt5, iproute, curl, jq

%description
ShadowTun VPN provides high-speed full-system tunneling over Shadowsocks with
automatic ssconf:// key parsing, DNS leak protection, and a modern GUI/CLI.

%install
mkdir -p %{buildroot}/opt/shadowtun
mkdir -p %{buildroot}/usr/local/bin
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/icons/hicolor/scalable/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps

cp -r ${ROOT_DIR}/core %{buildroot}/opt/shadowtun/
cp -r ${ROOT_DIR}/gui %{buildroot}/opt/shadowtun/
cp -r ${ROOT_DIR}/cli %{buildroot}/opt/shadowtun/
cp -r ${ROOT_DIR}/bin %{buildroot}/opt/shadowtun/

ln -sf /opt/shadowtun/bin/shadowtun %{buildroot}/usr/local/bin/shadowtun
ln -sf /opt/shadowtun/bin/shadowtun %{buildroot}/usr/local/bin/shadowtun-vpn
ln -sf /opt/shadowtun/bin/vpn-core-helper %{buildroot}/usr/local/bin/vpn-core-helper

cp ${ROOT_DIR}/packaging/shadowtun.desktop %{buildroot}/usr/share/applications/
cp ${ROOT_DIR}/gui/assets/icon.svg %{buildroot}/usr/share/icons/hicolor/scalable/apps/shadowtun.svg
cp ${ROOT_DIR}/gui/assets/icon.png %{buildroot}/usr/share/icons/hicolor/256x256/apps/shadowtun.png

%post
cat << 'SUDO_EOF' > /etc/sudoers.d/shadowtun
ALL ALL=(ALL) NOPASSWD: /usr/local/bin/vpn-core-helper, /usr/bin/tun2socks, /usr/local/bin/tun2socks, /usr/bin/ip, /usr/bin/resolvectl, /usr/bin/pkill, /usr/bin/kill
SUDO_EOF
chmod 0440 /etc/sudoers.d/shadowtun

%files
/opt/shadowtun
/usr/local/bin/shadowtun
/usr/local/bin/shadowtun-vpn
/usr/local/bin/vpn-core-helper
/usr/share/applications/shadowtun.desktop
/usr/share/icons/hicolor/scalable/apps/shadowtun.svg
/usr/share/icons/hicolor/256x256/apps/shadowtun.png
EOF

if command -v rpmbuild >/dev/null 2>&1; then
  rpmbuild --define "_topdir $RPMBUILD_DIR" -bb "$RPMBUILD_DIR/SPECS/shadowtun.spec"
  echo "[✓] Built RPM package in: $RPMBUILD_DIR/RPMS/"
else
  echo "[!] rpmbuild not installed on this system. Prepared spec file in: $RPMBUILD_DIR/SPECS/shadowtun.spec"
fi
