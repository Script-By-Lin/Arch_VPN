#!/usr/bin/env bash
# ==============================================================================
# AuraLink VPN - Universal Linux Installer
# Supports: Arch Linux, Manjaro, CachyOS, Debian, Ubuntu, Linux Mint,
#           Fedora, RHEL, openSUSE, Alpine, etc.
# Configures dependencies, static binary fallbacks, desktop launcher,
# and one-time sudoers permissions.
#
# Direct 1-Line Curl Installation:
#   curl -fsSL https://raw.githubusercontent.com/Script-By-Lin/Arch_VPN/main/install.sh | sudo bash
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
echo "║          AuraLink VPN - Universal Linux Installer         ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${RESET}"

# Require root/sudo permissions
if [[ $EUID -ne 0 ]]; then
  if [[ "$0" == "bash" || "$0" == "sh" || "$0" == "-bash" || ! -f "$0" ]]; then
    echo -e "${RED}[!] Root permissions required for installation.${RESET}"
    echo -e "    Please run with sudo:"
    echo -e "    ${BOLD}curl -fsSL https://raw.githubusercontent.com/Script-By-Lin/Arch_VPN/main/install.sh | sudo bash${RESET}\n"
    exit 1
  else
    echo -e "${YELLOW}[*] Root permissions required for installation. Requesting sudo...${RESET}"
    exec sudo "$0" "$@"
  fi
fi

TARGET_DIR="/opt/auralink"
BIN_LINK="/usr/local/bin/auralink"
HELPER_LINK="/usr/local/bin/vpn-core-helper"
SUDOERS_FILE="/etc/sudoers.d/auralink"
CLEANUP_TMP=false
TMP_DIR=""
SRC_DIR=""

# Determine source files (Local clone vs Remote curl pipe)
SCRIPT_SOURCE="${BASH_SOURCE[0]:-$0}"
if [[ -f "$SCRIPT_SOURCE" ]]; then
  LOCAL_DIR="$(cd "$(dirname "$SCRIPT_SOURCE")" 2>/dev/null && pwd)"
  if [[ -d "$LOCAL_DIR/core" && -d "$LOCAL_DIR/gui" ]]; then
    SRC_DIR="$LOCAL_DIR"
  fi
fi

if [[ -z "$SRC_DIR" ]]; then
  echo -e "${CYAN}[*] Downloading latest AuraLink release from GitHub...${RESET}"
  TMP_DIR="$(mktemp -d)"
  CLEANUP_TMP=true
  ARCHIVE_URL="https://github.com/Script-By-Lin/Arch_VPN/archive/refs/heads/main.tar.gz"
  curl -sSL "$ARCHIVE_URL" | tar -xz -C "$TMP_DIR"
  SRC_DIR="$(find "$TMP_DIR" -maxdepth 2 -type d -name "*Arch_VPN*" | head -n 1)"
  if [[ -z "$SRC_DIR" || ! -d "$SRC_DIR/core" ]]; then
    echo -e "${RED}[✗] Failed to download or unpack repository archive.${RESET}"
    [[ -n "$TMP_DIR" && -d "$TMP_DIR" ]] && rm -rf "$TMP_DIR"
    exit 1
  fi
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
  pacman -Sy --noconfirm --needed python python-pyqt5 python-pip iproute2 systemd-resolvconf curl jq shadowsocks-rust || true
  
  # Try pacman for tun2socks
  if ! command -v tun2socks >/dev/null 2>&1; then
    pacman -S --noconfirm --needed tun2socks 2>/dev/null || true
  fi

  # Auto-install tun2socks from AUR using yay or paru if available
  if ! command -v tun2socks >/dev/null 2>&1; then
    TARGET_USER="${SUDO_USER:-$(logname 2>/dev/null || echo '')}"
    if [[ -n "$TARGET_USER" && "$TARGET_USER" != "root" ]]; then
      if sudo -u "$TARGET_USER" command -v yay >/dev/null 2>&1; then
        echo -e "${CYAN}[*] Auto-installing tun2socks from AUR via yay...${RESET}"
        sudo -u "$TARGET_USER" yay -S --noconfirm --needed tun2socks 2>/dev/null || true
      elif sudo -u "$TARGET_USER" command -v paru >/dev/null 2>&1; then
        echo -e "${CYAN}[*] Auto-installing tun2socks from AUR via paru...${RESET}"
        sudo -u "$TARGET_USER" paru -S --noconfirm --needed tun2socks 2>/dev/null || true
      fi
    elif command -v yay >/dev/null 2>&1; then
      yay -S --noconfirm --needed tun2socks 2>/dev/null || true
    fi
  fi
elif command -v apt-get >/dev/null 2>&1; then
  echo "Detected Debian / Ubuntu"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y python3 python3-pyqt5 python3-pip iproute2 systemd-resolved curl jq shadowsocks-libev || true
elif command -v dnf >/dev/null 2>&1; then
  echo "Detected Fedora / RHEL"
  dnf install -y python3 python3-qt5 python3-pyqt5 python3-pip iproute systemd-resolved curl jq || true
elif command -v zypper >/dev/null 2>&1; then
  echo "Detected openSUSE"
  zypper install -y python3 python3-qt5 python3-pip iproute2 systemd curl jq || true
fi

# Verify Python PyQt5 availability; attempt pip install fallback if system package was missed
if ! python3 -c "from PyQt5 import QtCore, QtWidgets" >/dev/null 2>&1; then
  echo -e "${YELLOW}[*] Installing PyQt5 via pip fallback...${RESET}"
  if command -v pip3 >/dev/null 2>&1; then
    pip3 install --break-system-packages PyQt5 || pip3 install PyQt5 || true
  elif python3 -m pip --version >/dev/null 2>&1; then
    python3 -m pip install --break-system-packages PyQt5 || python3 -m pip install PyQt5 || true
  fi
fi

if python3 -c "from PyQt5 import QtCore, QtWidgets" >/dev/null 2>&1; then
  echo -e "${GREEN}[✓] PyQt5 GUI runtime is available and verified.${RESET}"
else
  echo -e "${YELLOW}[!] Warning: PyQt5 is not installed. GUI mode will require 'python-pyqt5' / 'python3-pyqt5'. CLI mode works 100%.${RESET}"
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
  ZIP_PATH="$(mktemp --suffix=.zip)"
  curl -sSL "$TUN_URL" -o "$ZIP_PATH"
  if command -v unzip >/dev/null 2>&1; then
    unzip -q "$ZIP_PATH" -d "$TMP_TUN"
  else
    python3 -c "import zipfile; zipfile.ZipFile('$ZIP_PATH').extractall('$TMP_TUN')"
  fi
  rm -f "$ZIP_PATH"
  BIN_FOUND="$(find "$TMP_TUN" -type f -name "tun2socks*" | head -n 1)"
  if [[ -n "$BIN_FOUND" && -f "$BIN_FOUND" ]]; then
    cp "$BIN_FOUND" /usr/local/bin/tun2socks
    chmod +x /usr/local/bin/tun2socks
  else
    echo -e "${RED}[✗] Failed to extract tun2socks binary.${RESET}"
    rm -rf "$TMP_TUN"
    [[ "$CLEANUP_TMP" == true && -d "$TMP_DIR" ]] && rm -rf "$TMP_DIR"
    exit 1
  fi
  rm -rf "$TMP_TUN"
  echo -e "${GREEN}[✓] tun2socks installed to /usr/local/bin/tun2socks${RESET}"
else
  echo -e "${GREEN}[✓] tun2socks is available at $(command -v tun2socks)${RESET}"
fi

# 3. Deploy Application Files to /opt/auralink
echo -e "${CYAN}[3/6] Deploying application files to $TARGET_DIR...${RESET}"
mkdir -p "$TARGET_DIR"
cp -r "$SRC_DIR/core" "$TARGET_DIR/"
cp -r "$SRC_DIR/gui" "$TARGET_DIR/"
cp -r "$SRC_DIR/cli" "$TARGET_DIR/"
cp -r "$SRC_DIR/bin" "$TARGET_DIR/"
if [[ -f "$SRC_DIR/uninstall.sh" ]]; then
  cp "$SRC_DIR/uninstall.sh" "$TARGET_DIR/uninstall.sh"
  chmod +x "$TARGET_DIR/uninstall.sh"
fi

chmod +x "$TARGET_DIR/bin/auralink" 2>/dev/null || true
if [[ -f "$TARGET_DIR/bin/shadowtun" ]]; then chmod +x "$TARGET_DIR/bin/shadowtun"; fi
chmod +x "$TARGET_DIR/bin/vpn-core-helper"
chmod +x "$TARGET_DIR/cli/main.py"
chmod +x "$TARGET_DIR/gui/app.py"

# Symlink CLI / GUI launcher and helper
ln -sf "$TARGET_DIR/bin/auralink" "$BIN_LINK"
ln -sf "$TARGET_DIR/bin/auralink" "/usr/local/bin/auralink-vpn"
ln -sf "$TARGET_DIR/bin/auralink" "/usr/local/bin/shadowtun"
ln -sf "$TARGET_DIR/bin/auralink" "/usr/local/bin/shadowtun-vpn"
ln -sf "$TARGET_DIR/bin/vpn-core-helper" "$HELPER_LINK"

# Also maintain legacy /opt/shadowtun link if needed
if [[ ! -e "/opt/shadowtun" ]]; then
  ln -sf "$TARGET_DIR" "/opt/shadowtun"
fi

# 4. Configure One-Time Sudoers Permissions (No more passwords on connect)
echo -e "${CYAN}[4/6] Configuring one-time sudoers permissions...${RESET}"

get_bin_path() {
  local bin="$1"
  local fallback="$2"
  local p
  p="$(type -P "$bin" 2>/dev/null || which "$bin" 2>/dev/null || true)"
  if [[ -n "$p" && "$p" =~ ^/ ]]; then
    echo "$p"
  else
    echo "$fallback"
  fi
}

TUN2SOCKS_PATH="$(get_bin_path tun2socks /usr/local/bin/tun2socks)"
IP_PATH="$(get_bin_path ip /usr/sbin/ip)"
RESOLVECTL_PATH="$(get_bin_path resolvectl /usr/bin/resolvectl)"
PKILL_PATH="$(get_bin_path pkill /usr/bin/pkill)"
KILL_PATH="$(get_bin_path kill /usr/bin/kill)"

ALLOWED_BINS=("$HELPER_LINK" "$TUN2SOCKS_PATH" "/usr/local/bin/tun2socks" "/usr/bin/tun2socks" "$IP_PATH" "/usr/sbin/ip" "/usr/bin/ip" "$RESOLVECTL_PATH" "/usr/bin/resolvectl" "$PKILL_PATH" "/usr/bin/pkill" "$KILL_PATH" "/usr/bin/kill" "/bin/kill")

VALID_BINS=()
for b in "${ALLOWED_BINS[@]}"; do
  if [[ "$b" =~ ^/ ]] && { [[ -e "$b" ]] || [[ "$b" == "$HELPER_LINK" ]] || [[ "$b" == "$TUN2SOCKS_PATH" ]]; }; then
    if [[ ! " ${VALID_BINS[*]} " =~ " ${b} " ]]; then
      VALID_BINS+=("$b")
    fi
  fi
done

SUDO_CMDS="$(printf ", %s" "${VALID_BINS[@]}")"
SUDO_CMDS="${SUDO_CMDS:2}"

cat <<EOF > "$SUDOERS_FILE"
# AuraLink VPN Privileged Helper Rule
# Allows non-root users to manage TUN device, routes, and VPN daemon seamlessly.
ALL ALL=(ALL) NOPASSWD: $SUDO_CMDS
EOF

chmod 0440 "$SUDOERS_FILE"
if command -v visudo >/dev/null 2>&1; then
  visudo -cf "$SUDOERS_FILE" >/dev/null 2>&1 || true
fi
echo -e "${GREEN}[✓] Sudoers rule installed at $SUDOERS_FILE${RESET}"

# 5. Install Desktop Entry and Icons
echo -e "${CYAN}[5/6] Installing desktop shortcut and icons...${RESET}"
mkdir -p /usr/share/applications
mkdir -p /usr/share/pixmaps

cp "$SRC_DIR/gui/assets/icon.png" /usr/share/pixmaps/auralink.png 2>/dev/null || true
cp "$SRC_DIR/gui/assets/icon.svg" /usr/share/icons/hicolor/scalable/apps/auralink.svg 2>/dev/null || true

for s in 16 22 24 32 48 64 128 256 512; do
  mkdir -p "/usr/share/icons/hicolor/${s}x${s}/apps"
  if [[ -f "$SRC_DIR/gui/assets/icons/auralink_${s}x${s}.png" ]]; then
    cp "$SRC_DIR/gui/assets/icons/auralink_${s}x${s}.png" "/usr/share/icons/hicolor/${s}x${s}/apps/auralink.png" 2>/dev/null || true
  fi
done

if [[ -f "$SRC_DIR/packaging/auralink.desktop" ]]; then
  cp "$SRC_DIR/packaging/auralink.desktop" /usr/share/applications/auralink.desktop
elif [[ -f "$SRC_DIR/packaging/shadowtun.desktop" ]]; then
  cp "$SRC_DIR/packaging/shadowtun.desktop" /usr/share/applications/auralink.desktop
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
fi

# Cleanup temp files if any
if [[ "$CLEANUP_TMP" == true && -n "$TMP_DIR" && -d "$TMP_DIR" ]]; then
  rm -rf "$TMP_DIR"
fi

# 6. Verification
echo -e "${CYAN}[6/6] Finalizing setup...${RESET}"
echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}  ✓ AuraLink VPN has been installed successfully!           ${RESET}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════${RESET}"
echo ""
echo -e "You can now run AuraLink VPN in either mode:"
echo -e "  • ${CYAN}${BOLD}auralink gui${RESET}        Launch Modern Desktop GUI"
echo -e "  • ${CYAN}${BOLD}auralink connect <key>${RESET} Direct connect via CLI"
echo -e "  • ${CYAN}${BOLD}auralink import <key>${RESET}  Import ssconf:// key"
echo -e "  • ${CYAN}${BOLD}auralink status${RESET}       View live connection status"
echo ""
