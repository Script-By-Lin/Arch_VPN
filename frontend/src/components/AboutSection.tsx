"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { 
  ShieldCheck, 
  Cpu, 
  Lock, 
  Zap, 
  Globe2, 
  Layers, 
  Radio, 
  KeyRound, 
  Sliders, 
  Server,
  ArrowUpRight,
  CheckCircle2
} from "lucide-react";

export default function AboutSection() {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const features = [
    {
      icon: KeyRound,
      title: "ssconf:// Subscription Engine",
      tag: "Auto-Parser",
      color: "from-cyan-500 to-blue-600",
      glow: "rgba(0, 229, 255, 0.2)",
      metric: "JSON Schema Validated",
      description: "Directly fetches, decodes, and validates Shadowsocks subscription URLs. Automatically detects expired node packages, maps local ports, and injects configuration profiles into your local store."
    },
    {
      icon: Layers,
      title: "Full-System Kernel TUN (tun0)",
      tag: "Layer 3 Routing",
      color: "from-purple-500 to-indigo-600",
      glow: "rgba(139, 92, 246, 0.2)",
      metric: "100% TCP/UDP Captured",
      description: "Unlike browser-only SOCKS5 proxies, AuraLink provisions a real Layer-3 tun0 network interface. All system traffic—including games, terminal commands, Docker, and background daemons—is transparently captured."
    },
    {
      icon: Lock,
      title: "Anti-Censorship & TLS Prefixes",
      tag: "DPI Bypass",
      color: "from-emerald-500 to-teal-600",
      glow: "rgba(0, 230, 118, 0.2)",
      metric: "TLS 1.2/1.3 Handshake Disguise",
      description: "Equipped with Shadowsocks-Rust packet prefixes, disguise headers (TLS handshakes), AEAD ciphers (ChaCha20-Poly1305, AES-256-GCM), and UDP relay to evade active state-level Deep Packet Inspection."
    },
    {
      icon: ShieldCheck,
      title: "Zero-Leak DNS & IPv6 Protection",
      tag: "Systemd Guard",
      color: "from-amber-500 to-orange-600",
      glow: "rgba(245, 158, 11, 0.2)",
      metric: "resolvectl domain tun0 '~.'",
      description: "Integrates with systemd-resolved and resolvectl domain tun0 '~.' to establish a wildcard domain sinkhole. Drops default IPv6 routes to prevent dual-stack IP and DNS leakage."
    },
    {
      icon: Radio,
      title: "Physical Gateway Route Pinning",
      tag: "Loop Prevention",
      color: "from-pink-500 to-rose-600",
      glow: "rgba(244, 63, 94, 0.2)",
      metric: "Automatic Route Host Pin",
      description: "Dynamically inspects the Linux kernel route table, isolates your physical gateway (e.g. 192.168.1.1 via wlan0), and pins the remote server route to eliminate infinite tunnel routing loops."
    },
    {
      icon: Sliders,
      title: "PyQt5 Dark GUI + Headless CLI",
      tag: "Dual Modality",
      color: "from-cyan-400 to-emerald-400",
      glow: "rgba(0, 229, 255, 0.2)",
      metric: "GUI Tray + Bash CLI Automation",
      description: "Enjoy a rich dark-mode desktop GUI featuring a glowing circular connect button, live speed counters, ping latency testing, DNS picker, and system tray minimization, or manage everything headlessly via CLI."
    }
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.12,
        delayChildren: 0.1
      }
    }
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 30, scale: 0.95 },
    visible: { 
      opacity: 1, 
      y: 0, 
      scale: 1,
      transition: { duration: 0.5, ease: "easeOut" as const } 
    }
  };

  return (
    <section id="about" className="py-20 md:py-28 relative overflow-hidden">
      {/* Ambient background glow orbs */}
      <div className="absolute top-1/3 -left-32 w-96 h-96 bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-purple-600/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        
        {/* Section Header with smooth entrance animation */}
        <motion.div
          initial={{ opacity: 0, y: 25 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 0.6 }}
          className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-6"
        >
          <div className="max-w-2xl">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4 }}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-cyan-300 text-xs font-semibold uppercase tracking-wider mb-3 shadow-lg shadow-cyan-950/30"
            >
              <Zap className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
              <span>Engineered for Linux Power Users</span>
            </motion.div>

            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight leading-tight">
              Why AuraLink is{" "}
              <span className="bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-400 bg-clip-text text-transparent">
                Built Different
              </span>
            </h2>

            <p className="mt-4 text-slate-300 text-base sm:text-lg leading-relaxed">
              Standard proxies require per-app configuration and leak DNS queries. AuraLink bridges the gap between lightweight Shadowsocks encryption and full-system VPN tunneling.
            </p>
          </div>

          <motion.div
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            className="flex-shrink-0 flex items-center gap-3"
          >
            <a
              href="#user-guide"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold text-cyan-300 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 hover:border-cyan-400/60 shadow-lg shadow-cyan-950/20 transition-all"
            >
              <span>Explore User Guide</span>
              <ArrowUpRight className="w-4 h-4" />
            </a>
          </motion.div>
        </motion.div>

        {/* Feature Grid with Animated Stagger and Hover Interaction */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-60px" }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {features.map((feature, idx) => {
            const isHovered = hoveredIndex === idx;
            return (
              <motion.div
                key={feature.title}
                variants={cardVariants}
                onMouseEnter={() => setHoveredIndex(idx)}
                onMouseLeave={() => setHoveredIndex(null)}
                whileHover={{ y: -8, transition: { duration: 0.25, ease: "easeOut" } }}
                className="relative rounded-3xl bg-[#0c101a]/85 border border-white/[0.08] hover:border-cyan-400/50 p-6 sm:p-7 shadow-xl shadow-cyan-950/20 hover:shadow-cyan-500/15 transition-all duration-300 group overflow-hidden flex flex-col justify-between"
              >
                {/* Dynamic animated glow backing on hover */}
                <motion.div
                  animate={{
                    opacity: isHovered ? 0.8 : 0.2,
                    scale: isHovered ? 1.2 : 1
                  }}
                  transition={{ duration: 0.4 }}
                  className="absolute top-0 right-0 w-40 h-40 rounded-full blur-3xl pointer-events-none"
                  style={{ background: feature.glow }}
                />

                <div>
                  <div className="flex items-center justify-between mb-5">
                    {/* Animated Icon Container */}
                    <motion.div
                      whileHover={{ rotate: [0, -8, 8, 0], scale: 1.1 }}
                      transition={{ duration: 0.4 }}
                      className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${feature.color} p-2.5 flex items-center justify-center text-white shadow-lg`}
                    >
                      <feature.icon className="w-6 h-6" />
                    </motion.div>

                    <span className="text-[11px] font-mono font-medium px-2.5 py-0.5 rounded-full bg-white/[0.05] text-slate-300 border border-white/[0.08] group-hover:border-cyan-500/30 group-hover:text-cyan-300 transition-colors">
                      {feature.tag}
                    </span>
                  </div>

                  <h3 className="text-xl font-bold text-white mb-2 group-hover:text-cyan-300 transition-colors duration-200">
                    {feature.title}
                  </h3>

                  <p className="text-slate-400 text-sm leading-relaxed mb-4">
                    {feature.description}
                  </p>
                </div>

                {/* Bottom Micro Metric Tag with Pulse */}
                <div className="pt-4 border-t border-white/[0.06] flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5 text-[11px] font-mono text-cyan-300/90">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>{feature.metric}</span>
                  </div>
                  <motion.div
                    animate={{ scale: isHovered ? [1, 1.25, 1] : 1 }}
                    transition={{ duration: 1, repeat: isHovered ? Infinity : 0 }}
                    className="w-2 h-2 rounded-full bg-cyan-400"
                  />
                </div>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Deep Tech Highlights Ribbon with Stagger Animation */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-40px" }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mt-14 rounded-3xl bg-gradient-to-r from-cyan-950/40 via-[#0a0e1a]/80 to-purple-950/40 border border-white/[0.08] p-6 sm:p-8 backdrop-blur-xl shadow-2xl"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center md:text-left">
            <motion.div 
              whileHover={{ scale: 1.02 }}
              className="flex items-start gap-4 p-3 rounded-2xl transition-all"
            >
              <div className="w-10 h-10 rounded-xl bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-300 flex-shrink-0 shadow-lg shadow-cyan-950/40">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-white font-semibold text-sm flex items-center gap-2">
                  <span>Zero Polling Overhead</span>
                </h4>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  Polls Linux ProcFS (<code className="font-mono text-cyan-300">/proc/net/dev</code>) directly for hardware-speed byte telemetry without CPU spikes.
                </p>
              </div>
            </motion.div>

            <motion.div 
              whileHover={{ scale: 1.02 }}
              className="flex items-start gap-4 p-3 rounded-2xl transition-all"
            >
              <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-300 flex-shrink-0 shadow-lg shadow-emerald-950/40">
                <Server className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-white font-semibold text-sm">Direct TCP SYN/ACK Probing</h4>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  Accurate millisecond latency testing using raw socket TCP handshakes directly to proxy endpoints.
                </p>
              </div>
            </motion.div>

            <motion.div 
              whileHover={{ scale: 1.02 }}
              className="flex items-start gap-4 p-3 rounded-2xl transition-all"
            >
              <div className="w-10 h-10 rounded-xl bg-purple-500/15 border border-purple-500/30 flex items-center justify-center text-purple-300 flex-shrink-0 shadow-lg shadow-purple-950/40">
                <Globe2 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-white font-semibold text-sm">Multi-DNS Upstream Selection</h4>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  Switch between Cloudflare (1.1.1.1), Google (8.8.8.8), Quad9 (9.9.9.9), and AdGuard (94.140.14.14) with zero DNS leaks.
                </p>
              </div>
            </motion.div>
          </div>
        </motion.div>

      </div>
    </section>
  );
}
