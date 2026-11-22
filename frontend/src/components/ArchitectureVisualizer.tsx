"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ARCH_NODES, ArchNode } from "@/data/appData";
import {
  ArrowRight,
  Terminal,
  Activity,
  Network,
  ShieldCheck,
  ShieldAlert,
  Play,
  Pause,
  Lock,
  Unlock,
  Gauge,
  Radio,
} from "lucide-react";

const SVG_NODES = [
  { id: "apps", x: 95, y: 130, label: "Linux Apps", sub: "TCP / UDP / DNS" },
  { id: "kernel", x: 265, y: 130, label: "tun0 (L3)", sub: "10.0.0.2/24" },
  { id: "tun2socks", x: 435, y: 130, label: "tun2socks", sub: "Go Bridge" },
  { id: "sslocal", x: 605, y: 130, label: "sslocal", sub: "AEAD + TLS" },
  { id: "physical", x: 775, y: 130, label: "wlan0 / eth0", sub: "Pinned /32" },
  { id: "server", x: 945, y: 130, label: "VPN Node", sub: "Encrypted WAN" },
];

export default function ArchitectureVisualizer() {
  const [selectedNode, setSelectedNode] = useState<ArchNode>(ARCH_NODES[1]);
  const [tunnelActive, setTunnelActive] = useState(true);
  const [ipv6Blocked, setIpv6Blocked] = useState(true);
  const [antiDpiEnabled, setAntiDpiEnabled] = useState(true);
  const [isPlaying, setIsPlaying] = useState(true);
  const [fastMode, setFastMode] = useState(false);

  const flowDuration = fastMode ? 1.3 : 2.4;

  const selectById = (id: string) => {
    const match = ARCH_NODES.find((n) => n.id === id);
    if (match) setSelectedNode(match);
  };

  return (
    <section
      id="architecture"
      className="py-20 md:py-28 relative bg-gradient-to-b from-[#f8fafc] via-white to-[#f1f5f9] border-y border-slate-200/80 overflow-hidden"
    >
      {/* Subtle decorative rings */}
      <div className="absolute -top-24 right-1/4 w-96 h-96 bg-sky-200/30 rounded-full blur-[110px] pointer-events-none" />
      <div className="absolute -bottom-24 left-1/4 w-96 h-96 bg-indigo-200/25 rounded-full blur-[110px] pointer-events-none" />

      <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.45 }}
          className="text-center max-w-3xl mx-auto mb-12"
        >
          <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-bold uppercase tracking-wider mb-3 shadow-xs">
            <Network className="w-3.5 h-3.5 text-indigo-600" />
            <span>Interactive Packet & Kernel Model</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight">
            Live Tunnel Architecture Simulator
          </h2>
          <p className="mt-3 text-slate-600 text-sm sm:text-base">
            Toggle full-tunnel routing, kernel IPv6 leak blocking, and anti-DPI TLS prefix disguise below—then click any stage to inspect live Linux kernel calls.
          </p>
        </motion.div>

        {/* INTERACTIVE MODEL CANVAS + CONTROLS */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="max-w-6xl mx-auto mb-10 rounded-3xl bg-white border border-slate-200/90 shadow-xl shadow-slate-900/[0.05] overflow-hidden"
        >
          {/* Interactive Control Deck */}
          <div className="px-5 py-4 bg-slate-50/90 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => setTunnelActive((v) => !v)}
                className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-mono font-bold border transition-all cursor-pointer ${
                  tunnelActive
                    ? "bg-emerald-50 text-emerald-700 border-emerald-300 shadow-xs"
                    : "bg-rose-50 text-rose-700 border-rose-300"
                }`}
              >
                <Radio className={`w-3.5 h-3.5 ${tunnelActive ? "animate-pulse" : ""}`} />
                <span>Tunnel: {tunnelActive ? "ACTIVE (tun0)" : "BYPASSED"}</span>
              </button>

              <button
                onClick={() => setIpv6Blocked((v) => !v)}
                className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-mono font-bold border transition-all cursor-pointer ${
                  ipv6Blocked
                    ? "bg-sky-50 text-sky-700 border-sky-300 shadow-xs"
                    : "bg-amber-50 text-amber-800 border-amber-300"
                }`}
              >
                {ipv6Blocked ? (
                  <ShieldCheck className="w-3.5 h-3.5 text-sky-600" />
                ) : (
                  <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
                )}
                <span>IPv6 Guard: {ipv6Blocked ? "DISABLED (0 LEAKS)" : "EXPOSED"}</span>
              </button>

              <button
                onClick={() => setAntiDpiEnabled((v) => !v)}
                className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-mono font-bold border transition-all cursor-pointer ${
                  antiDpiEnabled
                    ? "bg-indigo-50 text-indigo-700 border-indigo-300 shadow-xs"
                    : "bg-slate-100 text-slate-600 border-slate-300"
                }`}
              >
                {antiDpiEnabled ? (
                  <Lock className="w-3.5 h-3.5 text-indigo-600" />
                ) : (
                  <Unlock className="w-3.5 h-3.5 text-slate-500" />
                )}
                <span>TLS Prefix: {antiDpiEnabled ? "DISGUISED" : "RAW"}</span>
              </button>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setFastMode((v) => !v)}
                className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-mono font-semibold border transition-all cursor-pointer ${
                  fastMode
                    ? "bg-sky-600 text-white border-sky-600"
                    : "bg-white text-slate-600 border-slate-200 hover:border-slate-300"
                }`}
              >
                <Gauge className="w-3.5 h-3.5" />
                <span>{fastMode ? "2x Flow" : "1x Flow"}</span>
              </button>

              <button
                onClick={() => setIsPlaying((v) => !v)}
                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-mono font-semibold bg-white text-slate-700 border border-slate-200 hover:border-sky-300 hover:text-sky-700 transition-all cursor-pointer"
              >
                {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                <span>{isPlaying ? "Pause" : "Simulate"}</span>
              </button>
            </div>
          </div>

          {/* Interactive SVG Pipeline Canvas */}
          <div className="p-4 sm:p-6 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:20px_20px] overflow-x-auto">
            <svg
              viewBox="0 0 1040 270"
              className="w-full min-w-[780px] h-auto select-none"
              role="img"
              aria-label="Interactive AuraLink Linux VPN packet flow model"
            >
              <defs>
                <linearGradient id="tunnelGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#0284c7" />
                  <stop offset="50%" stopColor="#0d9488" />
                  <stop offset="100%" stopColor="#059669" />
                </linearGradient>
                <linearGradient id="bypassGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#94a3b8" />
                  <stop offset="100%" stopColor="#ef4444" />
                </linearGradient>
              </defs>

              {/* Kernel Boundary Zone Box */}
              <rect
                x="195"
                y="42"
                width="310"
                height="165"
                rx="18"
                fill="rgba(224, 242, 254, 0.35)"
                stroke="#bae6fd"
                strokeDasharray="6 4"
                strokeWidth="1.5"
              />
              <text
                x="350"
                y="64"
                textAnchor="middle"
                className="fill-sky-700 text-[10px] font-mono font-bold"
              >
                LINUX KERNEL TUN + USERSPACE BRIDGE
              </text>

              {/* ISP / DPI Inspection Zone */}
              <rect
                x="715"
                y="42"
                width="120"
                height="165"
                rx="18"
                fill={antiDpiEnabled && tunnelActive ? "rgba(236, 253, 245, 0.45)" : "rgba(254, 243, 199, 0.5)"}
                stroke={antiDpiEnabled && tunnelActive ? "#a7f3d0" : "#fcd34d"}
                strokeDasharray="5 4"
                strokeWidth="1.5"
              />
              <text
                x="775"
                y="64"
                textAnchor="middle"
                className={`text-[10px] font-mono font-bold ${
                  antiDpiEnabled && tunnelActive ? "fill-emerald-700" : "fill-amber-700"
                }`}
              >
                {antiDpiEnabled && tunnelActive ? "DPI: TLS PASS" : "DPI: EXPOSED"}
              </text>

              {/* Primary Tunnel Connectors */}
              {SVG_NODES.slice(0, -1).map((node, i) => {
                const next = SVG_NODES[i + 1];
                return (
                  <g key={node.id}>
                    <line
                      x1={node.x + 36}
                      y1={node.y}
                      x2={next.x - 36}
                      y2={next.y}
                      stroke={tunnelActive ? "url(#tunnelGrad)" : "#cbd5e1"}
                      strokeWidth={tunnelActive ? 3 : 2}
                      strokeDasharray={tunnelActive ? undefined : "6 6"}
                    />
                    {isPlaying && tunnelActive && (
                      <>
                        <motion.circle
                          r="5"
                          fill={i >= 3 ? "#059669" : "#0284c7"}
                          initial={{ cx: node.x + 36, cy: node.y, opacity: 0.9 }}
                          animate={{
                            cx: [node.x + 36, next.x - 36],
                            opacity: [0.3, 1, 0.3],
                          }}
                          transition={{
                            duration: flowDuration * 0.45,
                            repeat: Infinity,
                            ease: "linear",
                            delay: i * 0.16,
                          }}
                        />
                        <motion.circle
                          r="10"
                          fill={i >= 3 ? "rgba(5,150,105,0.22)" : "rgba(2,132,199,0.22)"}
                          initial={{ cx: node.x + 36, cy: node.y }}
                          animate={{ cx: [node.x + 36, next.x - 36] }}
                          transition={{
                            duration: flowDuration * 0.45,
                            repeat: Infinity,
                            ease: "linear",
                            delay: i * 0.16,
                          }}
                        />
                      </>
                    )}
                  </g>
                );
              })}

              {/* Bypass Direct Arc when Tunnel is OFF */}
              {!tunnelActive && (
                <g>
                  <path
                    d="M 95 166 Q 435 255 775 166"
                    fill="none"
                    stroke="url(#bypassGrad)"
                    strokeWidth="2.5"
                    strokeDasharray="6 4"
                  />
                  <text
                    x="435"
                    y="238"
                    textAnchor="middle"
                    className="fill-rose-600 text-[11px] font-mono font-bold"
                  >
                    UNENCRYPTED DIRECT ISP ROUTE (VPN OFF)
                  </text>
                  {isPlaying && (
                    <motion.circle
                      r="5"
                      fill="#ef4444"
                      animate={{ cx: [95, 435, 775], cy: [166, 211, 166] }}
                      transition={{ duration: flowDuration, repeat: Infinity, ease: "easeInOut" }}
                    />
                  )}
                </g>
              )}

              {/* IPv6 Leak Channel Model (Bottom Left -> Kernel Shield) */}
              <g>
                <path
                  d="M 95 166 C 125 225, 225 232, 310 232 L 735 232 C 760 232, 775 205, 775 166"
                  fill="none"
                  stroke={ipv6Blocked ? "#94a3b8" : "#f59e0b"}
                  strokeWidth={ipv6Blocked ? 1.5 : 2.5}
                  strokeDasharray={ipv6Blocked ? "4 5" : "8 4"}
                  opacity={tunnelActive ? 1 : 0.35}
                />
                <rect
                  x="338"
                  y="217"
                  width="270"
                  height="28"
                  rx="14"
                  fill={ipv6Blocked ? "#ecfdf5" : "#fffbeb"}
                  stroke={ipv6Blocked ? "#6ee7b7" : "#fcd34d"}
                  strokeWidth="1.5"
                />
                <text
                  x="473"
                  y="235"
                  textAnchor="middle"
                  className={`text-[10.5px] font-mono font-bold ${
                    ipv6Blocked ? "fill-emerald-700" : "fill-amber-800"
                  }`}
                >
                  {ipv6Blocked
                    ? "IPv6 BLOCKED (disable_ipv6=1 • 0% LEAK)"
                    : "WARNING: IPv6 BYPASS LEAK PATH OPEN"}
                </text>
                {isPlaying && tunnelActive && !ipv6Blocked && (
                  <motion.circle
                    r="5"
                    fill="#f59e0b"
                    animate={{ cx: [110, 320, 660, 770], cy: [185, 232, 232, 185] }}
                    transition={{ duration: flowDuration, repeat: Infinity, ease: "linear" }}
                  />
                )}
              </g>

              {/* Clickable Interactive Topology Nodes */}
              {SVG_NODES.map((n) => {
                const isSelected = selectedNode.id === n.id;
                const arch = ARCH_NODES.find((a) => a.id === n.id);
                return (
                  <g
                    key={n.id}
                    onClick={() => selectById(n.id)}
                    className="cursor-pointer group"
                  >
                    {isSelected && (
                      <motion.circle
                        cx={n.x}
                        cy={n.y}
                        r="42"
                        fill="rgba(2, 132, 199, 0.12)"
                        stroke="#0284c7"
                        strokeWidth="1.5"
                        initial={{ scale: 0.85, opacity: 0 }}
                        animate={{ scale: [1, 1.06, 1], opacity: 1 }}
                        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                      />
                    )}
                    <circle
                      cx={n.x}
                      cy={n.y}
                      r="33"
                      fill="#ffffff"
                      stroke={isSelected ? "#0284c7" : tunnelActive ? "#10b981" : "#cbd5e1"}
                      strokeWidth={isSelected ? 3 : 2}
                    />
                    <text
                      x={n.x}
                      y={n.y + 6}
                      textAnchor="middle"
                      className="text-[20px]"
                    >
                      {arch?.icon ?? "●"}
                    </text>
                    <text
                      x={n.x}
                      y={n.y + 52}
                      textAnchor="middle"
                      className={`text-[12px] font-bold ${
                        isSelected ? "fill-sky-700" : "fill-slate-800"
                      }`}
                    >
                      {n.label}
                    </text>
                    <text
                      x={n.x}
                      y={n.y + 67}
                      textAnchor="middle"
                      className="fill-slate-500 text-[10px] font-mono"
                    >
                      {n.sub}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </motion.div>

        {/* Detailed 6-Node List + Live Deep-Dive Inspector */}
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-7 items-start">
          {/* Left Column: Clickable Pipeline Stages */}
          <div className="lg:col-span-7 space-y-2.5">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center justify-between">
              <span>Packet Traversal Stages</span>
              <span className="text-sky-600 font-mono text-[11px]">Click any layer to inspect</span>
            </div>

            {ARCH_NODES.map((node) => {
              const isSelected = selectedNode.id === node.id;
              return (
                <motion.div
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  whileHover={{ x: 4 }}
                  transition={{ type: "spring", stiffness: 400, damping: 28 }}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer relative overflow-hidden ${
                    isSelected
                      ? "bg-white border-sky-400 shadow-lg shadow-sky-900/[0.07]"
                      : "bg-white/75 border-slate-200 hover:border-sky-300 hover:bg-white"
                  }`}
                >
                  {isSelected && (
                    <motion.div
                      layoutId="activeArchBar"
                      className="absolute left-0 top-0 bottom-0 w-1.5 bg-gradient-to-b from-sky-500 to-emerald-500"
                    />
                  )}

                  <div className="flex items-center justify-between gap-4 pl-1.5">
                    <div className="flex items-center gap-3.5">
                      <div
                        className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg flex-shrink-0 border ${
                          isSelected
                            ? "bg-sky-50 border-sky-200"
                            : "bg-slate-50 border-slate-200"
                        }`}
                      >
                        {node.icon}
                      </div>

                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4
                            className={`text-sm sm:text-base font-bold transition-colors ${
                              isSelected ? "text-sky-800" : "text-slate-800"
                            }`}
                          >
                            {node.title}
                          </h4>
                          <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 border border-slate-200">
                            {node.tag}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 mt-0.5">{node.subtitle}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="hidden sm:inline-block text-[11px] font-mono text-sky-700 font-medium">
                        {node.technology}
                      </span>
                      <ArrowRight
                        className={`w-4 h-4 transition-transform ${
                          isSelected ? "text-sky-600 translate-x-1" : "text-slate-400"
                        }`}
                      />
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Right Column: Sticky Node Deep-Dive Inspector */}
          <div className="lg:col-span-5 lg:sticky lg:top-24">
            <AnimatePresence mode="wait">
              <motion.div
                key={selectedNode.id}
                initial={{ opacity: 0, y: 10, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.98 }}
                transition={{ duration: 0.22 }}
                className="rounded-3xl bg-white border border-sky-200/90 p-6 sm:p-7 shadow-xl shadow-sky-900/[0.06] relative overflow-hidden"
              >
                <div className="absolute -top-12 -right-12 w-36 h-36 bg-sky-100 rounded-full blur-2xl pointer-events-none" />

                <div className="flex items-center justify-between mb-4 relative">
                  <span className="text-xs font-mono text-sky-700 font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-emerald-600 animate-pulse" />
                    <span>Subsystem Inspector</span>
                  </span>
                  <span className="text-2xl">{selectedNode.icon}</span>
                </div>

                <h3 className="text-xl font-extrabold text-slate-900 mb-1">
                  {selectedNode.title}
                </h3>
                <div className="text-xs text-sky-700 font-mono font-semibold mb-4">
                  Technology: {selectedNode.technology}
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 mb-5">
                  <p className="text-xs sm:text-sm text-slate-700 leading-relaxed">
                    {selectedNode.description}
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                    <Terminal className="w-3.5 h-3.5 text-sky-600" />
                    <span>Kernel & Subsystem Invocation</span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 font-mono text-xs text-emerald-300 overflow-x-auto select-all shadow-inner">
                    <code>{selectedNode.kernelAction}</code>
                  </div>
                </div>

                <div className="mt-6 pt-5 border-t border-slate-200 grid grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="text-slate-500 block text-[10px] uppercase font-mono font-semibold">
                      Routing Isolation
                    </span>
                    <span className={`font-bold ${tunnelActive ? "text-slate-900" : "text-rose-600"}`}>
                      {tunnelActive ? "Full-Tunnel (100%)" : "Direct (Bypassed)"}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="text-slate-500 block text-[10px] uppercase font-mono font-semibold">
                      IPv6 & DNS Guard
                    </span>
                    <span className={`font-bold ${ipv6Blocked ? "text-emerald-700" : "text-amber-700"}`}>
                      {ipv6Blocked ? "Zero-Leak Active" : "IPv6 Unprotected"}
                    </span>
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}
