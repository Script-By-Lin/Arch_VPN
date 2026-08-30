#!/usr/bin/env bash
# ==============================================================================
# ShadowTun VPN - Clean Uninstaller
# ==============================================================================
set -euo pipefail

CYAN="\033[96m"
GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
BOLD="\033[1m"
RESET="\033[0m"

if [[ $EUID -ne 0 ]]; then
  echo -e "${YELLOW}[*] Root permissions required for uninstall. Requesting sudo...${RESET}"
  exec sudo "$0" "$@"
fi

echo -e "${YELLOW}[*] Stopping any active ShadowTun VPN sessions...${RESET}"
/usr/local/bin/shadowtun disconnect 2>/dev/null || true
/usr/local/bin/shadowtun-vpn disconnect 2>/dev/null || true
pkill -f "tun2socks" 2>/dev/null || true
pkill -f "sslocal -c" 2>/dev/null || true

echo -e "${YELLOW}[*] Removing installed files and links...${RESET}"
rm -rf /opt/shadowtun
rm -f /usr/local/bin/shadowtun
rm -f /usr/local/bin/shadowtun-vpn
rm -f /usr/local/bin/vpn-core-helper
rm -f /etc/sudoers.d/shadowtun
rm -f /usr/share/applications/shadowtun.desktop
rm -f /usr/share/icons/hicolor/scalable/apps/shadowtun.svg
rm -f /usr/share/icons/hicolor/256x256/apps/shadowtun.png

echo -e "${GREEN}${BOLD}[✓] ShadowTun VPN has been cleanly uninstalled.${RESET}"
