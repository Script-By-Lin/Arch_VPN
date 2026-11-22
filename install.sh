#!/usr/bin/env bash
# ==============================================================================
# AuraLink VPN - Universal Linux Installer
# Supports: Arch Linux, Manjaro, CachyOS, EndeavourOS, Debian, Ubuntu,
#           Linux Mint, Pop!_OS, Fedora, RHEL, Rocky, Alma, CentOS,
#           openSUSE (Leap/Tumbleweed), Alpine Linux (musl), Void Linux, etc.
# Configures dependencies, static binary fallbacks, desktop launcher,
# and validated one-time sudoers permissions.
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
export PATH="/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin:$PATH"
TMP_DIR=""
SRC_DIR=""

cleanup() {
  if [[ "$CLEANUP_TMP" == true && -n "$TMP_DIR" && -d "$TMP_DIR" ]]; then
    rm -rf "$TMP_DIR"
  fi
}
trap cleanup EXIT

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
  curl -fsSL "$ARCHIVE_URL" | tar -xz -C "$TMP_DIR"
  SRC_DIR="$(find "$TMP_DIR" -maxdepth 2 -type d -name "*Arch_VPN*" | head -n 1)"
  if [[ -z "$SRC_DIR" || ! -d "$SRC_DIR/core" ]]; then
    echo -e "${RED}[✗] Failed to download or unpack repository archive.${RESET}"
    exit 1
  fi
fi

# Detect Architecture & C Library (glibc vs musl for Alpine/Void-musl)
ARCH="$(uname -m)"
LIBC_SUFFIX="gnu"
if ldd --version 2>&1 | grep -qi "musl"; then
  LIBC_SUFFIX="musl"
elif [[ -f /etc/alpine-release ]]; then
  LIBC_SUFFIX="musl"
fi

case "$ARCH" in
  x86_64|amd64)
    BIN_ARCH="amd64"
    SS_ARCH="x86_64-unknown-linux-${LIBC_SUFFIX}"
    ;;
  aarch64|arm64)
    BIN_ARCH="arm64"
    SS_ARCH="aarch64-unknown-linux-${LIBC_SUFFIX}"
    ;;
  *)
    echo -e "${RED}[✗] Unsupported architecture: $ARCH${RESET}"
    exit 1
    ;;
esac

echo -e "${CYAN}[i] System: $(uname -s) ${ARCH} (${LIBC_SUFFIX})${RESET}"

# 1. Detect Package Manager and Install Dependencies
echo -e "${CYAN}[1/6] Verifying system dependencies...${RESET}"

HAS_PY3=false
HAS_IP=false
HAS_CURL=false
HAS_JQ=false
HAS_TAR=false
HAS_XZ=false
HAS_UNZIP=false
HAS_PROCPS=false
HAS_PYQT5=false
HAS_RESOLVER=false

command -v python3 >/dev/null 2>&1 && HAS_PY3=true
command -v ip >/dev/null 2>&1 && HAS_IP=true
command -v curl >/dev/null 2>&1 && HAS_CURL=true
command -v jq >/dev/null 2>&1 && HAS_JQ=true
command -v tar >/dev/null 2>&1 && HAS_TAR=true
command -v xz >/dev/null 2>&1 && HAS_XZ=true
command -v unzip >/dev/null 2>&1 && HAS_UNZIP=true
(command -v pkill >/dev/null 2>&1 || command -v ps >/dev/null 2>&1) && HAS_PROCPS=true
(command -v resolvectl >/dev/null 2>&1 || command -v resolvconf >/dev/null 2>&1) && HAS_RESOLVER=true

if python3 -c "from PyQt5 import QtCore, QtWidgets" >/dev/null 2>&1; then
  HAS_PYQT5=true
fi

ALL_DEPS_MET=false
if $HAS_PY3 && $HAS_IP && $HAS_CURL && $HAS_JQ && $HAS_TAR && $HAS_XZ && $HAS_UNZIP && $HAS_PROCPS && $HAS_PYQT5; then
  ALL_DEPS_MET=true
fi

if [[ "$ALL_DEPS_MET" == true ]]; then
  echo -e "${GREEN}[✓] All core dependencies and PyQt5 are already installed. Skipping package manager.${RESET}"
else
  if command -v pacman >/dev/null 2>&1; then
    echo "Detected Arch Linux / Pacman"
    PAC_PKGS=()
    $HAS_PY3 || PAC_PKGS+=("python")
    $HAS_IP || PAC_PKGS+=("iproute2")
    $HAS_CURL || PAC_PKGS+=("curl")
    $HAS_JQ || PAC_PKGS+=("jq")
    $HAS_TAR || PAC_PKGS+=("tar")
    $HAS_XZ || PAC_PKGS+=("xz")
    $HAS_UNZIP || PAC_PKGS+=("unzip")
    $HAS_PYQT5 || PAC_PKGS+=("python-pyqt5")
    if [[ ${#PAC_PKGS[@]} -gt 0 ]]; then
      pacman -Sy --noconfirm --needed "${PAC_PKGS[@]}" || true
    fi
    pacman -S --noconfirm --needed shadowsocks-rust 2>/dev/null || true
    if ! $HAS_RESOLVER; then
      pacman -S --noconfirm --needed systemd-resolvconf 2>/dev/null || true
    fi

  elif command -v apt-get >/dev/null 2>&1; then
    echo "Detected Debian / Ubuntu / Mint (APT)"
    export DEBIAN_FRONTEND=noninteractive
    APT_PKGS=()
    $HAS_PY3 || APT_PKGS+=("python3")
    $HAS_IP || APT_PKGS+=("iproute2")
    $HAS_CURL || APT_PKGS+=("curl")
    $HAS_JQ || APT_PKGS+=("jq")
    $HAS_TAR || APT_PKGS+=("tar")
    $HAS_XZ || APT_PKGS+=("xz-utils")
    $HAS_UNZIP || APT_PKGS+=("unzip")
    $HAS_PROCPS || APT_PKGS+=("procps")
    $HAS_PYQT5 || APT_PKGS+=("python3-pyqt5")
    if [[ ${#APT_PKGS[@]} -gt 0 ]]; then
      apt-get update -y || true
      apt-get install -y --no-install-recommends ca-certificates "${APT_PKGS[@]}" || true
    fi
    if ! $HAS_RESOLVER; then
      apt-get install -y systemd-resolved 2>/dev/null || apt-get install -y openresolv 2>/dev/null || true
    fi

  elif command -v dnf >/dev/null 2>&1; then
    echo "Detected Fedora / RHEL / Rocky / Alma (DNF)"
    DNF_PKGS=()
    $HAS_PY3 || DNF_PKGS+=("python3")
    $HAS_IP || DNF_PKGS+=("iproute")
    $HAS_CURL || DNF_PKGS+=("curl")
    $HAS_JQ || DNF_PKGS+=("jq")
    $HAS_TAR || DNF_PKGS+=("tar")
    $HAS_XZ || DNF_PKGS+=("xz")
    $HAS_UNZIP || DNF_PKGS+=("unzip")
    $HAS_PROCPS || DNF_PKGS+=("procps-ng")
    $HAS_PYQT5 || DNF_PKGS+=("python3-qt5")
    if ! $HAS_RESOLVER; then
      DNF_PKGS+=("systemd-resolved")
    fi

    if [[ ${#DNF_PKGS[@]} -gt 0 ]]; then
      echo -e "${CYAN}[*] Installing missing dependencies: ${DNF_PKGS[*]}...${RESET}"
      # Try with --refresh=never first to avoid hanging on slow/dead third-party repos (ChatGPT, Cursor, etc.)
      if ! dnf install -y --refresh=never ca-certificates "${DNF_PKGS[@]}" 2>/dev/null; then
        dnf install -y --setopt=timeout=15 ca-certificates "${DNF_PKGS[@]}" || true
      fi
    fi

  elif command -v yum >/dev/null 2>&1; then
    echo "Detected Legacy RHEL / CentOS (YUM)"
    YUM_PKGS=()
    $HAS_PY3 || YUM_PKGS+=("python3")
    $HAS_IP || YUM_PKGS+=("iproute")
    $HAS_CURL || YUM_PKGS+=("curl")
    $HAS_JQ || YUM_PKGS+=("jq")
    $HAS_TAR || YUM_PKGS+=("tar")
    $HAS_XZ || YUM_PKGS+=("xz")
    $HAS_UNZIP || YUM_PKGS+=("unzip")
    $HAS_PROCPS || YUM_PKGS+=("procps-ng")
    $HAS_PYQT5 || YUM_PKGS+=("python3-qt5")
    if [[ ${#YUM_PKGS[@]} -gt 0 ]]; then
      yum install -y ca-certificates "${YUM_PKGS[@]}" || true
    fi

  elif command -v zypper >/dev/null 2>&1; then
    echo "Detected openSUSE (Zypper)"
    ZYP_PKGS=()
    $HAS_PY3 || ZYP_PKGS+=("python3")
    $HAS_IP || ZYP_PKGS+=("iproute2")
    $HAS_CURL || ZYP_PKGS+=("curl")
    $HAS_JQ || ZYP_PKGS+=("jq")
    $HAS_TAR || ZYP_PKGS+=("tar")
    $HAS_XZ || ZYP_PKGS+=("xz")
    $HAS_UNZIP || ZYP_PKGS+=("unzip")
    $HAS_PROCPS || ZYP_PKGS+=("procps")
    $HAS_PYQT5 || ZYP_PKGS+=("python3-qt5")
    if [[ ${#ZYP_PKGS[@]} -gt 0 ]]; then
      zypper --non-interactive install --no-recommends ca-certificates "${ZYP_PKGS[@]}" || true
    fi

  elif command -v apk >/dev/null 2>&1; then
    echo "Detected Alpine Linux (APK / musl)"
    APK_PKGS=()
    $HAS_PY3 || APK_PKGS+=("python3")
    $HAS_IP || APK_PKGS+=("iproute2")
    $HAS_CURL || APK_PKGS+=("curl")
    $HAS_JQ || APK_PKGS+=("jq")
    $HAS_TAR || APK_PKGS+=("tar")
    $HAS_XZ || APK_PKGS+=("xz")
    $HAS_UNZIP || APK_PKGS+=("unzip")
    $HAS_PROCPS || APK_PKGS+=("procps")
    $HAS_PYQT5 || APK_PKGS+=("py3-qt5")
    $HAS_RESOLVER || APK_PKGS+=("openresolv")
    if [[ ${#APK_PKGS[@]} -gt 0 ]]; then
      apk add --no-cache bash sudo ca-certificates "${APK_PKGS[@]}" || true
    fi

  elif command -v xbps-install >/dev/null 2>&1; then
    echo "Detected Void Linux (XBPS)"
    XBPS_PKGS=()
    $HAS_PY3 || XBPS_PKGS+=("python3")
    $HAS_IP || XBPS_PKGS+=("iproute2")
    $HAS_CURL || XBPS_PKGS+=("curl")
    $HAS_JQ || XBPS_PKGS+=("jq")
    $HAS_TAR || XBPS_PKGS+=("tar")
    $HAS_XZ || XBPS_PKGS+=("xz")
    $HAS_UNZIP || XBPS_PKGS+=("unzip")
    $HAS_PROCPS || XBPS_PKGS+=("procps-ng")
    $HAS_PYQT5 || XBPS_PKGS+=("python3-PyQt5")
    $HAS_RESOLVER || XBPS_PKGS+=("openresolv")
    if [[ ${#XBPS_PKGS[@]} -gt 0 ]]; then
      xbps-install -Sy ca-certificates "${XBPS_PKGS[@]}" || true
    fi

  else
    echo -e "${YELLOW}[!] Unrecognized package manager. Continuing with generic Linux installation...${RESET}"
  fi
fi

# Verify Python 3 availability
if ! command -v python3 >/dev/null 2>&1; then
  echo -e "${RED}[✗] python3 is required but could not be installed automatically.${RESET}"
  exit 1
fi

# Verify Python PyQt5 availability; attempt pip install fallback if system package was missed
if ! python3 -c "from PyQt5 import QtCore, QtWidgets" >/dev/null 2>&1; then
  echo -e "${YELLOW}[*] PyQt5 not found via system packages; trying pip fallback...${RESET}"
  if command -v pip3 >/dev/null 2>&1; then
    pip3 install --break-system-packages PyQt5 2>/dev/null || pip3 install PyQt5 2>/dev/null || true
  elif python3 -m pip --version >/dev/null 2>&1; then
    python3 -m pip install --break-system-packages PyQt5 2>/dev/null || python3 -m pip install PyQt5 2>/dev/null || true
  fi
fi

if python3 -c "from PyQt5 import QtCore, QtWidgets" >/dev/null 2>&1; then
  echo -e "${GREEN}[✓] PyQt5 GUI runtime is available and verified.${RESET}"
else
  echo -e "${YELLOW}[!] Warning: PyQt5 is not installed. GUI mode requires PyQt5; CLI mode works 100%.${RESET}"
fi

# 2. Check and Download Missing Core Binaries (sslocal & tun2socks)
echo -e "${CYAN}[2/6] Verifying core binaries (sslocal & tun2socks)...${RESET}"

mkdir -p /usr/local/bin

find_existing_bin() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    command -v "$name"
    return 0
  fi
  for p in "/usr/local/bin/$name" "/usr/bin/$name" "/bin/$name"; do
    if [[ -x "$p" ]]; then
      echo "$p"
      return 0
    fi
  done
  TARGET_USER="${SUDO_USER:-$(logname 2>/dev/null || echo '')}"
  if [[ -n "$TARGET_USER" ]]; then
    local user_cargo="/home/$TARGET_USER/.cargo/bin/$name"
    if [[ -x "$user_cargo" ]]; then
      echo "$user_cargo"
      return 0
    fi
  fi
  return 1
}

EXISTING_SS="$(find_existing_bin sslocal || true)"
if [[ -n "$EXISTING_SS" ]]; then
  if [[ "$EXISTING_SS" != "/usr/local/bin/sslocal" && ! -e "/usr/local/bin/sslocal" ]]; then
    cp "$EXISTING_SS" /usr/local/bin/sslocal
    chmod 0755 /usr/local/bin/sslocal
  fi
  echo -e "${GREEN}[✓] sslocal is available at ${EXISTING_SS}${RESET}"
else
  echo -e "${YELLOW}[+] Fetching prebuilt shadowsocks-rust (${SS_ARCH})...${RESET}"
  SS_URL="https://github.com/shadowsocks/shadowsocks-rust/releases/download/v1.25.0/shadowsocks-v1.25.0.${SS_ARCH}.tar.xz"
  TMP_SS="$(mktemp -d)"
  SS_ARCHIVE="$TMP_SS/shadowsocks.tar.xz"
  if curl -fsSL --connect-timeout 15 --max-time 120 "$SS_URL" -o "$SS_ARCHIVE"; then
    if command -v xz >/dev/null 2>&1; then
      tar -xJf "$SS_ARCHIVE" -C "$TMP_SS"
    else
      python3 -c "import tarfile; tarfile.open('$SS_ARCHIVE', 'r:xz').extractall('$TMP_SS')"
    fi
    SS_FOUND="$(find "$TMP_SS" -type f -name "sslocal" | head -n 1)"
    if [[ -n "$SS_FOUND" && -f "$SS_FOUND" ]]; then
      cp "$SS_FOUND" /usr/local/bin/sslocal
      chmod 0755 /usr/local/bin/sslocal
      echo -e "${GREEN}[✓] sslocal installed to /usr/local/bin/sslocal${RESET}"
    else
      echo -e "${RED}[✗] Failed to extract sslocal binary.${RESET}"
      rm -rf "$TMP_SS"
      exit 1
    fi
  else
    echo -e "${RED}[✗] Failed to download shadowsocks-rust archive.${RESET}"
    rm -rf "$TMP_SS"
    exit 1
  fi
  rm -rf "$TMP_SS"
fi

EXISTING_TUN="$(find_existing_bin tun2socks || true)"
if [[ -n "$EXISTING_TUN" ]]; then
  if [[ "$EXISTING_TUN" != "/usr/local/bin/tun2socks" && ! -e "/usr/local/bin/tun2socks" ]]; then
    cp "$EXISTING_TUN" /usr/local/bin/tun2socks
    chmod 0755 /usr/local/bin/tun2socks
  fi
  echo -e "${GREEN}[✓] tun2socks is available at ${EXISTING_TUN}${RESET}"
else
  echo -e "${YELLOW}[+] Fetching prebuilt tun2socks (linux-${BIN_ARCH})...${RESET}"
  TUN_URL="https://github.com/xjasonlyu/tun2socks/releases/download/v2.5.2/tun2socks-linux-${BIN_ARCH}.zip"
  TMP_TUN="$(mktemp -d)"
  ZIP_PATH="$TMP_TUN/tun2socks.zip"
  if curl -fsSL --connect-timeout 15 --max-time 120 "$TUN_URL" -o "$ZIP_PATH"; then
    if command -v unzip >/dev/null 2>&1; then
      unzip -q "$ZIP_PATH" -d "$TMP_TUN"
    else
      python3 -c "import zipfile; zipfile.ZipFile('$ZIP_PATH').extractall('$TMP_TUN')"
    fi
    rm -f "$ZIP_PATH"
    BIN_FOUND="$(find "$TMP_TUN" -type f -name "tun2socks*" | head -n 1)"
    if [[ -n "$BIN_FOUND" && -f "$BIN_FOUND" ]]; then
      cp "$BIN_FOUND" /usr/local/bin/tun2socks
      chmod 0755 /usr/local/bin/tun2socks
      echo -e "${GREEN}[✓] tun2socks installed to /usr/local/bin/tun2socks${RESET}"
    else
      echo -e "${RED}[✗] Failed to extract tun2socks binary.${RESET}"
      rm -rf "$TMP_TUN"
      exit 1
    fi
  else
    echo -e "${RED}[✗] Failed to download tun2socks archive.${RESET}"
    rm -rf "$TMP_TUN"
    exit 1
  fi
  rm -rf "$TMP_TUN"
fi

# 3. Deploy Application Files to /opt/auralink
echo -e "${CYAN}[3/6] Deploying application files to $TARGET_DIR...${RESET}"
mkdir -p "$TARGET_DIR"
rm -rf "$TARGET_DIR/core" "$TARGET_DIR/gui" "$TARGET_DIR/cli" "$TARGET_DIR/bin"
cp -r "$SRC_DIR/core" "$TARGET_DIR/"
cp -r "$SRC_DIR/gui" "$TARGET_DIR/"
cp -r "$SRC_DIR/cli" "$TARGET_DIR/"
cp -r "$SRC_DIR/bin" "$TARGET_DIR/"
if [[ -f "$SRC_DIR/uninstall.sh" ]]; then
  cp "$SRC_DIR/uninstall.sh" "$TARGET_DIR/uninstall.sh"
  chmod 0755 "$TARGET_DIR/uninstall.sh"
fi

chmod 0755 "$TARGET_DIR/bin/auralink" 2>/dev/null || true
chmod 0755 "$TARGET_DIR/bin/vpn-core-helper"
chmod 0755 "$TARGET_DIR/cli/main.py"
chmod 0755 "$TARGET_DIR/gui/app.py"

# Symlink CLI / GUI launcher and helper
ln -sf "$TARGET_DIR/bin/auralink" "$BIN_LINK"
ln -sf "$TARGET_DIR/bin/auralink" "/usr/local/bin/auralink-vpn"
ln -sf "$TARGET_DIR/bin/vpn-core-helper" "$HELPER_LINK"

# 4. Configure Validated One-Time Sudoers Permissions (No more passwords on connect)
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
SYSCTL_PATH="$(get_bin_path sysctl /usr/sbin/sysctl)"
RESOLVECTL_PATH="$(get_bin_path resolvectl /usr/bin/resolvectl)"
SYSTEMD_RESOLVE_PATH="$(get_bin_path systemd-resolve /usr/bin/systemd-resolve)"
RESOLVCONF_PATH="$(get_bin_path resolvconf /usr/sbin/resolvconf)"
PKILL_PATH="$(get_bin_path pkill /usr/bin/pkill)"
KILL_PATH="$(get_bin_path kill /usr/bin/kill)"

ALLOWED_BINS=(
  "$HELPER_LINK"
  "$TUN2SOCKS_PATH" "/usr/local/bin/tun2socks" "/usr/bin/tun2socks"
  "$IP_PATH" "/usr/sbin/ip" "/usr/bin/ip" "/sbin/ip" "/bin/ip"
  "$SYSCTL_PATH" "/usr/sbin/sysctl" "/usr/bin/sysctl" "/sbin/sysctl"
  "$RESOLVECTL_PATH" "/usr/bin/resolvectl"
  "$SYSTEMD_RESOLVE_PATH" "/usr/bin/systemd-resolve"
  "$RESOLVCONF_PATH" "/usr/sbin/resolvconf" "/sbin/resolvconf" "/usr/bin/resolvconf"
  "$PKILL_PATH" "/usr/bin/pkill" "/bin/pkill"
  "$KILL_PATH" "/usr/bin/kill" "/bin/kill"
)

VALID_BINS=()
for b in "${ALLOWED_BINS[@]}"; do
  if [[ "$b" =~ ^/ ]] && { [[ -e "$b" ]] || [[ "$b" == "$HELPER_LINK" ]] || [[ "$b" == "$TUN2SOCKS_PATH" ]]; }; then
    if [[ ! " ${VALID_BINS[*]:-} " =~ " ${b} " ]]; then
      VALID_BINS+=("$b")
    fi
  fi
done

SUDO_CMDS="$(printf ", %s" "${VALID_BINS[@]}")"
SUDO_CMDS="${SUDO_CMDS:2}"

mkdir -p /etc/sudoers.d
TMP_SUDOERS="$(mktemp)"
cat <<EOF > "$TMP_SUDOERS"
# AuraLink VPN Privileged Helper Rule
# Allows non-root users to manage TUN device, routes, IPv6 guard, DNS, and VPN daemon seamlessly.
ALL ALL=(ALL) NOPASSWD: $SUDO_CMDS
EOF
chmod 0440 "$TMP_SUDOERS"

if command -v visudo >/dev/null 2>&1; then
  if visudo -cf "$TMP_SUDOERS" >/dev/null 2>&1; then
    mv -f "$TMP_SUDOERS" "$SUDOERS_FILE"
    chmod 0440 "$SUDOERS_FILE"
    echo -e "${GREEN}[✓] Validated sudoers rule installed at $SUDOERS_FILE${RESET}"
  else
    rm -f "$TMP_SUDOERS"
    echo -e "${YELLOW}[!] Warning: visudo validation failed; skipped installing $SUDOERS_FILE to keep sudo safe.${RESET}"
  fi
else
  mv -f "$TMP_SUDOERS" "$SUDOERS_FILE"
  chmod 0440 "$SUDOERS_FILE"
  echo -e "${GREEN}[✓] Sudoers rule installed at $SUDOERS_FILE${RESET}"
fi

# 5. Install Desktop Entry and Icons
echo -e "${CYAN}[5/6] Installing desktop shortcut and icons...${RESET}"
mkdir -p /usr/share/applications
mkdir -p /usr/share/pixmaps
mkdir -p /usr/share/icons/hicolor/scalable/apps

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
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications 2>/dev/null || true
fi

# 6. Post-Install Verification
echo -e "${CYAN}[6/6] Verifying installed components...${RESET}"
VERIFY_OK=true
for bin in auralink vpn-core-helper sslocal tun2socks ip; do
  if command -v "$bin" >/dev/null 2>&1 || [[ -x "/usr/local/bin/$bin" ]]; then
    echo -e "  ${GREEN}[OK]${RESET} $bin"
  else
    echo -e "  ${RED}[MISSING]${RESET} $bin"
    VERIFY_OK=false
  fi
done

if [[ ! -c /dev/net/tun ]]; then
  echo -e "  ${YELLOW}[WARN]${RESET} /dev/net/tun not detected yet (try: sudo modprobe tun)"
fi

echo ""
if [[ "$VERIFY_OK" == true ]]; then
  echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════${RESET}"
  echo -e "${GREEN}${BOLD}  ✓ AuraLink VPN has been installed successfully!           ${RESET}"
  echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════${RESET}"
else
  echo -e "${YELLOW}${BOLD}════════════════════════════════════════════════════════════${RESET}"
  echo -e "${YELLOW}${BOLD}  ! AuraLink VPN installed with missing dependencies above  ${RESET}"
  echo -e "${YELLOW}${BOLD}════════════════════════════════════════════════════════════${RESET}"
fi
echo ""
echo -e "You can now run AuraLink VPN in either mode:"
echo -e "  • ${CYAN}${BOLD}auralink gui${RESET}           Launch Daylight Desktop GUI"
echo -e "  • ${CYAN}${BOLD}auralink connect <key>${RESET} Direct connect via CLI"
echo -e "  • ${CYAN}${BOLD}auralink import <key>${RESET}  Import ssconf:// key"
echo -e "  • ${CYAN}${BOLD}auralink status${RESET}        View live connection & IPv6 status"
echo ""
