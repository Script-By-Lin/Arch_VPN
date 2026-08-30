#!/usr/bin/env bash
# ==============================================================================
# ShadowTun VPN - Universal Linux Installer
# Supports: Arch Linux, Manjaro, CachyOS, Debian, Ubuntu, Linux Mint,
#           Fedora, RHEL, openSUSE, Alpine, etc.
# Configures dependencies, static binary fallbacks, desktop launcher,
# and one-time sudoers permissions.
# ==============================================================================
set -euo pipefail

CYAN="\033[96m"
GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
BOLD="\033[1m"
RESET="\033[0m"

echo -e "${CYAN}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║          ShadowTun VPN - Universal Linux Installer        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${RESET}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="/opt/shadowtun"
BIN_LINK="/usr/local/bin/shadowtun"
HELPER_LINK="/usr/local/bin/vpn-core-helper"
SUDOERS_FILE="/etc/sudoers.d/shadowtun"

# Require sudo for installation steps
if [[ $EUID -ne 0 ]]; then
  echo -e "${YELLOW}[*] Root permissions required for installation. Requesting sudo...${RESET}"
  exec sudo "$0" "$@"
fi

# Detect Architecture
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|amd64) BIN_ARCH="amd64"; SS_ARCH="x86_64-unknown-linux-gnu" ;;
  aarch64|arm64) BIN_ARCH="arm64"; SS_ARCH="aarch64-unknown-linux-gnu" ;;
  *) echo -e "${RED}[✗] Unsupported architecture: $ARCH${RESET}"; exit 1 ;;
esac

# 1. Detect Package Manager and Install Dependencies
echo -e "${CYAN}[1/6] Detecting OS and installing dependencies...${RESET}"

if command -v pacman >/dev/null 2>&1; then
  echo "Detected Arch Linux / Pacman"
  pacman -Sy --noconfirm --needed python python-pyqt5 iproute2 systemd-resolvconf curl jq shadowsocks-rust tun2socks || true
elif command -v apt-get >/dev/null 2>&1; then
  echo "Detected Debian / Ubuntu"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y python3 python3-pyqt5 iproute2 systemd-resolved curl jq shadowsocks-libev || true
elif command -v dnf >/dev/null 2>&1; then
  echo "Detected Fedora / RHEL"
  dnf install -y python3 python3-qt5 iproute systemd-resolved curl jq || true
elif command -v zypper >/dev/null 2>&1; then
  echo "Detected openSUSE"
  zypper install -y python3 python3-qt5 iproute2 systemd curl jq || true
fi

# 2. Check and Download Missing Core Binaries (sslocal & tun2socks)
echo -e "${CYAN}[2/6] Verifying core binaries (sslocal & tun2socks)...${RESET}"

mkdir -p /usr/local/bin

if ! command -v sslocal >/dev/null 2>&1; then
  echo -e "${YELLOW}[+] Fetching prebuilt shadowsocks-rust (sslocal)...${RESET}"
  SS_URL="https://github.com/shadowsocks/shadowsocks-rust/releases/download/v1.25.0/shadowsocks-v1.25.0.${SS_ARCH}.tar.xz"
  TMP_SS="$(mktemp -d)"
  curl -sSL "$SS_URL" | tar -xJ -C "$TMP_SS"
  cp "$TMP_SS/sslocal" /usr/local/bin/sslocal
  chmod +x /usr/local/bin/sslocal
  rm -rf "$TMP_SS"
  echo -e "${GREEN}[✓] sslocal installed to /usr/local/bin/sslocal${RESET}"
else
  echo -e "${GREEN}[✓] sslocal is available at $(command -v sslocal)${RESET}"
fi

if ! command -v tun2socks >/dev/null 2>&1; then
  echo -e "${YELLOW}[+] Fetching prebuilt tun2socks...${RESET}"
  TUN_URL="https://github.com/xjasonlyu/tun2socks/releases/download/v2.5.2/tun2socks-linux-${BIN_ARCH}.zip"
  TMP_TUN="$(mktemp -d)"
  curl -sSL "$TUN_URL" -o "$TMP_TUN/tun2socks.zip"
  if command -v unzip >/dev/null 2>&1; then
    unzip -q "$TMP_TUN/tun2socks.zip" -d "$TMP_TUN"
  else
    python3 -c "import zipfile; zipfile.ZipFile('$TMP_TUN/tun2socks.zip').extractall('$TMP_TUN')"
  fi
  cp "$TMP_TUN"/tun2socks* /usr/local/bin/tun2socks
  chmod +x /usr/local/bin/tun2socks
  rm -rf "$TMP_TUN"
  echo -e "${GREEN}[✓] tun2socks installed to /usr/local/bin/tun2socks${RESET}"
else
  echo -e "${GREEN}[✓] tun2socks is available at $(command -v tun2socks)${RESET}"
fi

# 3. Deploy Application Files to /opt/shadowtun
echo -e "${CYAN}[3/6] Deploying application files to $TARGET_DIR...${RESET}"
mkdir -p "$TARGET_DIR"
cp -r "$SCRIPT_DIR/core" "$TARGET_DIR/"
cp -r "$SCRIPT_DIR/gui" "$TARGET_DIR/"
cp -r "$SCRIPT_DIR/cli" "$TARGET_DIR/"
cp -r "$SCRIPT_DIR/bin" "$TARGET_DIR/"

chmod +x "$TARGET_DIR/bin/shadowtun"
chmod +x "$TARGET_DIR/bin/vpn-core-helper"
chmod +x "$TARGET_DIR/cli/main.py"
chmod +x "$TARGET_DIR/gui/app.py"

# Symlink CLI / GUI launcher and helper
ln -sf "$TARGET_DIR/bin/shadowtun" "$BIN_LINK"
ln -sf "$TARGET_DIR/bin/shadowtun" "/usr/local/bin/shadowtun-vpn"
ln -sf "$TARGET_DIR/bin/vpn-core-helper" "$HELPER_LINK"

# 4. Configure One-Time Sudoers Permissions (No more passwords on connect)
echo -e "${CYAN}[4/6] Configuring one-time sudoers permissions...${RESET}"
SSLOCAL_PATH="$(command -v sslocal || echo /usr/local/bin/sslocal)"
TUN2SOCKS_PATH="$(command -v tun2socks || echo /usr/local/bin/tun2socks)"
IP_PATH="$(command -v ip || echo /usr/bin/ip)"
RESOLVECTL_PATH="$(command -v resolvectl || echo /usr/bin/resolvectl)"
PKILL_PATH="$(command -v pkill || echo /usr/bin/pkill)"
KILL_PATH="$(command -v kill || echo /usr/bin/kill)"

cat <<EOF > "$SUDOERS_FILE"
# ShadowTun VPN Privileged Helper Rule
# Allows non-root users to manage TUN device, routes, and VPN daemon seamlessly.
ALL ALL=(ALL) NOPASSWD: $HELPER_LINK, $TUN2SOCKS_PATH, $IP_PATH, $RESOLVECTL_PATH, $PKILL_PATH, $KILL_PATH
EOF

chmod 0440 "$SUDOERS_FILE"
echo -e "${GREEN}[✓] Sudoers rule installed at $SUDOERS_FILE${RESET}"

# 5. Install Desktop Entry and Icons
echo -e "${CYAN}[5/6] Installing desktop shortcut and icons...${RESET}"
mkdir -p /usr/share/applications
mkdir -p /usr/share/icons/hicolor/scalable/apps
mkdir -p /usr/share/icons/hicolor/256x256/apps

cp "$TARGET_DIR/gui/assets/icon.svg" /usr/share/icons/hicolor/scalable/apps/shadowtun.svg 2>/dev/null || true
cp "$TARGET_DIR/gui/assets/icon.png" /usr/share/icons/hicolor/256x256/apps/shadowtun.png 2>/dev/null || true
cp "$SCRIPT_DIR/packaging/shadowtun.desktop" /usr/share/applications/shadowtun.desktop

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
fi

# 6. Verification
echo -e "${CYAN}[6/6] Finalizing setup...${RESET}"
echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}  ✓ ShadowTun VPN has been installed successfully!          ${RESET}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════${RESET}"
echo ""
echo -e "You can now run ShadowTun VPN in either mode:"
echo -e "  • ${CYAN}${BOLD}shadowtun gui${RESET}        Launch Modern Desktop GUI"
echo -e "  • ${CYAN}${BOLD}shadowtun connect <key>${RESET} Direct connect via CLI"
echo -e "  • ${CYAN}${BOLD}shadowtun import <key>${RESET}  Import ssconf:// key"
echo -e "  • ${CYAN}${BOLD}shadowtun status${RESET}       View live connection status"
echo ""
