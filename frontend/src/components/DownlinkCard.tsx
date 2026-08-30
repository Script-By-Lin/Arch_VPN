"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Copy, Check, FileCode, ExternalLink, ShieldCheck } from "lucide-react";
import { DISTRO_INSTALLS } from "@/data/appData";

export default function DownlinkCard() {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <section id="downlink" className="py-16 md:py-24 relative">
      <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Open, unboxed layout - Direct on page matching reference image */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="space-y-6 max-w-5xl"
        >
          {/* Header Title & Version Pill */}
          <div className="flex items-center gap-3">
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white font-sans">
              ShadowTun CLI
            </h2>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#1a2b4c] text-[#60a5fa] border border-[#2563eb]/30">
              v1.0.0
            </span>
          </div>

          {/* Subtitle / Description */}
          <p className="text-slate-300 text-base sm:text-lg leading-relaxed max-w-3xl">
            Work with ShadowTun directly in your codebase or desktop. Build, debug, and route all Linux traffic securely from your terminal. Full TUN encapsulation, automatic subscription decoding, and zero-leak DNS.
          </p>

          {/* Platform Sections Stacked Directly (No surrounding card) */}
          <div className="pt-4 space-y-8">
            {DISTRO_INSTALLS.map((platform) => {
              const isCopied = copiedId === platform.id;
              return (
                <div key={platform.id} className="space-y-2.5">
                  {/* Platform Label - Clean Left-Aligned */}
                  <div className="flex flex-wrap items-center gap-2 text-sm font-semibold text-slate-100">
                    <span className="text-base">{platform.icon}</span>
                    <span>{platform.name}</span>
                    {platform.badge && (
                      <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/25">
                        {platform.badge}
                      </span>
                    )}
                  </div>

                  {/* Left-Aligned Notes/Details if any */}
                  {platform.notes && (
                    <p className="text-xs text-slate-400 leading-relaxed">
                      {platform.notes}
                    </p>
                  )}

                  {/* Code Container matching the rounded pill style in reference */}
                  <div className="group relative flex items-center justify-between gap-4 px-5 py-4 rounded-2xl bg-[#0f1422] border border-white/[0.1] hover:border-cyan-500/40 transition-colors">
                    <div className="overflow-x-auto font-mono text-xs sm:text-[13.5px] text-cyan-300 leading-relaxed pr-2 w-full select-all">
                      <pre className="whitespace-pre font-mono font-normal">
                        {platform.command}
                      </pre>
                    </div>

                    {/* Copy Button */}
                    <button
                      onClick={() => handleCopy(platform.command, platform.id)}
                      className={`flex-shrink-0 flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                        isCopied
                          ? "bg-emerald-500 text-black font-bold shadow-lg shadow-emerald-500/30"
                          : "bg-slate-800/80 text-slate-300 hover:text-white hover:bg-slate-700 border border-white/10"
                      }`}
                      title={`Copy ${platform.name} command`}
                      aria-label={`Copy command for ${platform.name}`}
                    >
                      {isCopied ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-black" />
                          <span>Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-200" />
                          <span className="hidden sm:inline">Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Bottom helper info and script links */}
          <div className="pt-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>Helper rule configured in <code className="text-slate-300 font-mono">/etc/sudoers.d/shadowtun</code> for passwordless operation</span>
            </div>

          </div>

        </motion.div>
      </div>
    </section>
  );
}
