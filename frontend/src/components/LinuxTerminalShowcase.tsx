"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Terminal, Activity, Sparkles, Layers, ShieldCheck } from "lucide-react";

export default function LinuxTerminalShowcase() {
  const [activeTab, setActiveTab] = useState<"fastfetch" | "dmesg" | "iproute">("fastfetch");
  const [typedCommand, setTypedCommand] = useState("");
  const [cursorVisible, setCursorVisible] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setCursorVisible((v) => !v);
    }, 530);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const targetCommand =
      activeTab === "fastfetch"
        ? "fastfetch --structure Title:OS:Kernel:Uptime:Packages:Shell:DE:Terminal:Network"
        : activeTab === "dmesg"
        ? "sudo dmesg -w --facility=daemon,kern | grep -E 'tun|auralink|sslocal'"
        : "ip -brief address show && ip route show default";

    let idx = 0;
    const typing = setInterval(() => {
      idx++;
      if (idx <= targetCommand.length) {
        setTypedCommand(targetCommand.slice(0, idx));
      } else {
        clearInterval(typing);
      }
    }, 20);

    return () => clearInterval(typing);
  }, [activeTab]);

  return (
    <section
      id="kernel-integration"
      className="py-16 md:py-24 relative overflow-hidden bg-[#f8fafc] border-t border-slate-200/80"
    >
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-sky-200/35 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/3 -right-32 w-96 h-96 bg-indigo-200/30 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.45 }}
          className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-6 max-w-6xl mx-auto"
        >
          <div>
            <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-sky-50 border border-sky-200 text-sky-700 text-xs font-bold uppercase tracking-wider mb-3">
              <Sparkles className="w-3.5 h-3.5 text-sky-600" />
              <span>Native Linux Subsystem</span>
            </div>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight">
              Deep Kernel Integration
            </h2>
            <p className="mt-3 text-slate-600 text-sm sm:text-base max-w-2xl leading-relaxed">
              Real-time inspection of the Linux kernel network stack, TUN virtual interface provisioning, IPv6 leak blocking, and system routing telemetry.
            </p>
          </div>

          {/* Animated Sliding Pill Switcher */}
          <div className="flex items-center gap-1.5 bg-white p-1.5 rounded-2xl border border-slate-200 shadow-xs">
            {[
              { id: "fastfetch" as const, label: "Fastfetch HUD", icon: Terminal },
              { id: "dmesg" as const, label: "Kernel dmesg", icon: Activity },
              { id: "iproute" as const, label: "ip route & tun0", icon: Layers },
            ].map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`relative flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-mono font-bold transition-colors cursor-pointer ${
                    isActive ? "text-sky-800" : "text-slate-500 hover:text-slate-800"
                  }`}
                >
                  {isActive && (
                    <motion.div
                      layoutId="terminalActiveTab"
                      transition={{ type: "spring", stiffness: 380, damping: 28 }}
                      className="absolute inset-0 bg-sky-50 border border-sky-200 rounded-xl shadow-xs"
                    />
                  )}
                  <tab.icon className="w-3.5 h-3.5 relative z-10" />
                  <span className="relative z-10">{tab.label}</span>
                </button>
              );
            })}
          </div>
        </motion.div>

        {/* Daylight Terminal Window */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="max-w-6xl mx-auto rounded-3xl bg-white border border-slate-200 shadow-xl shadow-slate-900/[0.06] overflow-hidden font-mono"
        >
          {/* Header Bar */}
          <div className="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-rose-400" />
              <div className="w-3 h-3 rounded-full bg-amber-400" />
              <div className="w-3 h-3 rounded-full bg-emerald-400" />
              <span className="text-xs text-slate-600 ml-2 font-mono font-semibold">
                bit@cachyos-arch: ~/auralink
              </span>
            </div>

            <div className="flex items-center gap-3 text-xs text-slate-500">
              <span className="hidden sm:inline-block text-[11px] text-emerald-700 font-bold">
                ● KERNEL ACTIVE: 6.12.9-cachyos
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-md bg-white text-sky-700 border border-slate-200 font-semibold">
                bash 5.2.37
              </span>
            </div>
          </div>

          {/* Terminal Body */}
          <div className="p-6 sm:p-8 space-y-6 text-xs sm:text-sm leading-relaxed overflow-x-auto min-h-[340px] bg-white">
            {/* Active Command Prompt */}
            <div className="flex items-center gap-2 text-slate-700 flex-wrap">
              <span className="text-emerald-700 font-bold">bit@cachyos</span>
              <span className="text-slate-400">:</span>
              <span className="text-sky-700 font-bold">~/auralink</span>
              <span className="text-slate-400">$</span>
              <span className="text-slate-900 font-semibold">{typedCommand}</span>
              <span
                className={`w-2 h-4 bg-sky-600 ${cursorVisible ? "opacity-100" : "opacity-0"}`}
              />
            </div>

            {/* TAB 1: FASTFETCH */}
            {activeTab === "fastfetch" && (
              <motion.div
                key="fastfetch"
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25 }}
                className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center pt-2"
              >
                <div className="md:col-span-5 text-sky-700 font-mono text-xs sm:text-sm leading-tight select-none">
                  <pre className="text-sky-700 font-semibold">
{`       /\\         AuraLink Linux
      /  \\        ----------------
     /\\   \\       OS: Arch Linux x86_64
    /      \\      Host: Linux Workstation
   /   ,,   \\     Kernel: 6.12.9-cachyos-v3
  /   |  |  -\\    Uptime: 4 days, 18 hours
 /_-''    ''-_\\   Packages: 1142 (pacman)
                  Shell: bash 5.2.37
                  DE: KDE Plasma 6.3 / Wayland
                  WM: KWin (Wayland)
                  Terminal: alacritty`}
                  </pre>
                </div>

                <div className="md:col-span-7 space-y-2.5 bg-slate-50 p-4 sm:p-5 rounded-2xl border border-slate-200">
                  <div className="flex justify-between items-center text-xs pb-1.5 border-b border-slate-200">
                    <span className="text-slate-500">Virtual TUN Interface:</span>
                    <span className="text-emerald-700 font-bold">tun0 (10.0.0.2/24) • MTU 1500</span>
                  </div>
                  <div className="flex justify-between items-center text-xs pb-1.5 border-b border-slate-200">
                    <span className="text-slate-500">Default Route:</span>
                    <span className="text-sky-700 font-bold">default dev tun0 (100% Routed)</span>
                  </div>
                  <div className="flex justify-between items-center text-xs pb-1.5 border-b border-slate-200">
                    <span className="text-slate-500">IPv6 Leak Protection:</span>
                    <span className="text-emerald-700 font-bold">disable_ipv6=1 (Restored on exit)</span>
                  </div>
                  <div className="flex justify-between items-center text-xs pb-1.5 border-b border-slate-200">
                    <span className="text-slate-500">DNS Sinkhole:</span>
                    <span className="text-indigo-700 font-bold">systemd-resolved (~. wildcard)</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-500">Active AEAD Cipher:</span>
                    <span className="text-amber-700 font-bold">chacha20-ietf-poly1305 + TLS Prefix</span>
                  </div>

                  <div className="pt-2">
                    <div className="flex justify-between text-[11px] text-slate-500 mb-1">
                      <span>Kernel Ring Buffer Allocation</span>
                      <span className="text-sky-700 font-bold">0.02% (Zero Overhead)</span>
                    </div>
                    <div className="h-2 rounded-full bg-slate-200 overflow-hidden">
                      <motion.div
                        initial={{ width: "0%" }}
                        animate={{ width: "38%" }}
                        transition={{ duration: 0.9 }}
                        className="h-full bg-gradient-to-r from-sky-500 to-emerald-500 rounded-full"
                      />
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* TAB 2: DMESG */}
            {activeTab === "dmesg" && (
              <motion.div
                key="dmesg"
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25 }}
                className="space-y-1.5 text-xs font-mono text-slate-700 bg-slate-50 p-4 rounded-2xl border border-slate-200"
              >
                <div className="text-slate-400">[    0.000000] Linux version 6.12.9-cachyos (gcc 14.2.1) #1 SMP PREEMPT_DYNAMIC</div>
                <div>[    1.102840] <span className="text-sky-700 font-bold">tun:</span> Universal TUN/TAP device driver, 1.6</div>
                <div className="text-emerald-700 font-semibold">[   42.189201] auralink[1204]: privileged helper executing /usr/local/bin/vpn-core-helper</div>
                <div className="text-sky-700 font-semibold">[   42.204510] tun0: link becomes ready, MTU set to 1500</div>
                <div className="text-emerald-700 font-semibold">[   42.212040] sysctl: net.ipv6.conf.all.disable_ipv6 = 1 (IPv6 leak shield armed)</div>
                <div className="text-emerald-700">[   42.215090] tun2socks[1210]: device=tun0, proxy=socks5://127.0.0.1:1080, mtu=1500</div>
                <div className="text-indigo-700">[   42.228940] sslocal[1209]: listening TCP/UDP on 127.0.0.1:1080 (AEAD chacha20-poly1305)</div>
                <div className="text-amber-700">[   42.240105] iproute2: route replace 198.51.100.42/32 via 192.168.1.1 dev wlan0 (pinned)</div>
                <div className="text-sky-700">[   42.251400] systemd-resolved[450]: Using DNS server 1.1.1.1 for interface tun0 (~.)</div>
                <div className="text-emerald-700 font-bold">[   42.260800] auralink: full-tunnel connection established. Zero IPv4/IPv6/DNS leaks.</div>
              </motion.div>
            )}

            {/* TAB 3: IP ROUTE */}
            {activeTab === "iproute" && (
              <motion.div
                key="iproute"
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25 }}
                className="space-y-4 text-xs font-mono"
              >
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <div className="text-slate-500 text-[11px] font-bold uppercase tracking-wider">
                    # ip -brief address show
                  </div>
                  <div className="text-slate-700">lo               UNKNOWN        127.0.0.1/8 ::1/128</div>
                  <div className="text-slate-700">wlan0            UP             192.168.1.145/24 (IPv6 disabled)</div>
                  <div className="text-emerald-700 font-bold">tun0             UP             10.0.0.2/24</div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <div className="text-slate-500 text-[11px] font-bold uppercase tracking-wider">
                    # ip route show
                  </div>
                  <div className="text-emerald-700 font-bold">default dev tun0 scope link</div>
                  <div className="text-sky-700 font-semibold">10.0.0.0/24 dev tun0 proto kernel scope link src 10.0.0.2</div>
                  <div className="text-amber-700 font-semibold">198.51.100.42 via 192.168.1.1 dev wlan0 proto static (PINNED PROXY)</div>
                  <div className="text-slate-500">192.168.1.0/24 dev wlan0 proto kernel scope link src 192.168.1.145</div>
                </div>
              </motion.div>
            )}
          </div>

          {/* Status Bar */}
          <div className="px-5 py-2.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-[11px] text-slate-600">
            <div className="flex items-center gap-2 font-semibold">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Layer 3 Subsystem Integrity: OK</span>
            </div>
            <div className="font-mono text-sky-700 font-bold flex items-center gap-1.5">
              <span>tun0: 0% DROPS</span>
              <span className="text-slate-400">•</span>
              <span>IPv6 GUARD ON</span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
