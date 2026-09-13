"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Terminal, Shield, Zap, ArrowRight, Lock, Activity, Globe } from "lucide-react";

export default function Hero() {
  const fullText = "Universal Shadowsocks & tun2socks VPN for Linux";
  const [charCount, setCharCount] = useState(0);

  useEffect(() => {
    let current = 0;
    const interval = setInterval(() => {
      if (current < fullText.length) {
        current++;
        setCharCount(current);
      } else {
        clearInterval(interval);
      }
    }, 45);
    return () => clearInterval(interval);
  }, []);

  // Compute text slices
  const part1 = fullText.slice(0, Math.min(charCount, 24)); // "Universal Shadowsocks & "
  const part2 = charCount > 24 ? fullText.slice(24, Math.min(charCount, 37)) : ""; // "tun2socks VPN"
  const part3 = charCount > 37 ? fullText.slice(37, charCount) : ""; // " for Linux"

  return (
    <section className="relative pt-32 pb-20 md:pt-40 md:pb-28 overflow-hidden cyber-radial">
      {/* Background cyber grid & glow accents */}
      <div className="absolute inset-0 cyber-grid opacity-40 pointer-events-none" />
      <div className="scanline pointer-events-none opacity-20" />
      
      {/* Glowing atmospheric orbs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[500px] bg-gradient-to-tr from-cyan-500/15 via-purple-600/10 to-emerald-500/10 blur-[140px] pointer-events-none -z-10" />

      <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="flex flex-col items-center text-center max-w-6xl mx-auto">
          
          {/* Robot Avatar & Top Pill Badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="flex flex-col items-center mb-6"
          >
            <div className="relative mb-4 group cursor-pointer">
              <div className="absolute -inset-1.5 bg-gradient-to-r from-cyan-500 via-teal-400 to-purple-600 rounded-full blur-md opacity-75 group-hover:opacity-100 transition duration-500 animate-pulse" />
              <div className="relative w-24 h-24 sm:w-28 sm:h-28 rounded-full overflow-hidden border-2 border-cyan-400/80 shadow-2xl bg-[#090d16] p-1">
                <img
                  src="/icon.png"
                  alt="AuraLink Robot Mascot"
                  className="w-full h-full object-cover rounded-full group-hover:scale-105 transition-transform duration-300"
                />
              </div>
            </div>

            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-semibold tracking-wide shadow-lg shadow-cyan-950/40">
              <Zap className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
              <span>AURALINK LINUX TUNNELING ENGINE • ARCH, DEBIAN, FEDORA & RPM</span>
            </div>
          </motion.div>

          {/* Main Title with Typing Animation */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-[1.12] mb-6 min-h-[96px] sm:min-h-[120px] md:min-h-[144px] flex items-center justify-center flex-wrap whitespace-pre-wrap text-center max-w-5xl"
          >
            <span>{part1}</span>
            {part2 && (
              <span className="bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-400 bg-clip-text text-transparent">
                {part2}
              </span>
            )}
            {charCount > 37 && <span>{" "}</span>}
            {part3 && <span>{part3.trimStart()}</span>}
            <motion.span
              animate={{ opacity: [1, 0, 1] }}
              transition={{ repeat: Infinity, duration: 0.8, ease: "linear" }}
              className="inline-block w-1.5 h-8 sm:h-11 md:h-14 bg-cyan-400 ml-2 align-middle rounded-full shadow-[0_0_8px_#00e5ff]"
            />
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-base sm:text-lg md:text-xl text-slate-300 max-w-4xl mb-8 leading-relaxed font-normal"
          >
            Turn any Shadowsocks proxy subscription into a full-system TUN virtual network interface (<code className="font-mono text-cyan-300 text-sm px-1.5 py-0.5 rounded bg-slate-800/80 border border-cyan-500/20">tun0</code>). 
            Route all TCP, UDP, and DNS traffic securely with automatic TLS disguise prefixes and zero leaks.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto mb-14"
          >
            <a
              href="#downlink"
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl font-semibold text-sm text-black bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-400 hover:from-cyan-300 hover:to-emerald-300 shadow-xl shadow-cyan-500/25 hover:shadow-cyan-400/35 transition-all flex items-center justify-center gap-2 group"
            >
              <Terminal className="w-4 h-4 text-black group-hover:scale-110 transition-transform" />
              <span>Get 1-Line Install Command</span>
              <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
            </a>

            <a
              href="#user-guide"
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl font-semibold text-sm text-slate-200 bg-slate-900/80 hover:bg-slate-800/90 border border-white/10 hover:border-cyan-500/40 shadow-lg transition-all flex items-center justify-center gap-2"
            >
              <Shield className="w-4 h-4 text-cyan-400" />
              <span>Explore User Guide</span>
            </a>
          </motion.div>

          {/* Quick Metrics & Badges Grid */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5 w-full max-w-5xl lg:max-w-6xl mb-12"
          >
            <div className="glass-panel p-5 rounded-2xl text-left border border-white/[0.08] hover:border-cyan-500/40 hover:bg-[#0c101a]/90 transition-all shadow-lg">
              <div className="flex items-center gap-2 text-cyan-400 text-xs font-mono mb-1.5">
                <Lock className="w-4 h-4" />
                <span className="font-semibold">ANTI-DPI</span>
              </div>
              <div className="text-xl font-bold text-white">TLS Prefix</div>
              <div className="text-xs text-slate-400 mt-0.5">Camouflaged handshake</div>
            </div>

            <div className="glass-panel p-5 rounded-2xl text-left border border-white/[0.08] hover:border-emerald-500/40 hover:bg-[#0c101a]/90 transition-all shadow-lg">
              <div className="flex items-center gap-2 text-emerald-400 text-xs font-mono mb-1.5">
                <Shield className="w-4 h-4" />
                <span className="font-semibold">DNS GUARD</span>
              </div>
              <div className="text-xl font-bold text-white">0% Leaks</div>
              <div className="text-xs text-slate-400 mt-0.5">systemd-resolved bound</div>
            </div>

            <div className="glass-panel p-5 rounded-2xl text-left border border-white/[0.08] hover:border-purple-500/40 hover:bg-[#0c101a]/90 transition-all shadow-lg">
              <div className="flex items-center gap-2 text-purple-400 text-xs font-mono mb-1.5">
                <Activity className="w-4 h-4" />
                <span className="font-semibold">KERNEL TUN</span>
              </div>
              <div className="text-xl font-bold text-white">tun0 Layer 3</div>
              <div className="text-xs text-slate-400 mt-0.5">Full system routing</div>
            </div>

            <div className="glass-panel p-5 rounded-2xl text-left border border-white/[0.08] hover:border-amber-500/40 hover:bg-[#0c101a]/90 transition-all shadow-lg">
              <div className="flex items-center gap-2 text-amber-400 text-xs font-mono mb-1.5">
                <Globe className="w-4 h-4" />
                <span className="font-semibold">SUBSCRIPTIONS</span>
              </div>
              <div className="text-xl font-bold text-white">ssconf://</div>
              <div className="text-xs text-slate-400 mt-0.5">Instant key parsing</div>
            </div>
          </motion.div>

          {/* Animated Linux Distro Compatibility Ribbon */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="flex flex-wrap items-center justify-center gap-2.5 sm:gap-3.5 text-xs font-mono text-slate-300 max-w-5xl"
          >
            {[
              { name: "Linux Kernel 5.x/6.x", icon: "🐧" },
              { name: "Arch Linux", icon: "🏹" },
              { name: "CachyOS", icon: "⚡" },
              { name: "Debian / Ubuntu", icon: "🍥" },
              { name: "Fedora / RPM", icon: "🎩" },
              { name: "openSUSE", icon: "🦎" },
              { name: "systemd-resolved", icon: "🔒" },
            ].map((distro) => (
              <motion.span
                key={distro.name}
                whileHover={{ y: -3, scale: 1.05 }}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-[#0c101a]/90 border border-white/[0.08] hover:border-cyan-400/50 hover:text-cyan-200 transition-all shadow-md cursor-default"
              >
                <span>{distro.icon}</span>
                <span>{distro.name}</span>
              </motion.span>
            ))}
          </motion.div>

        </div>
      </div>
    </section>
  );
}
