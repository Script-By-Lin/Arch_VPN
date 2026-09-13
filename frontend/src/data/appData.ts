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
    description: "One-line automated installer for all modern Linux distributions. Automatically detects your package manager, resolves dependencies, and installs AuraLink system-wide.",
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
    notes: "Installs binary to /usr/local/bin/auralink with desktop entry and icon."
  },
  {
    id: "debian",
    name: "Debian / Ubuntu / Mint",
    icon: "🍥",
    badge: ".deb Package",
    command: "git clone https://github.com/Script-By-Lin/Arch_VPN.git\ncd Arch_VPN\n./packaging/build-deb.sh\nsudo dpkg -i dist/auralink_*.deb",
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
    command: "auralink connect [TARGET]",
    summary: "Initiate full-tunnel VPN connection (by Profile ID, Name, or key URL)",
    category: "Connection",
    options: [
      { flag: "-m, --monitor", description: "Stream real-time RX/TX network statistics directly in the terminal" },
      { flag: "[TARGET]", description: "Profile ID (e.g. a1b2c3d4), Name, or ssconf:// subscription URL" }
    ],
    example: "auralink connect a1b2c3d4",
    output: `[*] Preparing connection...
  → Resolving physical network gateway...
  → Resolving server 198.51.100.42...
  → Starting Shadowsocks core...
  → Creating TUN interface tun0...
[✓] Connected successfully!
    Profile : Tokyo-Fast-01
    Server  : 198.51.100.42:443
    TUN Dev : tun0`
  },
  {
    command: "auralink switch <TARGET>",
    summary: "Seamlessly switch active VPN server by Profile ID or Name without manual disconnect",
    category: "Connection",
    options: [
      { flag: "-m, --monitor", description: "Keep running and stream live traffic statistics after switching" },
      { flag: "<TARGET>", description: "Profile ID (full or prefix like a1b2) or Profile Name to switch to" }
    ],
    example: "auralink switch f7c320d9",
    output: `[*] Preparing connection...
  → Switching from Tokyo-Fast-01 to Singapore-VIP-02...
  → Resolving server 203.0.113.88...
  → Starting Shadowsocks core...
  → Creating TUN interface tun0...
[✓] Connected successfully!
    Profile : Singapore-VIP-02
    Server  : 203.0.113.88:8443
    TUN Dev : tun0`
  },
  {
    command: "auralink disconnect",
    summary: "Gracefully disconnect VPN and restore default network routing and DNS",
    category: "Connection",
    example: "auralink disconnect",
    output: `[*] Disconnecting VPN...
[✓] Disconnected successfully. Default routes and DNS restored.`
  },
  {
    command: "auralink status",
    summary: "Display active connection state, IP addresses, uptime, and transfer stats",
    category: "Diagnostics",
    example: "auralink status",
    output: `VPN Status: CONNECTED
  Profile : Tokyo-Fast-01 (ID: a1b2c3d4)
  Server  : 198.51.100.42:443
  Method  : chacha20-ietf-poly1305
  Uptime  : 01h 42m 18s
  Download: 1.84 GB (48.2 MB/s)
  Upload  : 412 MB (12.1 MB/s)`
  },
  {
    command: "auralink import <KEY_URL>",
    summary: "Import and validate a new ssconf:// or Shadowsocks subscription key",
    category: "Subscription",
    example: "auralink import \"ssconf://sub.example.com/api/v1/sub_token123.json#Tokyo-Fast-01\"",
    output: `[*] Parsing and fetching key: ssconf://sub.example.com/api/v1/sub_token123.json...
[✓] Successfully imported profile!
    ID     : a1b2c3d4
    Name   : Tokyo-Fast-01
    Server : 198.51.100.42:443
    Method : chacha20-ietf-poly1305
    Prefix : Enabled (Anti-Censorship)

To connect: auralink connect a1b2c3d4`
  },
  {
    command: "auralink list",
    summary: "List all saved VPN profiles with IDs, servers, and active statuses",
    category: "Subscription",
    example: "auralink list",
    output: `Saved VPN Profiles (3):
ID         NAME                             SERVER                 PORT   STATUS
------------------------------------------------------------------------------
a1b2c3d4   Tokyo-Fast-01                    198.51.100.42          443    ● ACTIVE
f7c320d9   Singapore-VIP-02                 203.0.113.88           8443   
9e4d10ba   US-West-Direct-03                192.0.2.14             443`
  },
  {
    command: "auralink test",
    summary: "Run real-time latency ping and packet handshake test on all profiles",
    category: "Diagnostics",
    example: "auralink test",
    output: `[*] Testing server latencies...
  Pinging Tokyo-Fast-01 (198.51.100.42:443)... 22 ms
  Pinging Singapore-VIP-02 (203.0.113.88:8443)... 45 ms
  Pinging US-West-Direct-03 (192.0.2.14:443)... 118 ms`
  },
  {
    command: "auralink logs",
    summary: "View recent VPN core logs or stream live updates in real time (-f / --follow)",
    category: "Diagnostics",
    options: [
      { flag: "-f, --follow", description: "Follow log stream in real time" },
      { flag: "-n <LINES>", description: "Number of initial log lines to show (default: 40)" }
    ],
    example: "auralink logs -f",
    output: `[*] Streaming real-time VPN logs (Ctrl+C to stop)...
[sslocal] 2026-09-01T01:16:55.080 DEBUG tokio-rt-worker CONNECT 198.51.100.42:443
[sslocal] 2026-09-01T01:16:55.313 DEBUG tokio-rt-worker established tcp tunnel 127.0.0.1:42558 <-> 198.51.100.42:443
[tun2socks] time="2026-09-01T01:16:56" level=info msg="[TCP] 10.0.0.2:33154 <-> 198.51.100.42:443"
[sslocal] 2026-09-01T01:17:08.265 DEBUG tokio-rt-worker CONNECT 203.0.113.88:443`
  },
  {
    command: "auralink gui",
    summary: "Launch the dark-mode PyQt5 desktop graphical user interface",
    category: "System",
    example: "auralink gui",
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
    description: "Virtual network adapter created at 10.0.0.2/24. AuraLink replaces the kernel default gateway to route all outbound IP packets into /dev/net/tun.",
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
    kernelAction: "sslocal -c /etc/auralink/config.json",
    tag: "Crypto Engine",
    icon: "🛡️"
  },
  {
    id: "physical",
    title: "5. Physical Network Gateway",
    subtitle: "Wi-Fi / Ethernet Interface (wlan0 / eth0)",
    technology: "iproute2 Route Pinning",
    description: "AuraLink automatically adds a static host route for the remote proxy server via your physical gateway (e.g. 192.168.1.1) to prevent routing loops.",
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
    answer: "AuraLink installs a secure, locked-down rule in `/etc/sudoers.d/auralink` that exclusively authorizes the privileged helper script `/usr/local/bin/vpn-core-helper` to configure `tun0` and `iproute2` rules without giving unrestricted root access to your user account.",
    code: "# Verified helper permissions:\n/usr/bin/vpn-core-helper NOPASSWD"
  },
  {
    question: "How does AuraLink prevent DNS and IPv6 leaks?",
    category: "DNS",
    answer: "AuraLink hooks directly into `systemd-resolved` using `resolvectl domain tun0 '~.'` which acts as a wildcard domain sinkhole, ensuring all system DNS lookups route exclusively through the encrypted VPN tunnel. Additionally, default IPv6 routes are torn down during connection to prevent dual-stack IP leakage.",
    code: "resolvectl dns tun0 1.1.1.1 8.8.8.8\nresolvectl domain tun0 \"~.\"\nresolvectl default-route tun0 yes\nip -6 route del default"
  },
  {
    question: "What should I do if the tun0 interface already exists or gets stuck?",
    category: "Routing",
    answer: "If an improper system shutdown or another VPN client left a dangling `tun0` interface, run `auralink disconnect` or reset the interface with the following command:",
    code: "sudo ip link delete tun0\nsudo pkill -9 tun2socks\nsudo pkill -9 sslocal"
  },
  {
    question: "How do I switch servers by Profile ID or Name?",
    category: "Routing",
    answer: "You can view all saved profiles and their 8-character IDs with `auralink list`, then switch immediately using `auralink switch <ID>` or `auralink connect <ID>`. Short prefix matching (e.g. first 4 characters) and profile names are supported, and active VPN tunnels will switch seamlessly without manual disconnection.",
    code: "# List available servers and IDs:\nauralink list\n\n# Switch using ID (or prefix):\nauralink switch a1b2c3d4\n\n# Or using connect:\nauralink connect a1b2c3d4\n\n# Or by Profile Name:\nauralink switch \"Tokyo-Fast-01\""
  },
  {
    question: "How do I view and stream live VPN logs in real time?",
    category: "Routing",
    answer: "Run `auralink logs -f` (or `auralink logs --follow`). AuraLink will display initial recent entries and stream all newly appended connection, DNS, and proxy events in real time with formatted tags.",
    code: "# Stream live logs:\nauralink logs -f\n\n# Stream live logs with custom initial lines:\nauralink logs -f -n 100"
  },
  {
    question: "How does the ssconf:// subscription URL format work?",
    category: "Installation",
    answer: "An `ssconf://` link is an intelligent subscription URL containing the server endpoint and profile tag. AuraLink connects to the endpoint, fetches the JSON configuration, automatically maps local proxy ports, and stores it in your profile vault.",
    code: "ssconf://sub.example.com/api/v1/profile.json#Tokyo-Fast-Node"
  }
];
