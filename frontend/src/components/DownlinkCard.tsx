"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Copy, Check, ShieldCheck } from "lucide-react";
import { DISTRO_INSTALLS } from "@/data/appData";

export default function DownlinkCard() {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <section id="downlink" className="py-16 md:py-24 relative bg-white border-t border-slate-200/80">
      <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="space-y-6 max-w-5xl mx-auto"
        >
          {/* Header Title & Version Pill */}
          <div className="flex items-center gap-3 flex-wrap">
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 font-sans">
              AuraLink CLI & Desktop
            </h2>
            <span className="inline-flex items-center px-3 py-0.5 rounded-full text-xs font-mono font-bold bg-sky-50 text-sky-700 border border-sky-200">
              v1.0.0
            </span>
          </div>

          <p className="text-slate-600 text-base sm:text-lg leading-relaxed max-w-3xl">
            Work with AuraLink directly in your terminal or desktop. Full TUN encapsulation, automatic subscription decoding, kernel IPv6 leak blocking, and zero-leak DNS across every major Linux distribution.
          </p>

          {/* Platform Sections */}
          <div className="pt-4 space-y-6">
            {DISTRO_INSTALLS.map((platform, idx) => {
              const isCopied = copiedId === platform.id;
              return (
                <motion.div
                  key={platform.id}
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: idx * 0.04 }}
                  className="p-5 rounded-2xl bg-slate-50/80 border border-slate-200 hover:border-sky-300 transition-all space-y-2.5 shadow-xs"
                >
                  <div className="flex flex-wrap items-center gap-2 text-sm font-bold text-slate-900">
                    <span className="text-base">{platform.icon}</span>
                    <span>{platform.name}</span>
                    {platform.badge && (
                      <span className="text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200">
                        {platform.badge}
                      </span>
                    )}
                  </div>

                  {platform.notes && (
                    <p className="text-xs text-slate-500 leading-relaxed">{platform.notes}</p>
                  )}

                  <div className="group relative flex items-center justify-between gap-4 px-4 py-3.5 rounded-xl bg-white border border-slate-200 hover:border-sky-300 transition-colors">
                    <div className="overflow-x-auto font-mono text-xs sm:text-[13px] text-sky-800 leading-relaxed pr-2 w-full select-all">
                      <pre className="whitespace-pre font-mono font-medium">
                        {platform.command}
                      </pre>
                    </div>

                    <motion.button
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handleCopy(platform.command, platform.id)}
                      className={`flex-shrink-0 flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                        isCopied
                          ? "bg-emerald-600 text-white shadow-sm"
                          : "bg-slate-100 text-slate-700 hover:text-sky-700 hover:bg-sky-50 border border-slate-200"
                      }`}
                      title={`Copy ${platform.name} command`}
                      aria-label={`Copy command for ${platform.name}`}
                    >
                      {isCopied ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-white" />
                          <span>Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span className="hidden sm:inline">Copy</span>
                        </>
                      )}
                    </motion.button>
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Bottom helper info */}
          <div className="pt-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs text-slate-600">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span>
                Helper rule configured in{" "}
                <code className="text-slate-900 font-mono bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                  /etc/sudoers.d/auralink
                </code>{" "}
                for passwordless operation
              </span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
