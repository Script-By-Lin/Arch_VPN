"use client";

import React from "react";
import Image from "next/image";
import { ArrowUp } from "lucide-react";
import GithubIcon from "@/components/GithubIcon";

export default function Footer() {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <footer className="border-t border-white/[0.08] bg-[#040609] pt-16 pb-12 relative overflow-hidden">
      {/* Glow accent */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-96 h-32 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 pb-12 border-b border-white/[0.06]">
          
          {/* Col 1: Brand */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl p-1 bg-gradient-to-br from-cyan-500/20 to-purple-600/20 border border-cyan-500/30">
                <Image
                  src="/icon.svg"
                  alt="ShadowTun"
                  width={28}
                  height={28}
                  className="w-full h-full object-contain"
                />
              </div>
              <span className="font-bold text-lg text-white">ShadowTun Linux</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                v1.0.0
              </span>
            </div>

            <p className="text-xs sm:text-sm text-slate-400 max-w-sm leading-relaxed">
              Universal high-performance Shadowsocks & tun2socks VPN Client for Linux distributions. 
              Full TUN kernel routing, anti-censorship TLS prefixes, and zero-leak DNS protection.
            </p>

            <div className="flex items-center gap-3 pt-2">
              <a
                href="https://github.com/Script-By-Lin/Arch_VPN"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-xs text-slate-300 hover:text-white transition-colors"
              >
                <GithubIcon className="w-3.5 h-3.5" />
                <span>GitHub Repository</span>
              </a>
              <span className="text-xs text-slate-500 font-mono">Open Source</span>
            </div>
          </div>

          {/* Col 2: Quick Links */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono">
              Quick Links
            </h4>
            <ul className="space-y-2 text-xs text-slate-400">
              <li>
                <a href="#downlink" className="hover:text-cyan-400 transition-colors">
                  1-Line Install Downlink
                </a>
              </li>
              <li>
                <a href="#kernel-integration" className="hover:text-cyan-400 transition-colors">
                  Kernel & Architecture
                </a>
              </li>
              <li>
                <a href="#simulator" className="hover:text-cyan-400 transition-colors">
                  Interactive Live Demo
                </a>
              </li>
              <li>
                <a href="#user-guide" className="hover:text-cyan-400 transition-colors">
                  User Guide & Manual
                </a>
              </li>
            </ul>
          </div>

          {/* Col 3: Documentation */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono">
              Documentation
            </h4>
            <ul className="space-y-2 text-xs text-slate-400">
              <li>
                <a
                  href="#quickstart"
                  onClick={() => {
                    if (typeof window !== "undefined") {
                      window.dispatchEvent(new CustomEvent("switch-userguide-tab", { detail: "quickstart" }));
                    }
                  }}
                  className="hover:text-cyan-400 transition-colors"
                >
                  Quick Start Guide
                </a>
              </li>
              <li>
                <a
                  href="#gui"
                  onClick={() => {
                    if (typeof window !== "undefined") {
                      window.dispatchEvent(new CustomEvent("switch-userguide-tab", { detail: "gui" }));
                    }
                  }}
                  className="hover:text-cyan-400 transition-colors"
                >
                  Desktop GUI Walkthrough
                </a>
              </li>
              <li>
                <a
                  href="#cli"
                  onClick={() => {
                    if (typeof window !== "undefined") {
                      window.dispatchEvent(new CustomEvent("switch-userguide-tab", { detail: "cli" }));
                    }
                  }}
                  className="hover:text-cyan-400 transition-colors"
                >
                  CLI Commands Reference
                </a>
              </li>
              <li>
                <a
                  href="#protocol"
                  onClick={() => {
                    if (typeof window !== "undefined") {
                      window.dispatchEvent(new CustomEvent("switch-userguide-tab", { detail: "protocol" }));
                    }
                  }}
                  className="hover:text-cyan-400 transition-colors"
                >
                  ssconf:// Subscription Protocol
                </a>
              </li>
              <li>
                <a
                  href="#faq"
                  onClick={() => {
                    if (typeof window !== "undefined") {
                      window.dispatchEvent(new CustomEvent("switch-userguide-tab", { detail: "faq" }));
                    }
                  }}
                  className="hover:text-cyan-400 transition-colors"
                >
                  Troubleshooting & FAQ
                </a>
              </li>
            </ul>
          </div>

        </div>

        {/* Bottom copyright and tech credit */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <span>Crafted for Linux by</span>
            <a
              href="https://github.com/Script-By-Lin"
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyan-400 hover:underline font-medium"
            >
              Script-By-Lin
            </a>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={scrollToTop}
              className="p-2 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-slate-400 hover:text-white border border-white/[0.06] transition-colors"
              title="Scroll to top"
              aria-label="Scroll to top"
            >
              <ArrowUp className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

      </div>
    </footer>
  );
}
