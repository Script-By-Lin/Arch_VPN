# ShadowTun Linux — Frontend & Documentation Web App

A modern, high-performance web application and interactive documentation portal for **ShadowTun Linux**, built with **Next.js 16 (App Router)**, **Framer Motion**, **Lucide Icons**, and **Tailwind CSS v4**.

---

## 🚀 Getting Started

### Development Server

```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build & Launch

```bash
cd frontend
npm run build
npm start
```

---

## 🌟 Key Features

1. **Downlink & Quick Install Card**:
   - Matches the reference design with title and version pill badge (`v1.0.0`).
   - Distribution selector tabs: **Linux (Universal curl)**, **Arch Linux / AUR / CachyOS**, **Debian / Ubuntu / Mint**, **Fedora / RPM**, **openSUSE**, **Standalone Shell (`tun2-stock.sh`)**, and **Git Source**.
   - Shell code block with interactive copy-to-clipboard button and animated checkmark feedback.
   - Quick access to download `install.sh`, `uninstall.sh`, and `tun2-stock.sh`.

2. **About ShadowTun Section**:
   - Deep-dive into core capabilities: `ssconf://` parser, full-system TUN interface (`tun0`), `shadowsocks-rust` AEAD ciphers, TLS disguise prefixes defeating Deep Packet Inspection (DPI), zero-leak DNS sinkhole, and non-root passwordless automation.

3. **Linux Kernel Architecture Visualizer**:
   - Interactive flow diagram mapping packet traversal from User Space Apps ➔ Kernel TUN (`tun0`) ➔ tun2socks Bridge (Go) ➔ sslocal Proxy (Rust) ➔ Physical Gateway (`wlan0`/`eth0`) ➔ Encrypted Remote Server.
   - Interactive node inspector showing the exact low-level Linux commands and routing rules.

4. **Live Interactive VPN Simulator**:
   - Full browser simulation of the PyQt5 desktop client.
   - Glowing circular connect/disconnect switch with pulse waves.
   - Live download & upload speedometers with simulated kernel byte telemetry (`/proc/net/dev`).
   - Real-time latency ping tester and DNS upstream selector.
   - Real-time simulated debug log console.

5. **Comprehensive User Guide & Manual**:
   - **Quick Start Guide**: 3-step setup and uninstallation commands.
   - **Desktop GUI Walkthrough**: Complete breakdown of PyQt5 dark-mode GUI features.
   - **CLI Commands Playground**: Searchable and filterable reference for `connect`, `disconnect`, `status`, `import`, `list`, `test`, and `logs` with one-click copyable snippets and expected outputs.
   - **ssconf:// Protocol Guide**: Technical breakdown of subscription parsing and payload structure.
   - **Troubleshooting & FAQ**: Common interface, routing, and systemd-resolved DNS questions.
