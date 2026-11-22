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

PURGE_CONFIG=false
for arg in "$@"; do
  case "$arg" in
    --purge) PURGE_CONFIG=true ;;
    -h|--help)
      echo "Usage: sudo $0 [--purge]"
      echo "  --purge   Also delete user configuration, profiles, and logs (~/.config/auralink)"
      exit 0
      ;;
  esac
done

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

disconnect_as_user() {
  local user="$1"
  local bin
  for bin in /usr/local/bin/auralink /usr/local/bin/auralink-vpn /usr/local/bin/shadowtun /usr/local/bin/shadowtun-vpn; do
    if [[ -x "$bin" ]]; then
      if [[ "$user" == "root" ]]; then
        "$bin" disconnect >/dev/null 2>&1 || true
      elif command -v sudo >/dev/null 2>&1; then
        sudo -u "$user" "$bin" disconnect >/dev/null 2>&1 || true
      elif command -v su >/dev/null 2>&1; then
        su -s /bin/bash "$user" -c "'$bin' disconnect" >/dev/null 2>&1 || true
      fi
    fi
  done
}

echo -e "${YELLOW}[*] Stopping any active AuraLink VPN sessions...${RESET}"

# Disconnect sessions owned by invoking non-root user (so ~/.config/auralink/state/session.json is found)
TARGET_USERS=()
if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
  TARGET_USERS+=("$SUDO_USER")
fi
# Also detect any user with an active session file
for sess in /home/*/.config/auralink/state/session.json /home/*/.config/shadowtun/state/session.json; do
  if [[ -f "$sess" ]]; then
    u="$(stat -c '%U' "$sess" 2>/dev/null || true)"
    if [[ -n "$u" && "$u" != "root" && ! " ${TARGET_USERS[*]:-} " =~ " ${u} " ]]; then
      TARGET_USERS+=("$u")
    fi
  fi
done

if [[ ${#TARGET_USERS[@]} -gt 0 ]]; then
  for u in "${TARGET_USERS[@]}"; do
    disconnect_as_user "$u"
  done
fi
# Also disconnect if a session was started directly as root
disconnect_as_user "root"

# Stop any running AuraLink GUI / core processes
pkill -f "/opt/auralink/gui/app.py" 2>/dev/null || true
pkill -f "/opt/shadowtun/gui/app.py" 2>/dev/null || true
pkill -f "tun2socks --device" 2>/dev/null || true
pkill -x "tun2socks" 2>/dev/null || true
pkill -f "sslocal -c .*auralink" 2>/dev/null || true
pkill -f "sslocal -c .*shadowtun" 2>/dev/null || true

# Safety cleanup if a dangling tun0 interface remains
if command -v ip >/dev/null 2>&1 && ip link show tun0 >/dev/null 2>&1; then
  if command -v resolvectl >/dev/null 2>&1; then
    resolvectl revert tun0 2>/dev/null || true
  elif command -v systemd-resolve >/dev/null 2>&1; then
    systemd-resolve --revert -i tun0 2>/dev/null || true
  fi
  ip route del default dev tun0 2>/dev/null || true
  ip link delete tun0 2>/dev/null || true
  if [[ -w /proc/sys/net/ipv6/conf/all/disable_ipv6 ]]; then
    echo 0 > /proc/sys/net/ipv6/conf/all/disable_ipv6 2>/dev/null || true
    echo 0 > /proc/sys/net/ipv6/conf/default/disable_ipv6 2>/dev/null || true
  fi
fi

echo -e "${YELLOW}[*] Removing installed files and links...${RESET}"
rm -rf /opt/auralink
rm -rf /opt/shadowtun
rm -f /usr/local/bin/auralink
rm -f /usr/local/bin/auralink-vpn
rm -f /usr/local/bin/shadowtun
rm -f /usr/local/bin/shadowtun-vpn
rm -f /usr/local/bin/vpn-core-helper
[[ -L /usr/bin/auralink ]] && rm -f /usr/bin/auralink
rm -f /etc/sudoers.d/auralink
rm -f /etc/sudoers.d/shadowtun
rm -f /usr/share/applications/auralink.desktop
rm -f /usr/share/applications/shadowtun.desktop
rm -f /usr/share/pixmaps/auralink.png
rm -f /usr/share/pixmaps/shadowtun.png
rm -f /usr/share/icons/hicolor/scalable/apps/auralink.svg
rm -f /usr/share/icons/hicolor/scalable/apps/shadowtun.svg

for s in 16 22 24 32 48 64 128 256 512; do
  rm -f "/usr/share/icons/hicolor/${s}x${s}/apps/auralink.png"
  rm -f "/usr/share/icons/hicolor/${s}x${s}/apps/shadowtun.png"
done

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications 2>/dev/null || true
fi

if [[ "$PURGE_CONFIG" == true ]]; then
  echo -e "${YELLOW}[*] Purging user configuration and logs...${RESET}"
  if [[ ${#TARGET_USERS[@]} -gt 0 ]]; then
    for u in "${TARGET_USERS[@]}"; do
      u_home="$(getent passwd "$u" 2>/dev/null | cut -d: -f6 || echo "/home/$u")"
      if [[ -n "$u_home" && -d "$u_home" ]]; then
        rm -rf "$u_home/.config/auralink" "$u_home/.config/shadowtun"
      fi
    done
  fi
  rm -rf /root/.config/auralink /root/.config/shadowtun
  echo -e "${GREEN}${BOLD}[✓] AuraLink VPN and all user configs have been cleanly uninstalled.${RESET}"
else
  echo -e "${GREEN}${BOLD}[✓] AuraLink VPN has been cleanly uninstalled.${RESET}"
  echo -e "${CYAN}[i] User profiles/settings in ~/.config/auralink were preserved. Re-run with --purge to remove them.${RESET}"
fi
