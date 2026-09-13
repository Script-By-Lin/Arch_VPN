#!/usr/bin/env bash
# ==============================================================================
# AuraLink VPN - Clean Uninstaller
#
# Direct 1-Line Curl Uninstallation:
#   curl -fsSL https://raw.githubusercontent.com/Script-By-Lin/Arch_VPN/main/uninstall.sh | sudo bash
# ==============================================================================
set -euo pipefail

CYAN="\033[96m"
GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
BOLD="\033[1m"
RESET="\033[0m"

if [[ $EUID -ne 0 ]]; then
  if [[ "$0" == "bash" || "$0" == "sh" || "$0" == "-bash" || ! -f "$0" ]]; then
    echo -e "${RED}[!] Root permissions required for uninstallation.${RESET}"
    echo -e "    Please run with sudo:"
    echo -e "    ${BOLD}curl -fsSL https://raw.githubusercontent.com/Script-By-Lin/Arch_VPN/main/uninstall.sh | sudo bash${RESET}\n"
    exit 1
  else
    echo -e "${YELLOW}[*] Root permissions required for uninstall. Requesting sudo...${RESET}"
    exec sudo "$0" "$@"
  fi
fi

echo -e "${YELLOW}[*] Stopping any active AuraLink VPN sessions...${RESET}"
/usr/local/bin/auralink disconnect 2>/dev/null || true
/usr/local/bin/auralink-vpn disconnect 2>/dev/null || true
/usr/local/bin/shadowtun disconnect 2>/dev/null || true
/usr/local/bin/shadowtun-vpn disconnect 2>/dev/null || true
pkill -f "tun2socks" 2>/dev/null || true
pkill -f "sslocal -c" 2>/dev/null || true

echo -e "${YELLOW}[*] Removing installed files and links...${RESET}"
rm -rf /opt/auralink
rm -rf /opt/shadowtun
rm -f /usr/local/bin/auralink
rm -f /usr/local/bin/auralink-vpn
rm -f /usr/local/bin/shadowtun
rm -f /usr/local/bin/shadowtun-vpn
rm -f /usr/local/bin/vpn-core-helper
rm -f /etc/sudoers.d/auralink
rm -f /etc/sudoers.d/shadowtun
rm -f /usr/share/applications/auralink.desktop
rm -f /usr/share/applications/shadowtun.desktop
rm -f /usr/share/icons/hicolor/scalable/apps/auralink.svg
rm -f /usr/share/icons/hicolor/256x256/apps/auralink.png
rm -f /usr/share/icons/hicolor/scalable/apps/shadowtun.svg
rm -f /usr/share/icons/hicolor/256x256/apps/shadowtun.png

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
fi

echo -e "${GREEN}${BOLD}[✓] AuraLink VPN has been cleanly uninstalled.${RESET}"
