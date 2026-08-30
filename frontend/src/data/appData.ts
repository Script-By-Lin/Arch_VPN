export interface DistroInstall {
  id: string;
  name: string;
  icon: string;
  badge?: string;
  command: string;
  description: string;
  prerequisites?: string[];
  notes?: string;
}

export const DISTRO_INSTALLS: DistroInstall[] = [
  {
    id: "universal",
    name: "Linux (Universal curl)",
    icon: "🐧",
    badge: "Recommended",
    command: "curl -fsSL https://raw.githubusercontent.com/Script-By-Lin/Arch_VPN/main/install.sh | sudo bash",
    description: "One-line automated installer for all modern Linux distributions. Automatically detects your package manager, resolves dependencies, and installs ShadowTun system-wide.",
    prerequisites: ["curl", "sudo", "bash"],
    notes: "Works on Arch, Debian, Ubuntu, Fedora, CachyOS, Manjaro, Mint, openSUSE, and CentOS/RHEL."
  },
  {
    id: "arch",
    name: "Arch Linux / AUR / CachyOS",
    icon: "🏹",
    badge: "Native PKGBUILD",
    command: "git clone https://github.com/Script-By-Lin/Arch_VPN.git\ncd Arch_VPN/packaging\nmakepkg -si",
    description: "Native Arch User Repository (AUR) / Pacman package installation with integrated system dependencies and systemd integration.",
    prerequisites: ["base-devel", "git", "python-pyqt5", "shadowsocks-rust", "tun2socks"],
    notes: "Installs binary to /usr/local/bin/shadowtun with desktop entry and icon."
  },
  {
    id: "debian",
    name: "Debian / Ubuntu / Mint",
    icon: "🍥",
    badge: ".deb Package",
    command: "git clone https://github.com/Script-By-Lin/Arch_VPN.git\ncd Arch_VPN\n./packaging/build-deb.sh\nsudo dpkg -i dist/shadowtun_*.deb",
    description: "Build and install a native Debian package (.deb) with APT dependency management.",
    prerequisites: ["python3-pyqt5", "curl", "iproute2", "systemd-resolved"],
    notes: "Can also be updated directly via the universal curl script."
  },
  {
    id: "fedora",
    name: "Fedora / RHEL / RPM",
    icon: "🎩",
    badge: ".rpm Package",
    command: "git clone https://github.com/Script-By-Lin/Arch_VPN.git\ncd Arch_VPN\n./packaging/build-rpm.sh\nsudo rpm -i dist/rpmbuild/RPMS/*/*.rpm",
    description: "Build and install a native RPM package for Fedora, CentOS Stream, RHEL, and AlmaLinux.",
    prerequisites: ["python3-qt5", "rpm-build", "iproute", "systemd-resolved"],
    notes: "Integrates with DNF/RPM package database."
  },
  {
    id: "opensuse",
    name: "openSUSE (Leap / Tumbleweed)",
    icon: "🦎",
    command: "sudo zypper install python3-qt5 curl iproute2\ngit clone https://github.com/Script-By-Lin/Arch_VPN.git\ncd Arch_VPN\nsudo ./install.sh",
    description: "Native openSUSE installation via zypper dependencies and direct installer script.",
    prerequisites: ["python3-qt5", "curl", "zypper"],
    notes: "Configures systemd-resolved and tun network interfaces automatically."
  },
  {
    id: "standalone",
    name: "Standalone Shell (tun2-stock.sh)",
    icon: "📜",
    badge: "Zero GUI Deps",
    command: "# Start VPN directly with key\n./tun2-stock.sh start \"ssconf://..../...#Profile\"\n\n# Check Status\n./tun2-stock.sh status\n\n# Stop VPN\n./tun2-stock.sh stop",
    description: "Ultra-lightweight POSIX bash script requiring zero Python or GUI dependencies. Ideal for headless servers, minimal routers, and embedded Linux boxes.",
    prerequisites: ["bash", "curl", "iproute2", "shadowsocks-rust", "tun2socks"],
    notes: "Direct Layer 3 routing engine with zero desktop overhead."
  },
  {
    id: "git",
    name: "Git Source Build",
    icon: "🐙",
    command: "git clone https://github.com/Script-By-Lin/Arch_VPN.git\ncd Arch_VPN\nsudo ./install.sh",
    description: "Clone directly from GitHub and run the automated interactive setup wizard.",
    prerequisites: ["git", "sudo", "bash"],
    notes: "Ideal for testing bleeding-edge commits and development branches."
  }
];

export interface CliCommand {
  command: string;
  summary: string;
  category: "Connection" | "Subscription" | "Diagnostics" | "System";
  options?: { flag: string; description: string }[];
  example: string;
  output: string;
}

export const CLI_COMMANDS: CliCommand[] = [
  {
    command: "shadowtun connect [KEY_URL]",
    summary: "Initiate full-tunnel VPN connection",
    category: "Connection",
    options: [
      { flag: "-m, --monitor", description: "Stream real-time RX/TX network statistics directly in the terminal" },
      { flag: "--dns <IP>", description: "Override DNS server upstream (e.g. 1.1.1.1, 8.8.8.8, 9.9.9.9)" }
    ],
    example: "shadowtun connect -m",
    output: `[✓] Resolving physical gateway (192.168.1.1 via wlan0)...
[✓] Pinning remote server 198.51.100.42 to physical interface...
[✓] Initializing tun0 virtual network adapter (10.0.0.2/24)...
[✓] Launching sslocal (Shadowsocks-Rust) on 127.0.0.1:1080...
[✓] Launching tun2socks engine on tun0...
[✓] Binding system DNS to tun0 with systemd-resolved (1.1.1.1, 8.8.8.8)...
[✓] Hijacking default gateway -> tun0
[⚡] ShadowTun Connected! Routing all TCP/UDP/DNS traffic through tunnel.
[STATS] RX: 48.2 MB/s | TX: 12.1 MB/s | Ping: 24ms | Dropped: 0%`
  },
  {
    command: "shadowtun disconnect",
    summary: "Gracefully disconnect VPN and restore default network routing",
    category: "Connection",
    example: "shadowtun disconnect",
    output: `[✓] Stopping tun2socks and sslocal background processes...
[✓] Reverting systemd-resolved DNS settings on tun0...
[✓] Restoring physical default route (via 192.168.1.1 dev wlan0)...
[✓] Removing pinned server route...
[✓] Tearing down virtual adapter tun0...
[✓] ShadowTun disconnected cleanly. Original network restored.`
  },
  {
    command: "shadowtun status",
    summary: "Display active connection state, IP addresses, uptime, and transfer stats",
    category: "Diagnostics",
    example: "shadowtun status",
    output: `================ ShadowTun Status ================
Connection State   : CONNECTED (Active)
Virtual Interface  : tun0 (10.0.0.2 / 255.255.255.0)
Physical Gateway   : 192.168.1.1 dev wlan0
Remote Server      : 198.51.100.42:8388 (AEAD ChaCha20-Poly1305)
Current Latency    : 22 ms (TCP SYN/ACK)
DNS Resolver       : Cloudflare 1.1.1.1 / 1.0.0.1 (Strict Tunnel)
Session Duration   : 01h 42m 18s
Total Transferred  : Download 1.84 GB | Upload 412 MB
==================================================`
  },
  {
    command: "shadowtun import <KEY_URL>",
    summary: "Import and validate a new ssconf:// or Shadowsocks subscription key",
    category: "Subscription",
    example: "shadowtun import \"ssconf://....../sub/token123.json#Tokyo-Fast-01\"",
    output: `[✓] Fetching subscription payload from endpoint...
[✓] Decoded Shadowsocks configuration:
    - Server: 198.51.100.42
    - Port: 8388
    - Method: chacha20-ietf-poly1305
    - Disguise Prefix: \\x16\\x03\\x01 (TLS 1.2 Handshake)
[✓] Profile 'Tokyo-Fast-01' saved to ~/.config/shadowtun/profiles.json
[✓] Set as active default profile.`
  },
  {
    command: "shadowtun list",
    summary: "List all imported VPN profiles with latency metrics",
    category: "Subscription",
    example: "shadowtun list",
    output: `  ID | PROFILE NAME          | SERVER          | METHOD           | PING  | STATUS
----------------------------------------------------------------------------------
* 01 | Tokyo-Fast-01 (Active)| 198.51.100.42   | chacha20-poly1305| 22ms  | ONLINE
  02 | Singapore-VIP-02      | 203.0.113.88    | aes-256-gcm      | 45ms  | ONLINE
  03 | US-West-Direct-03     | 192.0.2.14      | chacha20-poly1305| 120ms | ONLINE`
  },
  {
    command: "shadowtun test",
    summary: "Run real-time latency ping and packet handshake test on all profiles",
    category: "Diagnostics",
    example: "shadowtun test",
    output: `[+] Probing Profile 01 [Tokyo-Fast-01]: 198.51.100.42:8388 -> 22ms (OK)
[+] Probing Profile 02 [Singapore-VIP-02]: 203.0.113.88:8388 -> 45ms (OK)
[+] Probing Profile 03 [US-West-Direct-03]: 192.0.2.14:8388 -> 118ms (OK)
[✓] All 3 servers responsive. Optimal node: Tokyo-Fast-01`
  },
  {
    command: "shadowtun logs",
    summary: "Tail real-time debug log stream from tun2socks, sslocal, and routing helper",
    category: "Diagnostics",
    options: [
      { flag: "-f, --follow", description: "Follow log stream in real time" },
      { flag: "-n <LINES>", description: "Number of log lines to display (default: 50)" }
    ],
    example: "shadowtun logs -f",
    output: `2026-08-31 03:10:14 [INFO] [sslocal] listening TCP/UDP on 127.0.0.1:1080
2026-08-31 03:10:14 [INFO] [tun2socks] opened tun0 interface MTU=1500
2026-08-31 03:10:15 [INFO] [route-helper] injected default route via tun0
2026-08-31 03:10:16 [DEBUG] [tun2socks] TCP proxy -> 1.1.1.1:53 via 127.0.0.1:1080
2026-08-31 03:10:17 [DEBUG] [tun2socks] UDP relay -> 8.8.8.8:53 via 127.0.0.1:1080
2026-08-31 03:10:19 [INFO] [telemetry] RX: 48.2 MB/s | TX: 12.1 MB/s`
  },
  {
    command: "shadowtun gui",
    summary: "Launch the dark-mode PyQt5 desktop graphical user interface",
    category: "System",
    example: "shadowtun gui",
    output: `[✓] Initializing PyQt5 GUI Application...
[✓] Loaded theme: Cyber Dark Obsidian (#0A0D14)
[✓] System tray initialized. Showing main window.`
  }
];

export interface ArchNode {
  id: string;
  title: string;
  subtitle: string;
  technology: string;
  description: string;
  kernelAction: string;
  tag: string;
  icon: string;
}

export const ARCH_NODES: ArchNode[] = [
  {
    id: "apps",
    title: "1. User Space Applications",
    subtitle: "Web Browsers, CLI, Games, Daemons",
    technology: "Linux Userspace",
    description: "Every application generating TCP/UDP traffic or DNS queries on the system. No per-app proxy configuration or environment variables needed.",
    kernelAction: "Standard socket() and connect() system calls",
    tag: "Source",
    icon: "💻"
  },
  {
    id: "kernel",
    title: "2. Linux Kernel TUN (`tun0`)",
    subtitle: "Virtual Layer 3 Network Device",
    technology: "Linux Kernel TUN/TAP Driver",
    description: "Virtual network adapter created at 10.0.0.2/24. ShadowTun replaces the kernel default gateway to route all outbound IP packets into /dev/net/tun.",
    kernelAction: "ip tuntap add mode tun dev tun0 && ip route replace default dev tun0",
    tag: "Kernel Layer 3",
    icon: "⚙️"
  },
  {
    id: "tun2socks",
    title: "3. tun2socks Engine",
    subtitle: "Layer 3/4 Packet Forwarding Bridge",
    technology: "Go (Golang) / tun2socks v2.x",
    description: "Reads raw IP packets from /dev/net/tun, decodes Layer 3/4 TCP/UDP payloads, and transparently bridges them to the local SOCKS5 proxy port.",
    kernelAction: "tun2socks --device tun0 --proxy socks5://127.0.0.1:1080",
    tag: "Userspace Bridge",
    icon: "🔄"
  },
  {
    id: "sslocal",
    title: "4. Shadowsocks-Rust Core",
    subtitle: "High-Speed AEAD & Anti-Censorship",
    technology: "Rust (shadowsocks-rust)",
    description: "Encrypts user data with modern AEAD ciphers (ChaCha20-Poly1305, AES-256-GCM) and attaches TLS disguise prefixes to defeat Deep Packet Inspection (DPI).",
    kernelAction: "sslocal -c /etc/shadowtun/config.json",
    tag: "Crypto Engine",
    icon: "🛡️"
  },
  {
    id: "physical",
    title: "5. Physical Network Gateway",
    subtitle: "Wi-Fi / Ethernet Interface (wlan0 / eth0)",
    technology: "iproute2 Route Pinning",
    description: "ShadowTun automatically adds a static host route for the remote proxy server via your physical gateway (e.g. 192.168.1.1) to prevent routing loops.",
    kernelAction: "ip route replace <SERVER_IP>/32 via <GATEWAY_IP> dev <IFACE>",
    tag: "Physical Layer",
    icon: "📡"
  },
  {
    id: "server",
    title: "6. Remote Shadowsocks Server",
    subtitle: "Encrypted Cloud Node & Decensored WAN",
    technology: "Remote AEAD Shadowsocks Daemon",
    description: "Decrypts traffic, forwards outbound packets to the global open internet, and relays secure responses back through the tunnel.",
    kernelAction: "Encrypted TLS-Disguised Wire Traffic over WAN",
    tag: "Destination",
    icon: "🌐"
  }
];

export interface FaqItem {
  question: string;
  category: "Installation" | "Routing" | "DNS" | "Security";
  answer: string;
  code?: string;
}

export const FAQ_ITEMS: FaqItem[] = [
  {
    question: "Why do I not need to enter my sudo password every time I connect?",
    category: "Security",
    answer: "ShadowTun installs a secure, locked-down rule in `/etc/sudoers.d/shadowtun` that exclusively authorizes the privileged helper script `/usr/local/bin/vpn-core-helper` to configure `tun0` and `iproute2` rules without giving unrestricted root access to your user account.",
    code: "# Verified helper permissions:\n/usr/bin/vpn-core-helper NOPASSWD"
  },
  {
    question: "How does ShadowTun prevent DNS and IPv6 leaks?",
    category: "DNS",
    answer: "ShadowTun hooks directly into `systemd-resolved` using `resolvectl domain tun0 '~.'` which acts as a wildcard domain sinkhole, ensuring all system DNS lookups route exclusively through the encrypted VPN tunnel. Additionally, default IPv6 routes are torn down during connection to prevent dual-stack IP leakage.",
    code: "resolvectl dns tun0 1.1.1.1 8.8.8.8\nresolvectl domain tun0 \"~.\"\nresolvectl default-route tun0 yes\nip -6 route del default"
  },
  {
    question: "What should I do if the tun0 interface already exists or gets stuck?",
    category: "Routing",
    answer: "If an improper system shutdown or another VPN client left a dangling `tun0` interface, run `shadowtun disconnect` or reset the interface with the following command:",
    code: "sudo ip link delete tun0\nsudo pkill -9 tun2socks\nsudo pkill -9 sslocal"
  },
  {
    question: "How does the ssconf:// subscription URL format work?",
    category: "Installation",
    answer: "An `ssconf://` link is an intelligent subscription URL containing the server endpoint and profile tag. ShadowTun connects to the endpoint, fetches the JSON configuration, automatically maps local proxy ports, and stores it in your profile vault.",
    code: "ssconf://sub.example.com/api/v1/profile.json#Tokyo-Fast-Node"
  }
];
