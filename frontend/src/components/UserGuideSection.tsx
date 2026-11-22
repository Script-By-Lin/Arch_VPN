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
  Sliders,
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
        setActiveTab(tab);
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
    <section id="user-guide" className="py-20 md:py-28 relative bg-white border-t border-slate-200/80">
      <span id="faq" className="absolute -top-24" />
      <span id="troubleshooting" className="absolute -top-24" />
      <span id="cli" className="absolute -top-24" />
      <span id="gui" className="absolute -top-24" />
      <span id="protocol" className="absolute -top-24" />
      <span id="quickstart" className="absolute -top-24" />

      <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-sky-50 border border-sky-200 text-sky-700 text-xs font-bold uppercase tracking-wider mb-3">
            <BookOpen className="w-3.5 h-3.5 text-sky-600" />
            <span>Complete Documentation</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight">
            AuraLink User Guide & Manual
          </h2>
          <p className="mt-3 text-slate-600 text-sm sm:text-base">
            Master both the modern Daylight PyQt5 desktop GUI and headless CLI scripting workflows.
          </p>
        </div>

        {/* Animated Tab Navigation */}
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
                className={`relative flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer whitespace-nowrap border ${
                  isActive
                    ? "bg-sky-600 text-white border-sky-600 shadow-md shadow-sky-600/20"
                    : "bg-slate-50 text-slate-600 hover:text-sky-700 hover:bg-sky-50 border-slate-200"
                }`}
              >
                <tab.icon className={`w-4 h-4 ${isActive ? "text-white" : "text-slate-400"}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Content Panes */}
        <div className="max-w-6xl mx-auto rounded-3xl bg-slate-50/70 border border-slate-200 p-6 sm:p-10 shadow-sm">
          <AnimatePresence mode="wait">
            {/* TAB 1: QUICK START */}
            {activeTab === "quickstart" && (
              <motion.div
                key="quickstart"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.22 }}
                className="space-y-8"
              >
                <div>
                  <h3 className="text-2xl font-extrabold text-slate-900 mb-2">Getting Started with AuraLink</h3>
                  <p className="text-slate-600 text-sm">
                    Follow this 3-step guide to get AuraLink running on your Linux desktop or server.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs flex flex-col justify-between">
                    <div>
                      <div className="w-8 h-8 rounded-lg bg-sky-50 text-sky-700 font-mono font-bold flex items-center justify-center text-sm mb-4 border border-sky-200">
                        01
                      </div>
                      <h4 className="text-base font-bold text-slate-900 mb-2">Install AuraLink</h4>
                      <p className="text-xs text-slate-600 leading-relaxed mb-4">
                        Run the 1-command universal installer which configures dependencies, desktop shortcuts, and sudoers rules.
                      </p>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-900 font-mono text-[11px] text-sky-300 overflow-x-auto">
                      <code>curl -fsSL https://.../install.sh | sudo bash</code>
                    </div>
                  </div>

                  <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs flex flex-col justify-between">
                    <div>
                      <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-700 font-mono font-bold flex items-center justify-center text-sm mb-4 border border-indigo-200">
                        02
                      </div>
                      <h4 className="text-base font-bold text-slate-900 mb-2">Import Your Key</h4>
                      <p className="text-xs text-slate-600 leading-relaxed mb-4">
                        Import an <code className="text-sky-700 font-mono font-semibold">ssconf://</code> subscription link via GUI or CLI.
                      </p>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-900 font-mono text-[11px] text-indigo-300 overflow-x-auto">
                      <code>auralink import &quot;ssconf://...&quot;</code>
                    </div>
                  </div>

                  <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs flex flex-col justify-between">
                    <div>
                      <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-700 font-mono font-bold flex items-center justify-center text-sm mb-4 border border-emerald-200">
                        03
                      </div>
                      <h4 className="text-base font-bold text-slate-900 mb-2">Connect & Switch</h4>
                      <p className="text-xs text-slate-600 leading-relaxed mb-4">
                        Connect via CLI/GUI or switch active servers seamlessly by Profile ID with{" "}
                        <code className="text-sky-700 font-mono font-semibold">auralink switch &lt;ID&gt;</code>.
                      </p>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-900 font-mono text-[11px] text-emerald-300 overflow-x-auto">
                      <code>auralink switch a1b2c3d4</code>
                    </div>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-white border border-slate-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div>
                    <h5 className="text-sm font-bold text-slate-900">Clean Uninstallation</h5>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Safely disconnects active tunnels, restores routing/IPv6/DNS, and cleans system files (add <code className="font-mono">--purge</code> to remove user profiles).
                    </p>
                  </div>
                  <div className="flex items-center gap-2 font-mono text-xs text-rose-700 bg-rose-50 px-3.5 py-2 rounded-xl border border-rose-200 shrink-0">
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
                transition={{ duration: 0.22 }}
                className="space-y-8"
              >
                <div>
                  <h3 className="text-2xl font-extrabold text-slate-900 mb-2">PyQt5 Daylight Desktop GUI</h3>
                  <p className="text-slate-600 text-sm">
                    AuraLink features a bright, responsive light-mode desktop interface built for Linux desktops (GNOME, KDE Plasma, XFCE, Sway, Hyprland).
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  {[
                    {
                      icon: Sliders,
                      color: "text-sky-700",
                      title: "Animated Orbital Connect Hub",
                      desc: "Frosted circular switch with smooth hover interpolation, rotating orbital handshake arc, and concentric ripple rings while connected.",
                    },
                    {
                      icon: Zap,
                      color: "text-emerald-700",
                      title: "Live Speed Sparklines & Telemetry",
                      desc: "Direct kernel polling of /proc/net/dev renders real-time Download/Upload speed readouts with animated throughput waveforms.",
                    },
                    {
                      icon: BookOpen,
                      color: "text-indigo-700",
                      title: "Interactive Live Tunnel Model",
                      desc: "Inspect live packet flow across Apps, tun0, sslocal, and remote VPN server right inside the desktop window.",
                    },
                    {
                      icon: Monitor,
                      color: "text-amber-700",
                      title: "System Tray Integration",
                      desc: "Minimizes cleanly to your system status bar tray with quick connect/disconnect controls.",
                    },
                    {
                      icon: Terminal,
                      color: "text-blue-700",
                      title: "Real-Time Debug Log Console",
                      desc: "Built-in live log tail streaming events from tun2socks, sslocal, and kernel routing/IPv6 controls.",
                    },
                    {
                      icon: CheckCircle2,
                      color: "text-teal-700",
                      title: "DNS Preset & IPv6 Leak Guard",
                      desc: "Switch between Cloudflare, Google, Quad9, and AdGuard live while IPv6 is automatically disabled during VPN sessions.",
                    },
                  ].map((item) => (
                    <div key={item.title} className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs">
                      <h4 className={`text-sm font-bold ${item.color} flex items-center gap-2`}>
                        <item.icon className="w-4 h-4" />
                        <span>{item.title}</span>
                      </h4>
                      <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">{item.desc}</p>
                    </div>
                  ))}
                </div>

                <div className="p-4 rounded-2xl bg-sky-50 border border-sky-200 text-xs text-slate-700 flex flex-wrap items-center justify-between gap-3">
                  <span className="font-medium">To launch the desktop GUI from your terminal, execute:</span>
                  <code className="font-mono font-bold text-sky-800 bg-white px-3.5 py-1.5 rounded-lg border border-sky-200">
                    auralink gui
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
                transition={{ duration: 0.22 }}
                className="space-y-6"
              >
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div>
                    <h3 className="text-2xl font-extrabold text-slate-900 mb-1">CLI Command Reference</h3>
                    <p className="text-slate-600 text-xs sm:text-sm">
                      Automate VPN connections, test servers, and stream logs directly in headless environments.
                    </p>
                  </div>

                  <div className="relative w-full sm:w-64">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type="text"
                      placeholder="Search command..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full bg-white border border-slate-200 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-sky-500 font-mono"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2 overflow-x-auto pb-1">
                  {["All", "Connection", "Subscription", "Diagnostics", "System"].map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setCliFilter(cat)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors cursor-pointer border ${
                        cliFilter === cat
                          ? "bg-sky-600 text-white border-sky-600"
                          : "bg-white text-slate-600 hover:text-sky-700 border-slate-200"
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>

                <div className="space-y-4">
                  {filteredCommands.map((cmd, idx) => (
                    <div
                      key={cmd.command}
                      className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-sky-300 transition-all space-y-3 shadow-xs"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex items-center gap-2.5 flex-wrap">
                          <span className="font-mono text-sm font-bold text-sky-700">{cmd.command}</span>
                          <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                            {cmd.category}
                          </span>
                        </div>

                        <button
                          onClick={() => handleCopy(cmd.example, idx)}
                          className="self-start sm:self-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 text-xs font-semibold text-slate-700 hover:text-sky-700 hover:bg-sky-50 border border-slate-200 transition-colors cursor-pointer"
                        >
                          {copiedIndex === idx ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-emerald-600" />
                              <span className="text-emerald-700 text-[11px]">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              <span className="text-[11px]">Copy Command</span>
                            </>
                          )}
                        </button>
                      </div>

                      <p className="text-xs text-slate-600">{cmd.summary}</p>

                      {cmd.options && (
                        <div className="space-y-1 pt-1">
                          <span className="text-[11px] font-bold text-slate-700">Flags & Options:</span>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                            {cmd.options.map((opt) => (
                              <div key={opt.flag} className="text-[11px] font-mono text-slate-600">
                                <span className="text-indigo-700 font-bold">{opt.flag}</span>: {opt.description}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="mt-2 p-3.5 rounded-xl bg-slate-900 font-mono text-[11px] text-slate-200 overflow-x-auto">
                        <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1 font-semibold">
                          Expected Terminal Output:
                        </div>
                        <pre className="text-emerald-300 whitespace-pre-wrap leading-relaxed">{cmd.output}</pre>
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
                transition={{ duration: 0.22 }}
                className="space-y-6"
              >
                <div>
                  <h3 className="text-2xl font-extrabold text-slate-900 mb-2">ssconf:// Protocol Specification</h3>
                  <p className="text-slate-600 text-sm">
                    How AuraLink decodes, decrypts, and maps dynamic subscription endpoints.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-900 font-mono text-xs text-sky-300 select-all">
                  ssconf://..../api/v1/client/subscribe?token=xyz...#Profile-Label
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  {[
                    {
                      title: "1. URL Fetch & Verification",
                      body: "Strips ssconf:// to https://, requests the subscription payload over TLS, and checks for provider quota or expiration error payloads.",
                    },
                    {
                      title: "2. Shadowsocks Config Parsing",
                      body: "Extracts server endpoint, port, AEAD cipher (chacha20-ietf-poly1305, aes-256-gcm), password, and optional anti-DPI prefix headers.",
                    },
                    {
                      title: "3. Local Port & Profile Binding",
                      body: "Injects local SOCKS5 address (127.0.0.1:1080) and stores the profile in ~/.config/auralink/profiles.json.",
                    },
                    {
                      title: "4. Packet Prefix & TLS Disguise",
                      body: "Passes configured TLS Client Hello prefix bytes directly to sslocal so outbound proxy traffic resembles standard HTTPS handshakes.",
                    },
                  ].map((card) => (
                    <div key={card.title} className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-2">
                      <h4 className="text-sm font-bold text-slate-900">{card.title}</h4>
                      <p className="text-xs text-slate-600 leading-relaxed">{card.body}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* TAB 5: FAQ */}
            {activeTab === "faq" && (
              <motion.div
                key="faq"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.22 }}
                className="space-y-6"
              >
                <div>
                  <h3 className="text-2xl font-extrabold text-slate-900 mb-2">
                    Frequently Asked Questions & Troubleshooting
                  </h3>
                  <p className="text-slate-600 text-sm">
                    Common issues, systemd-resolved DNS diagnostics, IPv6 leak protection, and Linux routing questions.
                  </p>
                </div>

                <div className="space-y-4">
                  {FAQ_ITEMS.map((faq) => (
                    <div
                      key={faq.question}
                      className="p-5 rounded-2xl bg-white border border-slate-200 space-y-3 shadow-xs"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <h4 className="text-sm sm:text-base font-bold text-slate-900">{faq.question}</h4>
                        <span className="text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-md bg-sky-50 text-sky-700 border border-sky-200 shrink-0">
                          {faq.category}
                        </span>
                      </div>

                      <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">{faq.answer}</p>

                      {faq.code && (
                        <div className="p-3.5 rounded-xl bg-slate-900 font-mono text-[11px] text-emerald-300 overflow-x-auto select-all">
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
