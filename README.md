# AuraLink VPN (AuraLink Linux)

> **Universal Shadowsocks & tun2socks VPN Client for Linux (Arch, Debian, Ubuntu, Fedora, RPM, openSUSE)**

AuraLink VPN is a high-performance, full-system VPN client designed specifically for Linux. It turns Shadowsocks proxy subscriptions into a complete TUN-based virtual private network, routing all TCP/UDP traffic and DNS queries securely while bypassing deep packet inspection (DPI).

---

## Key Features

- **`ssconf://` Direct Key Parser**: Automatically fetches and decodes subscription keys (e.g., `ssconf://...../...json#ProfileName`), validates server error responses (such as package expiration notices), and injects local proxy ports.
- **Cross-Distribution Support**: Runs natively on **Arch Linux / Manjaro / CachyOS**, **Debian / Ubuntu / Mint**, **Fedora / RHEL / CentOS**, and **openSUSE**.
- **Full Tunnel Routing (`tun2socks`)**: Routes all system traffic through a `tun0` virtual network adapter with automatic default gateway preservation.
- **Anti-Censorship & Prefix Support**: Full support for Shadowsocks-rust packet prefixes (TLS disguise), AEAD ciphers (`chacha20-ietf-poly1305`, `aes-256-gcm`), and UDP relay.
- **One-Time Password Setup**: Automatically configures a privileged helper rule in `/etc/sudoers.d/auralink` so you never have to type your sudo password every time you connect.
- **Modern Dark-Mode GUI (PyQt5)**:
  - Glowing circular animated connect button
  - Live upload/download speed counters & session data meter
  - Server latency / ping testing
  - Instant clipboard paste auto-detection
  - DNS selection (Cloudflare 1.1.1.1, Google 8.8.8.8, Quad9, AdGuard)
  - Real-time debug log console
  - System Tray integration (minimize-to-tray & quick connect)
- **Web Application & Interactive Documentation Portal (`frontend/`)**:
  - Built with Next.js 16 (App Router), Framer Motion, and Tailwind CSS v4.
  - Interactive VPN simulator, kernel pipeline visualizer, and live CLI playground.
  - Ready for 1-click zero-config hosting on Vercel:
    
    [![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Script-By-Lin/Arch_VPN&root-directory=frontend)

---

## 🚀 Quick 1-Command Installation (Direct `curl`)

Install directly on any Linux distribution (Arch Linux, CachyOS, Manjaro, Debian, Ubuntu, Linux Mint, Fedora, openSUSE) with a single command:

```bash
curl -fsSL https://raw.githubusercontent.com/Script-By-Lin/Arch_VPN/main/install.sh | sudo bash
```

Or install from a local clone:

```bash
git clone https://github.com/Script-By-Lin/Arch_VPN.git
cd Arch_VPN
sudo ./install.sh
```

---

## 🖥️ Usage

### 1. Launching Desktop GUI

```bash
auralink gui
# or launch "AuraLink VPN" from your Application Menu / App Launcher
```

### 2. Command-Line Interface (CLI)

#### Import a Subscription Key

```bash
auralink import "ssconf://....#....#1"
```

#### Connect / Switch VPN Server

```bash
# Connect to the selected/active profile
auralink connect

# Switch / connect directly by Profile ID (full ID or prefix)
auralink connect a1b2c3d4
auralink switch a1b2c3d4

# Switch by Profile Name
auralink switch "Tokyo-Fast-01"

# Connect directly with a key URL
auralink connect "ssconf://...."

# Connect and stream live traffic statistics
auralink connect -m
```

#### Check Status

```bash
auralink status
```

#### List & Test Profiles

```bash
auralink list
auralink test
```

#### Disconnect

```bash
auralink disconnect
```

#### View Real-Time Logs

```bash
# View recent logs (default 40 lines)
auralink logs

# Follow log output in real-time
auralink logs -f

# Follow log output with customized initial line count
auralink logs -f -n 100
```

---

## 🛠️ Standalone Shell Script (`tun2-stock.sh`)

If you prefer a single standalone script without GUI dependencies:

```bash
# Start VPN with key
./tun2-stock.sh start "ssconf://....#...."

# Stop VPN
./tun2-stock.sh stop

# Status
./tun2-stock.sh status
```

---

## 📦 Packaging

- **Arch Linux / AUR**: `makepkg -si` using `packaging/PKGBUILD`
- **Debian / Ubuntu**: Run `./packaging/build-deb.sh` to generate `.deb`
- **Fedora / RPM**: Run `./packaging/build-rpm.sh` to generate `.rpm`

---

## 🗑️ Uninstallation

To cleanly remove all application files, binaries, desktop shortcuts, and sudoers rules:

```bash
# Via 1-line curl:
curl -fsSL https://raw.githubusercontent.com/Script-By-Lin/Arch_VPN/main/uninstall.sh | sudo bash

# Or from local clone:
sudo ./uninstall.sh
```
