"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  BookOpen, 
  Terminal, 
  Monitor, 
  KeyRound, 
  HelpCircle, 
  Copy, 
  Check, 
  Search, 
  CheckCircle2,
  Zap,
  Sliders
} from "lucide-react";
import { CLI_COMMANDS, FAQ_ITEMS } from "@/data/appData";

export default function UserGuideSection() {
  const [activeTab, setActiveTab] = useState<"quickstart" | "gui" | "cli" | "protocol" | "faq">("quickstart");
  const [cliFilter, setCliFilter] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  useEffect(() => {
    const handleHash = () => {
      const hash = window.location.hash.toLowerCase().replace("#", "");
      if (hash === "faq" || hash === "troubleshooting") {
        setActiveTab("faq");
      } else if (hash === "gui") {
        setActiveTab("gui");
      } else if (hash === "cli") {
        setActiveTab("cli");
      } else if (hash === "protocol") {
        setActiveTab("protocol");
      } else if (hash === "quickstart" || hash === "user-guide") {
        setActiveTab("quickstart");
      }
    };

    const handleCustomTab = (e: Event) => {
      const customEvent = e as CustomEvent<string>;
      const tab = customEvent.detail;
      if (tab === "faq" || tab === "troubleshooting") {
        setActiveTab("faq");
      } else if (tab === "gui" || tab === "cli" || tab === "protocol" || tab === "quickstart") {
        setActiveTab(tab as any);
      }
    };

    handleHash();
    window.addEventListener("hashchange", handleHash);
    window.addEventListener("switch-userguide-tab", handleCustomTab);
    return () => {
      window.removeEventListener("hashchange", handleHash);
      window.removeEventListener("switch-userguide-tab", handleCustomTab);
    };
  }, []);

  const handleTabClick = (tabId: "quickstart" | "gui" | "cli" | "protocol" | "faq") => {
    setActiveTab(tabId);
    if (typeof window !== "undefined") {
      window.history.replaceState(null, "", `#${tabId}`);
    }
  };

  const handleCopy = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const filteredCommands = CLI_COMMANDS.filter((cmd) => {
    const matchesCategory = cliFilter === "All" || cmd.category === cliFilter;
    const matchesSearch =
      cmd.command.toLowerCase().includes(searchQuery.toLowerCase()) ||
      cmd.summary.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <section id="user-guide" className="py-20 md:py-28 relative bg-[#06080d]">
      {/* Anchor targets for direct linking */}
      <span id="faq" className="absolute -top-24" />
      <span id="troubleshooting" className="absolute -top-24" />
      <span id="cli" className="absolute -top-24" />
      <span id="gui" className="absolute -top-24" />
      <span id="protocol" className="absolute -top-24" />
      <span id="quickstart" className="absolute -top-24" />

      <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-cyan-300 text-xs font-semibold uppercase tracking-wider mb-3">
            <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
            <span>Complete Documentation</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight">
            ShadowTun User Guide & Manual
          </h2>
          <p className="mt-3 text-slate-300 text-sm sm:text-base">
            Master both the modern PyQt5 desktop GUI and headless CLI scripting workflows.
          </p>
        </div>

        {/* Tab Navigation Navigation Bar */}
        <div className="flex items-center justify-center gap-2 mb-10 overflow-x-auto pb-2 scrollbar-none">
          {[
            { id: "quickstart" as const, label: "Quick Start", icon: Zap },
            { id: "gui" as const, label: "Desktop GUI Guide", icon: Monitor },
            { id: "cli" as const, label: "CLI Commands Reference", icon: Terminal },
            { id: "protocol" as const, label: "ssconf:// Protocol", icon: KeyRound },
            { id: "faq" as const, label: "Troubleshooting & FAQ", icon: HelpCircle },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => handleTabClick(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  isActive
                    ? "bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-200 border border-cyan-400/50 shadow-lg shadow-cyan-950/40"
                    : "bg-slate-900/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-white/[0.06]"
                }`}
              >
                <tab.icon className={`w-4 h-4 ${isActive ? "text-cyan-400" : "text-slate-500"}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Content Panes */}
        <div className="rounded-3xl bg-[#0c101a] border border-white/[0.08] p-6 sm:p-10 shadow-2xl">
          <AnimatePresence mode="wait">
            
            {/* TAB 1: QUICK START */}
            {activeTab === "quickstart" && (
              <motion.div
                key="quickstart"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.25 }}
                className="space-y-8"
              >
                <div>
                  <h3 className="text-2xl font-bold text-white mb-2">Getting Started with ShadowTun</h3>
                  <p className="text-slate-300 text-sm">
                    Follow this 3-step guide to get ShadowTun running on your Linux desktop or server.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Step 1 */}
                  <div className="p-5 rounded-2xl bg-black/40 border border-white/[0.06] flex flex-col justify-between">
                    <div>
                      <div className="w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-300 font-mono font-bold flex items-center justify-center text-sm mb-4 border border-cyan-500/30">
                        01
                      </div>
                      <h4 className="text-base font-bold text-white mb-2">Install ShadowTun</h4>
                      <p className="text-xs text-slate-400 leading-relaxed mb-4">
                        Run the 1-command universal installer which configures dependencies, desktop shortcuts, and sudoers rules.
                      </p>
                    </div>
                    <div className="p-3 rounded-xl bg-black font-mono text-[11px] text-cyan-300 overflow-x-auto border border-white/[0.04]">
                      <code>curl -fsSL https://.../install.sh | sudo bash</code>
                    </div>
                  </div>

                  {/* Step 2 */}
                  <div className="p-5 rounded-2xl bg-black/40 border border-white/[0.06] flex flex-col justify-between">
                    <div>
                      <div className="w-8 h-8 rounded-lg bg-purple-500/20 text-purple-300 font-mono font-bold flex items-center justify-center text-sm mb-4 border border-purple-500/30">
                        02
                      </div>
                      <h4 className="text-base font-bold text-white mb-2">Import Your Key</h4>
                      <p className="text-xs text-slate-400 leading-relaxed mb-4">
                        Import an <code className="text-cyan-300 font-mono">ssconf://</code> subscription link via GUI clipboard paste or CLI.
                      </p>
                    </div>
                    <div className="p-3 rounded-xl bg-black font-mono text-[11px] text-purple-300 overflow-x-auto border border-white/[0.04]">
                      <code>shadowtun import &quot;ssconf://...&quot;</code>
                    </div>
                  </div>

                  {/* Step 3 */}
                  <div className="p-5 rounded-2xl bg-black/40 border border-white/[0.06] flex flex-col justify-between">
                    <div>
                      <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-300 font-mono font-bold flex items-center justify-center text-sm mb-4 border border-emerald-500/30">
                        03
                      </div>
                      <h4 className="text-base font-bold text-white mb-2">Connect & Switch</h4>
                      <p className="text-xs text-slate-400 leading-relaxed mb-4">
                        Connect via CLI/GUI or switch active servers seamlessly by Profile ID with <code className="text-cyan-300 font-mono">shadowtun switch &lt;ID&gt;</code>.
                      </p>
                    </div>
                    <div className="p-3 rounded-xl bg-black font-mono text-[11px] text-emerald-300 overflow-x-auto border border-white/[0.04]">
                      <code>shadowtun switch a1b2c3d4</code>
                    </div>
                  </div>
                </div>

                {/* Uninstallation Callout */}
                <div className="p-5 rounded-2xl bg-slate-900/50 border border-white/[0.06] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div>
                    <h5 className="text-sm font-bold text-slate-200">Clean Uninstallation</h5>
                    {/* <p className="text-xs text-slate-400 mt-0.5">
                      To completely remove all binaries, systemd rules, and sudoers helper files:
                    </p> */}
                  </div>
                  <div className="flex items-center gap-2 font-mono text-xs text-rose-300 bg-black/60 px-3 py-2 rounded-xl border border-rose-500/20">
                    <code>curl -fsSL https://.../uninstall.sh | sudo bash</code>
                  </div>
                </div>
              </motion.div>
            )}

            {/* TAB 2: DESKTOP GUI GUIDE */}
            {activeTab === "gui" && (
              <motion.div
                key="gui"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.25 }}
                className="space-y-8"
              >
                <div>
                  <h3 className="text-2xl font-bold text-white mb-2">PyQt5 Dark Mode Desktop GUI</h3>
                  <p className="text-slate-300 text-sm">
                    ShadowTun features a sleek, hardware-accelerated desktop interface built for Linux desktops (GNOME, KDE Plasma, XFCE, Sway, Hyprland).
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="p-4 rounded-xl bg-black/40 border border-white/[0.06]">
                      <h4 className="text-sm font-bold text-cyan-300 flex items-center gap-2">
                        <Sliders className="w-4 h-4" />
                        <span>Glowing Animated Connect Button</span>
                      </h4>
                      <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                        Features a central glowing circular switch that dynamically animates green when connected and amber during tunnel route configuration.
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-black/40 border border-white/[0.06]">
                      <h4 className="text-sm font-bold text-emerald-300 flex items-center gap-2">
                        <Zap className="w-4 h-4" />
                        <span>Real-Time Speed & Telemetry Meters</span>
                      </h4>
                      <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                        Direct kernel polling of <code className="font-mono text-cyan-300">/proc/net/dev</code> provides instantaneous Download and Upload speedometers with cumulative session bandwidth accounting.
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-black/40 border border-white/[0.06]">
                      <h4 className="text-sm font-bold text-purple-300 flex items-center gap-2">
                        <BookOpen className="w-4 h-4" />
                        <span>Clipboard Auto-Detection</span>
                      </h4>
                      <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                        Copying any <code className="font-mono text-cyan-300">ssconf://</code> or Shadowsocks URL triggers an instant import prompt without manual copy-pasting.
                      </p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="p-4 rounded-xl bg-black/40 border border-white/[0.06]">
                      <h4 className="text-sm font-bold text-amber-300 flex items-center gap-2">
                        <Monitor className="w-4 h-4" />
                        <span>System Tray Minimization</span>
                      </h4>
                      <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                        Closes seamlessly to the system status bar tray. Right-click the tray icon to quickly toggle connection, test latency, or quit.
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-black/40 border border-white/[0.06]">
                      <h4 className="text-sm font-bold text-blue-300 flex items-center gap-2">
                        <Terminal className="w-4 h-4" />
                        <span>Real-Time Debug Log Console</span>
                      </h4>
                      <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                        Built-in log terminal displaying real-time outputs from <code className="font-mono text-cyan-300">tun2socks</code>, <code className="font-mono text-cyan-300">sslocal</code>, and <code className="font-mono text-cyan-300">vpn-core-helper</code> for easy debugging.
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-black/40 border border-white/[0.06]">
                      <h4 className="text-sm font-bold text-teal-300 flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>DNS Upstream Preset Selector</span>
                      </h4>
                      <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                        Switch between Cloudflare (1.1.1.1), Google (8.8.8.8), Quad9 (9.9.9.9), or AdGuard (94.140.14.14) with a single click.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-cyan-950/20 border border-cyan-500/20 text-xs text-slate-300 flex items-center justify-between">
                  <span>To launch the desktop GUI from your terminal, simply execute:</span>
                  <code className="font-mono text-cyan-300 bg-black/60 px-3 py-1.5 rounded-lg border border-cyan-500/30">
                    shadowtun gui
                  </code>
                </div>
              </motion.div>
            )}

            {/* TAB 3: CLI COMMANDS REFERENCE */}
            {activeTab === "cli" && (
              <motion.div
                key="cli"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.25 }}
                className="space-y-6"
              >
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div>
                    <h3 className="text-2xl font-bold text-white mb-1">CLI Command Playground</h3>
                    <p className="text-slate-300 text-xs sm:text-sm">
                      Automate VPN connections, test servers, and stream logs directly in headless environments.
                    </p>
                  </div>

                  {/* Search bar */}
                  <div className="relative w-full sm:w-64">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type="text"
                      placeholder="Search command..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full bg-black/60 border border-white/10 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400 font-mono"
                    />
                  </div>
                </div>

                {/* Category Filters */}
                <div className="flex items-center gap-2 overflow-x-auto pb-1">
                  {["All", "Connection", "Subscription", "Diagnostics", "System"].map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setCliFilter(cat)}
                      className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                        cliFilter === cat
                          ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                          : "bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-white/[0.04]"
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>

                {/* Commands Accordion Grid */}
                <div className="space-y-4">
                  {filteredCommands.map((cmd, idx) => (
                    <div
                      key={cmd.command}
                      className="p-5 rounded-2xl bg-black/40 border border-white/[0.08] hover:border-cyan-500/30 transition-all space-y-3"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex items-center gap-2.5">
                          <span className="font-mono text-sm font-bold text-cyan-300">
                            {cmd.command}
                          </span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/[0.06] text-slate-400">
                            {cmd.category}
                          </span>
                        </div>

                        <button
                          onClick={() => handleCopy(cmd.example, idx)}
                          className="self-start sm:self-auto flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800 text-xs text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
                        >
                          {copiedIndex === idx ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                              <span className="text-emerald-400 text-[11px]">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              <span className="text-[11px]">Copy Command</span>
                            </>
                          )}
                        </button>
                      </div>

                      <p className="text-xs text-slate-400">{cmd.summary}</p>

                      {/* Options if available */}
                      {cmd.options && (
                        <div className="space-y-1 pt-1">
                          <span className="text-[11px] font-semibold text-slate-400">Flags & Options:</span>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                            {cmd.options.map((opt) => (
                              <div key={opt.flag} className="text-[11px] font-mono text-slate-400">
                                <span className="text-purple-300 font-semibold">{opt.flag}</span>: {opt.description}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Output preview */}
                      <div className="mt-2 p-3 rounded-xl bg-black/80 border border-white/[0.04] font-mono text-[11px] text-slate-300 overflow-x-auto">
                        <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1 font-semibold">
                          Expected Terminal Output:
                        </div>
                        <pre className="text-emerald-400/90 whitespace-pre-wrap leading-relaxed">
                          {cmd.output}
                        </pre>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* TAB 4: ssconf:// PROTOCOL */}
            {activeTab === "protocol" && (
              <motion.div
                key="protocol"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.25 }}
                className="space-y-6"
              >
                <div>
                  <h3 className="text-2xl font-bold text-white mb-2">ssconf:// Protocol Specification</h3>
                  <p className="text-slate-300 text-sm">
                    How ShadowTun decodes, decrypts, and maps dynamic subscription endpoints.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-black/60 border border-cyan-500/20 font-mono text-xs text-cyan-300 select-all">
                  ssconf://..../api/v1/client/subscribe?token=xyz...#Profile-Label
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-5 rounded-2xl bg-black/40 border border-white/[0.06] space-y-3">
                    <h4 className="text-sm font-bold text-white">1. URL Fetch & Verification</h4>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      ShadowTun strips the <code className="text-cyan-300 font-mono">ssconf://</code> scheme to <code className="text-cyan-300 font-mono">https://</code>, requests the subscription payload over TLS, and checks HTTP response headers for account quota warnings or server package expirations.
                    </p>
                  </div>

                  <div className="p-5 rounded-2xl bg-black/40 border border-white/[0.06] space-y-3">
                    <h4 className="text-sm font-bold text-white">2. Base64 Shadowsocks Decryption</h4>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      The payload is unpacked into standard Shadowsocks client configurations, extracting the remote host, remote port, AEAD cipher (<code className="text-purple-300 font-mono">chacha20-ietf-poly1305</code>), password, and custom packet prefix headers.
                    </p>
                  </div>

                  <div className="p-5 rounded-2xl bg-black/40 border border-white/[0.06] space-y-3">
                    <h4 className="text-sm font-bold text-white">3. Local Port & Profile Binding</h4>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      Injects local SOCKS5 listening address (<code className="text-cyan-300 font-mono">127.0.0.1:1080</code>) and saves the active node profile to <code className="text-slate-300 font-mono">~/.config/shadowtun/profiles.json</code>.
                    </p>
                  </div>

                  <div className="p-5 rounded-2xl bg-black/40 border border-white/[0.06] space-y-3">
                    <h4 className="text-sm font-bold text-white">4. Packet Prefix & TLS Disguise</h4>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      If the subscription defines a prefix header (e.g. <code className="text-emerald-300 font-mono">\x16\x03\x01</code> for TLS Client Hello), ShadowTun injects it into <code className="text-slate-300 font-mono">sslocal</code> to disguise proxy packets as standard HTTPS traffic.
                    </p>
                  </div>
                </div>
              </motion.div>
            )}

            {/* TAB 5: TROUBLESHOOTING & FAQ */}
            {activeTab === "faq" && (
              <motion.div
                key="faq"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.25 }}
                className="space-y-6"
              >
                <div>
                  <h3 className="text-2xl font-bold text-white mb-2">Frequently Asked Questions & Troubleshooting</h3>
                  <p className="text-slate-300 text-sm">
                    Common issues, systemd-resolved DNS diagnostics, and Linux routing questions.
                  </p>
                </div>

                <div className="space-y-4">
                  {FAQ_ITEMS.map((faq) => (
                    <div
                      key={faq.question}
                      className="p-5 rounded-2xl bg-black/40 border border-white/[0.08] space-y-3"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <h4 className="text-sm sm:text-base font-bold text-white">
                          {faq.question}
                        </h4>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                          {faq.category}
                        </span>
                      </div>

                      <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                        {faq.answer}
                      </p>

                      {faq.code && (
                        <div className="p-3 rounded-xl bg-black/80 border border-white/[0.06] font-mono text-[11px] text-emerald-300 overflow-x-auto select-all">
                          <pre>{faq.code}</pre>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

          </AnimatePresence>
        </div>

      </div>
    </section>
  );
}
