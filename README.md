# ShadowTun Linux VPN

> **Universal Shadowsocks & tun2socks VPN Client for Linux (Arch, Debian, Ubuntu, Fedora, RPM, openSUSE)**

ShadowTun is a high-performance, full-system VPN client designed specifically for Linux. It turns Shadowsocks proxy subscriptions into a complete TUN-based virtual private network, routing all TCP/UDP traffic and DNS queries securely while bypassing deep packet inspection (DPI).

---

## Key Features

- **`ssconf://` Direct Key Parser**: Automatically fetches and decodes subscription keys (e.g., `ssconf://example.com/config.json#ServerName`), validates server error responses (such as package expiration notices), and injects local proxy ports.
- **Cross-Distribution Support**: Runs natively on **Arch Linux / Manjaro / CachyOS**, **Debian / Ubuntu / Mint**, **Fedora / RHEL / CentOS**, and **openSUSE**.
- **Full Tunnel Routing (`tun2socks`)**: Routes all system traffic through a `tun0` virtual network adapter with automatic default gateway preservation.
- **Anti-Censorship & Prefix Support**: Full support for Shadowsocks-rust packet prefixes (TLS disguise), AEAD ciphers (`chacha20-ietf-poly1305`, `aes-256-gcm`), and UDP relay.
- **One-Time Password Setup**: Automatically configures a privileged helper rule in `/etc/sudoers.d/shadowtun` so you never have to type your sudo password every time you connect.
- **Modern Dark-Mode GUI (PyQt5)**:
  - Glowing circular animated connect button
  - Live upload/download speed counters & session data meter
  - Server latency / ping testing
  - Instant clipboard paste auto-detection
  - DNS selection (Cloudflare 1.1.1.1, Google 8.8.8.8, Quad9, AdGuard)
  - Real-time debug log console
  - System Tray integration (minimize-to-tray & quick connect)
- **Rich Command-Line Interface (CLI)**: Full headless automation support with `connect`, `disconnect`, `status`, `import`, `list`, and `test` commands.

---

## 🚀 Quick 1-Command Installation

Run the universal installer (automatically installs dependencies, core binaries, desktop launcher, and sudoers rule):

```bash
chmod +x install.sh
sudo ./install.sh
```

---

## 🖥️ Usage

### 1. Launching Desktop GUI

```bash
shadowtun-vpn gui
# or launch "ShadowTun VPN" from your Application Menu / App Launcher
```

### 2. Command-Line Interface (CLI)

#### Import a Subscription Key

```bash
shadowtun-vpn import "ssconf://example.com/config.json#ServerName"
```

#### Connect to VPN

```bash
# Connect using the imported key or active profile
shadowtun-vpn connect

# Or connect directly with a key URL
shadowtun-vpn connect "ssconf://example.com/config.json#ServerName"

# Connect and stream live traffic statistics
shadowtun-vpn connect -m
```

#### Check Status

```bash
shadowtun-vpn status
```

#### List & Test Profiles

```bash
shadowtun-vpn list
shadowtun-vpn test
```

#### Disconnect

```bash
shadowtun-vpn disconnect
```

#### View Real-Time Logs

```bash
shadowtun-vpn logs
```

---

## 🛠️ Standalone Shell Script (`tun2-stock.sh`)

If you prefer a single standalone script without GUI dependencies:

```bash
# Start VPN with key
./tun2-stock.sh start "ssconf://example.com/config.json#ServerName"

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

To cleanly remove all application files, links, and sudoers rules:

```bash
sudo ./uninstall.sh
```
