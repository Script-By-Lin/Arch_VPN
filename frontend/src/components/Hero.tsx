"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Terminal, Shield, Zap, ArrowRight, Lock, Activity, Globe, Network } from "lucide-react";

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
    }, 36);
    return () => clearInterval(interval);
  }, []);

  const part1 = fullText.slice(0, Math.min(charCount, 24));
  const part2 = charCount > 24 ? fullText.slice(24, Math.min(charCount, 37)) : "";
  const part3 = charCount > 37 ? fullText.slice(37, charCount) : "";

  const metrics = [
    {
      icon: Lock,
      tag: "ANTI-DPI",
      title: "TLS Prefix",
      desc: "Camouflaged handshake",
      accent: "text-sky-600",
      bg: "bg-sky-50 border-sky-200/80",
      hover: "hover:border-sky-400/70",
    },
    {
      icon: Shield,
      tag: "ZERO LEAKS",
      title: "DNS & IPv6 Guard",
      desc: "resolvectl + sysctl kill",
      accent: "text-emerald-600",
      bg: "bg-emerald-50 border-emerald-200/80",
      hover: "hover:border-emerald-400/70",
    },
    {
      icon: Activity,
      tag: "KERNEL TUN",
      title: "tun0 Layer 3",
      desc: "Full system routing",
      accent: "text-indigo-600",
      bg: "bg-indigo-50 border-indigo-200/80",
      hover: "hover:border-indigo-400/70",
    },
    {
      icon: Globe,
      tag: "SUBSCRIPTIONS",
      title: "ssconf://",
      desc: "Instant key parsing",
      accent: "text-amber-600",
      bg: "bg-amber-50 border-amber-200/80",
      hover: "hover:border-amber-400/70",
    },
  ];

  return (
    <section className="relative pt-32 pb-20 md:pt-40 md:pb-24 overflow-hidden cyber-radial">
      {/* Subtle architectural blueprint grid */}
      <div className="absolute inset-0 cyber-grid opacity-70 pointer-events-none" />
      <div className="scanline pointer-events-none opacity-40" />

      {/* Animated soft daylight atmospheric blobs */}
      <motion.div
        animate={{ x: [0, 30, 0], y: [0, -20, 0] }}
        transition={{ duration: 11, repeat: Infinity, ease: "easeInOut" }}
        className="absolute top-12 left-1/4 w-[480px] h-[360px] bg-sky-300/25 rounded-full blur-[110px] pointer-events-none -z-10"
      />
      <motion.div
        animate={{ x: [0, -35, 0], y: [0, 25, 0] }}
        transition={{ duration: 13, repeat: Infinity, ease: "easeInOut" }}
        className="absolute top-24 right-1/5 w-[440px] h-[340px] bg-emerald-300/20 rounded-full blur-[110px] pointer-events-none -z-10"
      />

      <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="flex flex-col items-center text-center max-w-6xl mx-auto">
          {/* Top Pill Badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.45 }}
            className="flex flex-col items-center mb-6"
          >
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/90 border border-sky-200 text-sky-700 text-xs font-bold tracking-wide shadow-sm">
              <Zap className="w-3.5 h-3.5 text-sky-500 animate-pulse" />
              <span>AURALINK LINUX TUNNELING ENGINE • ARCH, DEBIAN, FEDORA & RPM</span>
            </div>
          </motion.div>

          {/* Main Title with Typing Animation */}
          <motion.h1
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.08 }}
            className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight text-slate-900 leading-[1.12] mb-6 min-h-[96px] sm:min-h-[120px] md:min-h-[144px] flex items-center justify-center flex-wrap whitespace-pre-wrap text-center max-w-5xl"
          >
            <span>{part1}</span>
            {part2 && (
              <span className="bg-gradient-to-r from-sky-600 via-teal-600 to-emerald-600 bg-clip-text text-transparent">
                {part2}
              </span>
            )}
            {charCount > 37 && <span>{" "}</span>}
            {part3 && <span>{part3.trimStart()}</span>}
            <motion.span
              animate={{ opacity: [1, 0, 1] }}
              transition={{ repeat: Infinity, duration: 0.8, ease: "linear" }}
              className="inline-block w-1.5 h-8 sm:h-11 md:h-14 bg-sky-500 ml-2 align-middle rounded-full"
            />
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.16 }}
            className="text-base sm:text-lg md:text-xl text-slate-600 max-w-4xl mb-8 leading-relaxed"
          >
            Turn any Shadowsocks proxy subscription into a full-system TUN virtual network interface (
            <code className="font-mono text-sky-700 text-sm px-2 py-0.5 rounded-md bg-sky-50 border border-sky-200 font-semibold">
              tun0
            </code>
            ). Route all TCP, UDP, and DNS traffic securely with automatic TLS disguise prefixes, kernel IPv6 leak blocking, and zero leaks.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.24 }}
            className="flex flex-col sm:flex-row items-center gap-3.5 w-full sm:w-auto mb-14"
          >
            <motion.a
              whileHover={{ y: -2, scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              href="#downlink"
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl font-bold text-sm text-white bg-gradient-to-r from-sky-600 via-teal-600 to-emerald-600 hover:from-sky-500 hover:to-emerald-500 shadow-lg shadow-sky-600/20 transition-all flex items-center justify-center gap-2 group"
            >
              <Terminal className="w-4 h-4 text-white group-hover:scale-110 transition-transform" />
              <span>Get 1-Line Install Command</span>
              <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
            </motion.a>

            <motion.a
              whileHover={{ y: -2, scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              href="#architecture"
              className="w-full sm:w-auto px-7 py-3.5 rounded-xl font-bold text-sm text-slate-800 bg-white hover:bg-sky-50 border border-slate-200 hover:border-sky-300 shadow-sm transition-all flex items-center justify-center gap-2"
            >
              <Network className="w-4 h-4 text-sky-600" />
              <span>Explore Interactive Model</span>
            </motion.a>
          </motion.div>

          {/* Quick Metrics & Badges Grid */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.32 }}
            className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5 w-full max-w-5xl lg:max-w-6xl mb-12"
          >
            {metrics.map((m, idx) => (
              <motion.div
                key={m.tag}
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.32 + idx * 0.06 }}
                whileHover={{ y: -4, scale: 1.015 }}
                className={`glass-panel p-5 rounded-2xl text-left transition-all ${m.hover}`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className={`inline-flex items-center gap-1.5 text-xs font-mono font-bold ${m.accent}`}>
                    <span className={`p-1.5 rounded-lg border ${m.bg}`}>
                      <m.icon className="w-3.5 h-3.5" />
                    </span>
                    <span>{m.tag}</span>
                  </div>
                </div>
                <div className="text-xl font-extrabold text-slate-900">{m.title}</div>
                <div className="text-xs text-slate-500 mt-0.5">{m.desc}</div>
              </motion.div>
            ))}
          </motion.div>

          {/* Animated Linux Distro Compatibility Ribbon */}
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.55, delay: 0.42 }}
            className="flex flex-wrap items-center justify-center gap-2.5 sm:gap-3 text-xs font-mono text-slate-700 max-w-5xl"
          >
            {[
              { name: "Linux Kernel 5.x/6.x", icon: "🐧" },
              { name: "Arch Linux", icon: "🏹" },
              { name: "CachyOS", icon: "⚡" },
              { name: "Debian / Ubuntu", icon: "🍥" },
              { name: "Fedora / RPM", icon: "🎩" },
              { name: "openSUSE", icon: "🦎" },
              { name: "IPv6 Leak Shield", icon: "🛡️" },
            ].map((distro) => (
              <motion.span
                key={distro.name}
                whileHover={{ y: -3, scale: 1.04 }}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white/90 border border-slate-200 hover:border-sky-400 hover:text-sky-700 transition-all shadow-xs cursor-default font-medium"
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
