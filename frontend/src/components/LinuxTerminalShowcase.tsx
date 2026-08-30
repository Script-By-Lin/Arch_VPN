"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Terminal, Activity, ShieldCheck, Sparkles, Layers } from "lucide-react";

export default function LinuxTerminalShowcase() {
  const [activeTab, setActiveTab] = useState<"fastfetch" | "dmesg" | "iproute">("fastfetch");
  const [typedCommand, setTypedCommand] = useState("");
  const [cursorVisible, setCursorVisible] = useState(true);

  // Blinking cursor
  useEffect(() => {
    const interval = setInterval(() => {
      setCursorVisible((v) => !v);
    }, 530);
    return () => clearInterval(interval);
  }, []);

  // Command typing simulation
  useEffect(() => {
    const targetCommand = 
      activeTab === "fastfetch" 
        ? "fastfetch --structure Title:OS:Kernel:Uptime:Packages:Shell:DE:Terminal:Network"
        : activeTab === "dmesg"
        ? "sudo dmesg -w --facility=daemon,kern | grep -E 'tun|shadowtun|sslocal'"
        : "ip -brief address show && ip route show default";

    setTypedCommand("");
    let idx = 0;
    const typing = setInterval(() => {
      if (idx < targetCommand.length) {
        setTypedCommand(targetCommand.slice(0, idx + 1));
        idx++;
      } else {
        clearInterval(typing);
      }
    }, 22);

    return () => clearInterval(typing);
  }, [activeTab]);

  return (
    <section id="kernel-integration" className="py-16 md:py-24 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/3 -right-32 w-96 h-96 bg-purple-600/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-6"
        >
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-cyan-300 text-xs font-semibold uppercase tracking-wider mb-3">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span>Native Linux Subsystem & Architecture</span>
            </div>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight">
              Deep Kernel Integration
            </h2>
            <p className="mt-3 text-slate-300 text-sm sm:text-base max-w-2xl leading-relaxed">
              Real-time visualization of the Linux kernel network stack, TUN virtual interface provisioning, and system routing telemetry.
            </p>
          </div>

          {/* Interactive Mode Switcher */}
          <div className="flex items-center gap-2 bg-[#0c101a] p-1.5 rounded-2xl border border-white/[0.08]">
            {[
              { id: "fastfetch", label: "Fastfetch HUD", icon: Terminal },
              { id: "dmesg", label: "Kernel dmesg", icon: Activity },
              { id: "iproute", label: "ip route & tun0", icon: Layers },
            ].map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-mono font-medium transition-all cursor-pointer ${
                    isActive
                      ? "bg-cyan-500/20 text-cyan-300 border border-cyan-400/40 shadow-lg shadow-cyan-950/40"
                      : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]"
                  }`}
                >
                  <tab.icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </motion.div>

        {/* The Animated Terminal Window */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="rounded-3xl bg-[#080b12] border border-cyan-500/25 shadow-2xl shadow-cyan-950/30 overflow-hidden font-mono"
        >
          {/* Terminal Window Header Bar */}
          <div className="px-5 py-3.5 bg-[#0e1320] border-b border-white/[0.08] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-rose-500/80 shadow-sm" />
              <div className="w-3 h-3 rounded-full bg-amber-500/80 shadow-sm" />
              <div className="w-3 h-3 rounded-full bg-emerald-500/80 shadow-sm" />
              <span className="text-xs text-slate-400 ml-2 font-mono">
                bit@cachyos-arch: ~/shadowtun
              </span>
            </div>

            <div className="flex items-center gap-3 text-xs text-slate-400">
              <span className="hidden sm:inline-block text-[11px] text-emerald-400 font-semibold">
                ● KERNEL ACTIVE: 6.12.9-cachyos
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-black/60 text-cyan-300 border border-white/[0.06]">
                bash 5.2.37
              </span>
            </div>
          </div>

          {/* Terminal Body with Prompt & Active Animation */}
          <div className="p-6 sm:p-8 space-y-6 text-xs sm:text-sm leading-relaxed overflow-x-auto min-h-[340px] bg-[#07090e]/95">
            
            {/* Active Command Prompt Line */}
            <div className="flex items-center gap-2 text-slate-300 flex-wrap">
              <span className="text-emerald-400 font-bold">bit@cachyos</span>
              <span className="text-slate-500">:</span>
              <span className="text-cyan-400 font-semibold">~/shadowtun</span>
              <span className="text-slate-400">$</span>
              <span className="text-white font-mono">{typedCommand}</span>
              <span className={`w-2 h-4 bg-cyan-400 ${cursorVisible ? "opacity-100" : "opacity-0"}`} />
            </div>

            {/* TAB 1: FASTFETCH LINUX HUD */}
            {activeTab === "fastfetch" && (
              <motion.div
                key="fastfetch"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
                className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center pt-2"
              >
                {/* ASCII Art Logo (Arch / ShadowTun Tux) */}
                <div className="md:col-span-5 text-cyan-400 font-mono text-xs sm:text-sm leading-tight select-none">
                  <pre className="text-cyan-300 drop-shadow-[0_0_12px_rgba(0,229,255,0.4)]">
{`       /\\         ShadowTun Linux
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

                {/* Live System & Tunneling Metrics */}
                <div className="md:col-span-7 space-y-2.5 bg-black/40 p-4 sm:p-5 rounded-2xl border border-white/[0.06]">
                  <div className="flex justify-between items-center text-xs pb-1 border-b border-white/[0.06]">
                    <span className="text-slate-400">Virtual TUN Interface:</span>
                    <span className="text-emerald-400 font-bold">tun0 (10.0.0.2/24) • MTU 1500</span>
                  </div>
                  <div className="flex justify-between items-center text-xs pb-1 border-b border-white/[0.06]">
                    <span className="text-slate-400">Default Route:</span>
                    <span className="text-cyan-300 font-semibold">default dev tun0 (100% Routed)</span>
                  </div>
                  <div className="flex justify-between items-center text-xs pb-1 border-b border-white/[0.06]">
                    <span className="text-slate-400">DNS Sinkhole:</span>
                    <span className="text-purple-300 font-semibold">systemd-resolved (~. wildcard)</span>
                  </div>
                  <div className="flex justify-between items-center text-xs pb-1 border-b border-white/[0.06]">
                    <span className="text-slate-400">Shadowsocks Core:</span>
                    <span className="text-amber-300 font-semibold">shadowsocks-rust 1.20 (sslocal)</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-400">Active AEAD Cipher:</span>
                    <span className="text-emerald-300 font-mono">chacha20-ietf-poly1305 + TLS Prefix</span>
                  </div>

                  {/* Visual memory/buffer bar */}
                  <div className="pt-2">
                    <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                      <span>Kernel Ring Buffer Allocation</span>
                      <span className="text-cyan-300">0.02% (Zero Overhead)</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <motion.div
                        initial={{ width: "0%" }}
                        animate={{ width: "38%" }}
                        transition={{ duration: 1 }}
                        className="h-full bg-gradient-to-r from-cyan-400 to-emerald-400"
                      />
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* TAB 2: KERNEL DMESG STREAM */}
            {activeTab === "dmesg" && (
              <motion.div
                key="dmesg"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
                className="space-y-1.5 text-xs font-mono text-slate-300"
              >
                <div className="text-slate-500">[    0.000000] Linux version 6.12.9-cachyos (gcc 14.2.1) #1 SMP PREEMPT_DYNAMIC</div>
                <div className="text-slate-400">[    1.102840] <span className="text-cyan-300">tun:</span> Universal TUN/TAP device driver, 1.6</div>
                <div className="text-slate-400">[    1.102842] <span className="text-cyan-300">tun:</span> (C) 1999-2002 Maxim Krasnyansky &lt;maxk@qualcomm.com&gt;</div>
                <div className="text-emerald-400">[   42.189201] shadowtun[1204]: privileged helper executing /usr/local/bin/vpn-core-helper</div>
                <div className="text-cyan-300">[   42.204510] tun0: link becomes ready, MTU set to 1500</div>
                <div className="text-emerald-400">[   42.215090] tun2socks[1210]: device=tun0, proxy=socks5://127.0.0.1:1080, mtu=1500</div>
                <div className="text-purple-300">[   42.228940] sslocal[1209]: listening TCP/UDP on 127.0.0.1:1080 (AEAD chacha20-poly1305)</div>
                <div className="text-amber-300">[   42.240105] iproute2: route replace 198.51.100.42/32 via 192.168.1.1 dev wlan0 (pinned)</div>
                <div className="text-cyan-300">[   42.251400] systemd-resolved[450]: Using DNS server 1.1.1.1 for interface tun0 (~.)</div>
                <div className="text-emerald-400 font-bold">[   42.260800] shadowtun: full-tunnel connection established. Zero packet leaks.</div>
              </motion.div>
            )}

            {/* TAB 3: IP ROUTE & INTERFACE INSPECTOR */}
            {activeTab === "iproute" && (
              <motion.div
                key="iproute"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
                className="space-y-4 text-xs font-mono"
              >
                <div className="p-4 rounded-xl bg-black/60 border border-white/[0.06] space-y-2">
                  <div className="text-slate-400 text-[11px] font-semibold uppercase tracking-wider">
                    # ip -brief address show
                  </div>
                  <div className="text-slate-300">lo               UNKNOWN        127.0.0.1/8 ::1/128</div>
                  <div className="text-slate-300">wlan0            UP             192.168.1.145/24 fe80::a00:27ff:fe4e:66a1/64</div>
                  <div className="text-emerald-400 font-bold">tun0             UP             10.0.0.2/24</div>
                </div>

                <div className="p-4 rounded-xl bg-black/60 border border-white/[0.06] space-y-2">
                  <div className="text-slate-400 text-[11px] font-semibold uppercase tracking-wider">
                    # ip route show
                  </div>
                  <div className="text-emerald-400 font-bold">default dev tun0 scope link</div>
                  <div className="text-cyan-300">10.0.0.0/24 dev tun0 proto kernel scope link src 10.0.0.2</div>
                  <div className="text-amber-300">198.51.100.42 via 192.168.1.1 dev wlan0 proto static (PINNED PROXY)</div>
                  <div className="text-slate-400">192.168.1.0/24 dev wlan0 proto kernel scope link src 192.168.1.145</div>
                </div>
              </motion.div>
            )}

          </div>

          {/* Terminal Status Bar */}
          <div className="px-5 py-2.5 bg-[#0a0e17] border-t border-white/[0.06] flex items-center justify-between text-[11px] text-slate-400">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Layer 3 Subsystem Integrity: OK</span>
            </div>
            <div className="font-mono text-cyan-400 flex items-center gap-1.5">
              <span>tun0: 0% DROPS</span>
              <span className="text-slate-600">•</span>
              <span>100% ROUTED</span>
            </div>
          </div>
        </motion.div>

      </div>
    </section>
  );
}
