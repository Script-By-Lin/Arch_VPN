# ShadowTun Linux VPN — System & Technology Architecture (`sys.md`)

This document provides a comprehensive technical overview of the technologies, libraries, protocols, kernel subsystems, and architectural design patterns implemented across the **ShadowTun Linux VPN** project.

---

## 1. High-Level System Architecture

ShadowTun transforms user-space SOCKS5 proxies (Shadowsocks) into a full-system TUN network device, capturing all operating system TCP/UDP traffic and DNS queries.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Linux User Space / Apps                         │
│             (Web Browsers, CLI Tools, Gaming, System Daemons)          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (All TCP/UDP & DNS Packets)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  Linux Kernel Network Subsystem (TUN/TAP)              │
│                        Virtual Adapter: `tun0`                         │
│                    IP Assigned: 10.0.0.2/24                            │
│           Default Route: `default dev tun0` (Hijacked)                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Layer 3 IP Packets)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     tun2socks Engine (Go / tun2socks)                  │
│       - Reads IP frames from /dev/net/tun                              │
│       - Unpacks Layer 3/4 TCP/UDP packets                              │
│       - Forwards payloads via SOCKS5 to localhost:1080                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ SOCKS5 Protocol (127.0.0.1:1080)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  Shadowsocks Core (`sslocal` / Rust)                   │
│       - Encrypts payload with AEAD Ciphers (ChaCha20-Poly1305, AES-GCM)│
│       - Adds TLS/Disguise Anti-Censorship Prefixes                     │
│       - Relays encrypted TCP/UDP packets to remote server              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Encrypted Wire Traffic)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Physical Network Interface (`wlan0` / `eth0`)        │
│          Static Pinned Route: `<server_ip>/32 via <gateway_ip>`        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Internet / WAN)
                                    ▼
                     ┌─────────────────────────────┐
                     │  Remote Shadowsocks Server  │
                     └─────────────────────────────┘
```

---

## 2. Technology Stack Breakdown

### 2.1 Core Programming Languages & Runtimes

| Technology | Purpose | Implementation Details |
| :--- | :--- | :--- |
| **Python 3** (3.8+) | Main Application Logic, Orchestration, GUI, and CLI | - Thread-safe service orchestrator (`VPNService`)<br>- Network management & route resolution<br>- Profile & configuration lifecycle<br>- Live telemetry and bandwidth calculation |
| **POSIX / Bash Shell** | Low-level privileged helper, installers, and standalone engine | - Privileged script helper (`bin/vpn-core-helper`)<br>- Universal cross-distro installer (`install.sh`)<br>- Standalone script engine (`tun2-stock.sh`)<br>- Safe uninstallation (`uninstall.sh`) |
| **Rust** | Shadowsocks Core (`sslocal`) | - High-performance memory-safe proxy core provided by `shadowsocks-rust` |
| **Go (Golang)** | Network Tunneling (`tun2socks`) | - High-throughput userspace network TUN-to-SOCKS5 bridge |

---

### 2.2 Core Tunneling & Proxy Engines

1. **`shadowsocks-rust` (`sslocal`)**:
   - Primary proxy daemon running in local client mode (`-c config.json`).
   - Handles AEAD encryption/decryption, TCP keepalive, and UDP relay.
   - Supports anti-censorship packet prefixing (TLS disguise headers) to defeat Deep Packet Inspection (DPI).

2. **`xjasonlyu/tun2socks` (v2.x)**:
   - Modern Go-based tun2socks implementation.
   - Interfaces directly with Linux TUN device (`--device tun0`) and forwards traffic to the local SOCKS5 proxy (`--proxy socks5://127.0.0.1:1080`).
   - Supports multithreaded network packet processing with low latency.

---

### 2.3 Linux Kernel & Network Routing Subsystems

| Subsystem / Utility | Implementation & Function |
| :--- | :--- |
| **Linux TUN/TAP Driver** (`/dev/net/tun`) | Creates virtual Layer-3 interface (`ip tuntap add mode tun dev tun0`) configured with private subnet (`10.0.0.2/24`). |
| **`iproute2` (`ip`)** | - **Physical Gateway Detection**: Dynamically inspects `ip -4 route show default` and `ip -4 route get 1.1.1.1` to obtain the physical gateway IP and interface (e.g. `192.168.1.1 dev wlan0`).<br>- **Route Pinning**: Pins the Shadowsocks remote server IP to the physical gateway (`ip route replace <server_ip>/32 via <gw> dev <dev>`) to prevent routing loops.<br>- **Default Gateway Hijacking**: Replaces system default route to point to the TUN device (`ip route replace default dev tun0`).<br>- **Graceful Teardown**: Restores physical default route, removes server pin, and tears down `tun0`. |
| **IPv6 Leak Protection** | Explicitly drops default IPv6 routes (`ip -6 route del default`) during connection to eliminate IPv6 DNS and data leakage. |
| **ProcFS (`/proc/net/dev`)** | Direct kernel byte counter polling for zero-overhead bandwidth tracking (live RX/TX transfer speeds and total session volume). |
| **Raw Socket Handshake (`socket`)** | Low-level TCP socket SYN/ACK handshake probing to measure millisecond server latency/ping. |

---

### 2.4 DNS Resolution & Leak Prevention

| Component | Technical Handling |
| :--- | :--- |
| **`systemd-resolved` & `resolvectl`** | - Configures per-interface DNS on `tun0` (`resolvectl dns tun0 1.1.1.1 8.8.8.8`).<br>- Injects wildcard domain routing (`resolvectl domain tun0 "~."`) to ensure **all** system DNS queries route exclusively through the VPN tunnel.<br>- Enables default DNS route flag (`resolvectl default-route tun0 yes`).<br>- Cleanly reverts settings upon disconnect (`resolvectl revert tun0`). |
| **Legacy `systemd-resolve` Fallback** | Fallback support for older distributions using `systemd-resolve -i tun0 --set-dns=... --set-domain=~.`. |
| **Supported DNS Upstreams** | Configurable via GUI/Settings: Cloudflare (`1.1.1.1`, `1.0.0.1`), Google (`8.8.8.8`, `8.8.4.4`), Quad9 (`9.9.9.9`), AdGuard (`94.140.14.14`). |

---

### 2.5 Security, Privilege Model & Elevation

- **Granular Sudoers Rule (`/etc/sudoers.d/shadowtun`)**:
  - Automatically installed during initial setup (`install.sh`).
  - Configures `NOPASSWD` elevation exclusively for required network and daemon binaries (`vpn-core-helper`, `tun2socks`, `ip`, `resolvectl`, `pkill`, `kill`).
  - Guarantees seamless one-click connect/disconnect in GUI/CLI without prompting for sudo passwords repeatedly.
- **Polkit (`pkexec`) Fallback**:
  - Automated fallback to `pkexec` when running in desktop environments where passwordless sudo is not configured.
- **Process Isolation**:
  - `sslocal` runs safely in unprivileged user space.
  - Only `tun2socks` and routing manipulation require root capabilities.

---

### 2.6 Desktop GUI Architecture (`PyQt5`)

- **Framework**: Python bindings for Qt5 (`PyQt5.QtWidgets`, `PyQt5.QtCore`, `PyQt5.QtGui`).
- **Design System & Styling**:
  - Bespoke QSS (Qt Style Sheet) engine with dark slate/zinc palette (`#111217`, `#181A22`, `#1E202B`).
  - Custom UI controls, card layouts (`QFrame.card`), hover transitions, and rounded status badges.
- **Custom Visual Components**:
  - Custom-painted animated connection indicator button (`QPainter`, `QBrush`, `QPen`).
  - High-density server cards with ping latency indicators, one-click switch buttons, and swipe-like action controls.
- **Asynchronous Event Loop & Concurrency**:
  - Qt signals/slots bridge (`BridgeSignals` using `pyqtSignal`) decoupling worker threads from GUI rendering.
  - Non-blocking server latency ping checks via background Python threads (`threading.Thread`).
  - Real-time polling timer (`QTimer`) for live upload/download speed counters and debug log streaming.
- **Desktop Environment Integration**:
  - `QSystemTrayIcon` with context menu for minimize-to-tray and background operation.
  - Freedesktop `.desktop` standard compliant (`/usr/share/applications/shadowtun.desktop`).
  - Hicolor icon theme compliant scalable SVG and PNG assets (`/usr/share/icons/hicolor/...`).

---

### 2.7 CLI & Automation Stack

- **`argparse` Subcommand Architecture**:
  - Commands: `connect`, `disconnect`, `status`, `import`, `list`, `delete`, `test`, `logs`, `gui`.
- **Interactive ANSI Stream**:
  - Terminal coloring and formatting with live in-place carriage-return update stream (`connect -m`).
- **Automation / Headless Support**:
  - Capable of running in headless Linux servers, CI/CD environments, and embedded devices without X11/Wayland display servers.

---

### 2.8 Subscription Protocols & Cryptographic Support

- **Subscription Schemes**:
  - `ssconf://`: Fetches remote JSON subscription configuration over HTTPS with custom User-Agent headers, TLS fallback, and error notice extraction.
  - `ss://`: Standard SIP002 Base64 URI decoder supporting userinfo encryption and URL anchor tags (`#ServerName`).
  - Raw Shadowsocks JSON configuration file import.
- **Ciphers & Protocols**:
  - Modern AEAD Ciphers: `chacha20-ietf-poly1305`, `aes-256-gcm`, `aes-128-gcm`, `2022-blake3-aes-256-gcm`.
  - Packet Disguise / Prefixing: TLS 1.3 Client Hello emulation prefixes for bypassing state-level firewalls.

---

### 2.9 Cross-Distribution Packaging & Deployment

| Distribution Family | Packaging Mechanism | Files & Tools |
| :--- | :--- | :--- |
| **Arch Linux / Manjaro / CachyOS** | Arch Package (`PKGBUILD`) | `makepkg -si`, `pacman` dependency resolution |
| **Debian / Ubuntu / Linux Mint** | Debian Binary Package (`.deb`) | `packaging/build-deb.sh` using `dpkg-deb` |
| **Fedora / RHEL / CentOS / Rocky** | Red Hat RPM (`.rpm`) | `packaging/build-rpm.sh` using `rpmbuild` |
| **Universal Linux** | Shell Installer & Binary Bootstrap | `install.sh` with architecture detection (`x86_64`, `aarch64`) and automated GitHub release binary fallback fetching |

---

## 3. Directory & File Organization

```
Arch_VPN/
├── bin/
│   ├── shadowtun             # Main unified CLI / GUI executable launcher
│   ├── shadowtun-vpn         # Symbolic link alias
│   └── vpn-core-helper       # Privileged network and interface helper script
├── cli/
│   ├── __init__.py           # CLI package definition
│   └── main.py               # Complete CLI command parser and runner
├── core/
│   ├── __init__.py           # Core package exports
│   ├── config_manager.py     # Subscriptions, ssconf/ss decoder, JSON profiles
│   ├── network_manager.py    # Route pinning, TUN setup, DNS, IPv6 killswitch
│   ├── process_manager.py    # sslocal & tun2socks process lifecycle & socket checks
│   ├── stats_monitor.py      # /proc/net/dev parser, speed meter, TCP ping
│   └── vpn_service.py        # Central thread-safe orchestrator & state machine
├── gui/
│   ├── __init__.py           # GUI package definition
│   ├── app.py                # PyQt5 GUI desktop application
│   ├── assets/               # SVG & PNG application icons
│   └── theme.py              # Dark QSS styles, palette tokens & typography
├── packaging/
│   ├── PKGBUILD              # Arch Linux package build recipe
│   ├── build-deb.sh          # Debian (.deb) package generator
│   ├── build-rpm.sh          # Fedora / RHEL (.rpm) package generator
│   └── shadowtun.desktop     # XDG Desktop application launcher
├── install.sh                # Universal 1-command installer script
├── uninstall.sh              # Clean uninstaller script
├── tun2-stock.sh             # Standalone monolithic shell script engine
├── README.md                 # User documentation & guide
└── sys.md                    # System & technology architecture document
```
