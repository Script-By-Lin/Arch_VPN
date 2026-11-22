#!/usr/bin/env bash
# ==============================================================================
# Fedora / RHEL / openSUSE RPM Spec & Builder for AuraLink VPN
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

PKG_NAME="auralink"
VERSION="1.0.0"
RPMBUILD_DIR="$ROOT_DIR/dist/rpmbuild"

rm -rf "$RPMBUILD_DIR"
mkdir -p "$RPMBUILD_DIR"/{SPECS,SOURCES,BUILD,RPMS,SRPMS}

cat <<EOF > "$RPMBUILD_DIR/SPECS/auralink.spec"
Name:           ${PKG_NAME}
Version:        ${VERSION}
Release:        1%{?dist}
Summary:        Cross-Distro Shadowsocks & tun2socks VPN Client for Linux
License:        GPLv3
URL:            https://github.com/Script-By-Lin/Arch_VPN
Requires:       python3, python3-qt5, iproute, curl, jq, procps-ng

%description
AuraLink VPN provides high-speed full-system tunneling over Shadowsocks with
automatic ssconf:// key parsing, IPv6 leak blocking, DNS protection, and GUI/CLI.

%install
mkdir -p %{buildroot}/opt/auralink
mkdir -p %{buildroot}/usr/local/bin
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/pixmaps
mkdir -p %{buildroot}/usr/share/icons/hicolor/scalable/apps

cp -r ${ROOT_DIR}/core %{buildroot}/opt/auralink/
cp -r ${ROOT_DIR}/gui %{buildroot}/opt/auralink/
cp -r ${ROOT_DIR}/cli %{buildroot}/opt/auralink/
cp -r ${ROOT_DIR}/bin %{buildroot}/opt/auralink/
chmod 0755 %{buildroot}/opt/auralink/bin/auralink %{buildroot}/opt/auralink/bin/vpn-core-helper %{buildroot}/opt/auralink/cli/main.py %{buildroot}/opt/auralink/gui/app.py

ln -sf /opt/auralink/bin/auralink %{buildroot}/usr/local/bin/auralink
ln -sf /opt/auralink/bin/auralink %{buildroot}/usr/local/bin/auralink-vpn
ln -sf /opt/auralink/bin/vpn-core-helper %{buildroot}/usr/local/bin/vpn-core-helper
ln -sf /opt/auralink/bin/auralink %{buildroot}/usr/bin/auralink

cp ${ROOT_DIR}/packaging/auralink.desktop %{buildroot}/usr/share/applications/
cp ${ROOT_DIR}/gui/assets/icon.png %{buildroot}/usr/share/pixmaps/auralink.png
cp ${ROOT_DIR}/gui/assets/icon.svg %{buildroot}/usr/share/icons/hicolor/scalable/apps/auralink.svg
for s in 16 22 24 32 48 64 128 256 512; do
  mkdir -p %{buildroot}/usr/share/icons/hicolor/\${s}x\${s}/apps
  if [ -f "${ROOT_DIR}/gui/assets/icons/auralink_\${s}x\${s}.png" ]; then
    cp "${ROOT_DIR}/gui/assets/icons/auralink_\${s}x\${s}.png" %{buildroot}/usr/share/icons/hicolor/\${s}x\${s}/apps/auralink.png
  fi
done

%post
mkdir -p /etc/sudoers.d
TMP_SUDO="\$(mktemp)"
cat << 'SUDO_EOF' > "\$TMP_SUDO"
ALL ALL=(ALL) NOPASSWD: /usr/local/bin/vpn-core-helper, /usr/bin/tun2socks, /usr/local/bin/tun2socks, /usr/bin/ip, /usr/sbin/ip, /usr/sbin/sysctl, /usr/bin/sysctl, /usr/bin/resolvectl, /usr/bin/pkill, /usr/bin/kill
SUDO_EOF
chmod 0440 "\$TMP_SUDO"
if command -v visudo >/dev/null 2>&1; then
  visudo -cf "\$TMP_SUDO" >/dev/null 2>&1 && mv -f "\$TMP_SUDO" /etc/sudoers.d/auralink || rm -f "\$TMP_SUDO"
else
  mv -f "\$TMP_SUDO" /etc/sudoers.d/auralink
fi
chmod 0440 /etc/sudoers.d/auralink 2>/dev/null || true
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi

%postun
if [ "\$1" -eq 0 ]; then
  rm -f /etc/sudoers.d/auralink
  if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
  fi
fi

%files
/opt/auralink
/usr/local/bin/auralink
/usr/local/bin/auralink-vpn
/usr/local/bin/vpn-core-helper
/usr/bin/auralink
/usr/share/applications/auralink.desktop
/usr/share/pixmaps/auralink.png
/usr/share/icons/hicolor/scalable/apps/auralink.svg
/usr/share/icons/hicolor/*/apps/auralink.png
EOF

if command -v rpmbuild >/dev/null 2>&1; then
  rpmbuild --define "_topdir $RPMBUILD_DIR" -bb "$RPMBUILD_DIR/SPECS/auralink.spec"
  echo "[✓] Built RPM package in: $RPMBUILD_DIR/RPMS/"
else
  echo "[!] rpmbuild not installed on this system. Prepared spec file in: $RPMBUILD_DIR/SPECS/auralink.spec"
fi
