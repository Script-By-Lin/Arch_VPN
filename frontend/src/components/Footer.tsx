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
    <footer className="border-t border-slate-200 bg-slate-50 pt-16 pb-12 relative overflow-hidden">
      <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 pb-12 border-b border-slate-200">
          {/* Col 1: Brand */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl overflow-hidden p-0.5 bg-gradient-to-br from-sky-500/20 to-emerald-500/20 border border-sky-200">
                <Image
                  src="/icon.png"
                  alt="AuraLink"
                  width={32}
                  height={32}
                  className="w-full h-full object-cover rounded-lg"
                />
              </div>
              <span className="font-extrabold text-lg text-slate-900">AuraLink Linux</span>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200">
                v1.0.0
              </span>
            </div>

            <p className="text-xs sm:text-sm text-slate-600 max-w-sm leading-relaxed">
              Universal high-performance Shadowsocks & tun2socks VPN Client for Linux distributions. Full TUN kernel routing, IPv6 leak blocking, anti-censorship TLS prefixes, and zero-leak DNS protection.
            </p>

            <div className="flex items-center gap-3 pt-1">
              <a
                href="https://github.com/Script-By-Lin/Arch_VPN"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white hover:bg-sky-50 border border-slate-200 hover:border-sky-300 text-xs font-semibold text-slate-700 hover:text-sky-700 transition-colors shadow-xs"
              >
                <GithubIcon className="w-3.5 h-3.5" />
                <span>GitHub Repository</span>
              </a>
              <span className="text-xs text-slate-500 font-mono font-medium">Open Source</span>
            </div>
          </div>

          {/* Col 2: Quick Links */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 font-mono">
              Quick Links
            </h4>
            <ul className="space-y-2 text-xs text-slate-600">
              <li>
                <a href="#architecture" className="hover:text-sky-700 transition-colors">
                  Interactive Tunnel Model
                </a>
              </li>
              <li>
                <a href="#simulator" className="hover:text-sky-700 transition-colors">
                  Interactive Live Demo
                </a>
              </li>
              <li>
                <a href="#downlink" className="hover:text-sky-700 transition-colors">
                  1-Line Install Downlink
                </a>
              </li>
              <li>
                <a href="#kernel-integration" className="hover:text-sky-700 transition-colors">
                  Kernel & Architecture
                </a>
              </li>
              <li>
                <a href="#user-guide" className="hover:text-sky-700 transition-colors">
                  User Guide & Manual
                </a>
              </li>
            </ul>
          </div>

          {/* Col 3: Documentation */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 font-mono">
              Documentation
            </h4>
            <ul className="space-y-2 text-xs text-slate-600">
              {[
                { href: "#quickstart", tab: "quickstart", label: "Quick Start Guide" },
                { href: "#gui", tab: "gui", label: "Desktop GUI Walkthrough" },
                { href: "#cli", tab: "cli", label: "CLI Commands Reference" },
                { href: "#protocol", tab: "protocol", label: "ssconf:// Subscription Protocol" },
                { href: "#faq", tab: "faq", label: "Troubleshooting & FAQ" },
              ].map((item) => (
                <li key={item.tab}>
                  <a
                    href={item.href}
                    onClick={() => {
                      if (typeof window !== "undefined") {
                        window.dispatchEvent(
                          new CustomEvent("switch-userguide-tab", { detail: item.tab })
                        );
                      }
                    }}
                    className="hover:text-sky-700 transition-colors"
                  >
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom copyright */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-1.5">
            <span>Crafted for Linux by</span>
            <a
              href="https://github.com/Script-By-Lin"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sky-700 hover:underline font-semibold"
            >
              Script-By-Lin
            </a>
          </div>

          <button
            onClick={scrollToTop}
            className="p-2 rounded-xl bg-white hover:bg-sky-50 text-slate-500 hover:text-sky-700 border border-slate-200 hover:border-sky-300 transition-colors shadow-xs cursor-pointer"
            title="Scroll to top"
            aria-label="Scroll to top"
          >
            <ArrowUp className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </footer>
  );
}
