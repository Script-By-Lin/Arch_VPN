"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ARCH_NODES, ArchNode } from "@/data/appData";
import { Cpu, ArrowRight, CheckCircle, Terminal, Layers, ShieldCheck, Activity, Network } from "lucide-react";

export default function ArchitectureVisualizer() {
  const [selectedNode, setSelectedNode] = useState<ArchNode>(ARCH_NODES[1]); // default to Kernel TUN

  return (
    <section id="architecture" className="py-20 md:py-28 relative bg-[#06080d]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/25 text-purple-300 text-xs font-semibold uppercase tracking-wider mb-3">
            <Network className="w-3.5 h-3.5 text-purple-400" />
            <span>Linux Kernel Pipeline</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            System & Network Architecture
          </h2>
          <p className="mt-3 text-slate-300 text-sm sm:text-base">
            Inspect how ShadowTun intercepts Layer-3 packets at the Linux kernel boundary and bridges them into encrypted SOCKS5 streams.
          </p>
        </div>

        {/* Interactive Architecture Flow Pipeline */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Left Column: Interactive Flow Steps */}
          <div className="lg:col-span-7 space-y-3">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
              <span>Packet Traversal Pipeline</span>
              <span className="text-cyan-400 font-mono text-[11px]">Click node to inspect</span>
            </div>

            {ARCH_NODES.map((node, index) => {
              const isSelected = selectedNode.id === node.id;
              return (
                <motion.div
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  whileHover={{ scale: 1.01 }}
                  className={`p-4 sm:p-5 rounded-2xl border transition-all cursor-pointer relative overflow-hidden ${
                    isSelected
                      ? "bg-gradient-to-r from-cyan-950/40 via-slate-900/90 to-purple-950/30 border-cyan-400/60 shadow-xl shadow-cyan-950/40"
                      : "bg-[#0c101a]/70 border-white/[0.06] hover:border-white/20 hover:bg-slate-900/50"
                  }`}
                >
                  {/* Active node left indicator bar */}
                  {isSelected && (
                    <motion.div
                      layoutId="activeIndicator"
                      className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-cyan-400 to-emerald-400"
                    />
                  )}

                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3.5">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg flex-shrink-0 ${
                        isSelected 
                          ? "bg-cyan-500/20 text-cyan-300 border border-cyan-400/40" 
                          : "bg-slate-800/80 text-slate-400 border border-white/[0.06]"
                      }`}>
                        {node.icon}
                      </div>

                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className={`text-sm sm:text-base font-bold transition-colors ${
                            isSelected ? "text-cyan-200" : "text-slate-200"
                          }`}>
                            {node.title}
                          </h4>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/[0.06] text-slate-400">
                            {node.tag}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5">
                          {node.subtitle}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="hidden sm:inline-block text-[11px] font-mono text-cyan-400/80">
                        {node.technology}
                      </span>
                      <ArrowRight className={`w-4 h-4 transition-transform ${
                        isSelected ? "text-cyan-400 translate-x-1" : "text-slate-600"
                      }`} />
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Right Column: Node Deep-Dive Inspector */}
          <div className="lg:col-span-5 sticky top-24">
            <AnimatePresence mode="wait">
              <motion.div
                key={selectedNode.id}
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.96 }}
                transition={{ duration: 0.25 }}
                className="rounded-3xl bg-[#0e1320] border border-cyan-500/30 p-6 sm:p-8 shadow-2xl shadow-cyan-950/30 backdrop-blur-xl relative overflow-hidden"
              >
                {/* Glow accent */}
                <div className="absolute -top-10 -right-10 w-40 h-40 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-mono text-cyan-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
                    <span>Active Subsystem Inspector</span>
                  </span>
                  <span className="text-2xl">{selectedNode.icon}</span>
                </div>

                <h3 className="text-xl font-bold text-white mb-1">
                  {selectedNode.title}
                </h3>
                <div className="text-xs text-cyan-300 font-mono mb-4">
                  Technology: {selectedNode.technology}
                </div>

                <div className="p-4 rounded-xl bg-black/40 border border-white/[0.06] mb-5">
                  <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                    {selectedNode.description}
                  </p>
                </div>

                {/* Low-Level Kernel Command Execution */}
                <div className="space-y-2">
                  <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Kernel & Subsystem Invocation</span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-black/80 border border-cyan-500/20 font-mono text-xs text-emerald-300 overflow-x-auto select-all">
                    <code>{selectedNode.kernelAction}</code>
                  </div>
                </div>

                {/* Subsystem Guarantees */}
                <div className="mt-6 pt-5 border-t border-white/[0.06] grid grid-cols-2 gap-3 text-xs">
                  <div className="p-2.5 rounded-lg bg-white/[0.03] border border-white/[0.04]">
                    <span className="text-slate-400 block text-[10px] uppercase font-mono">Routing Isolation</span>
                    <span className="font-semibold text-white">Full-Tunnel (100%)</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-white/[0.03] border border-white/[0.04]">
                    <span className="text-slate-400 block text-[10px] uppercase font-mono">DNS Leak Guard</span>
                    <span className="font-semibold text-emerald-400">Strict Sinkhole</span>
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
