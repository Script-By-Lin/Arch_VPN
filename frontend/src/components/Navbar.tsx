"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import { motion } from "framer-motion";
import { Download, Terminal, BookOpen, Shield, HelpCircle, Menu, X } from "lucide-react";
import GithubIcon from "@/components/GithubIcon";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { name: "Install", href: "#downlink", icon: Download },
    { name: "Kernel & Architecture", href: "#kernel-integration", icon: Shield },
    { name: "Live Demo", href: "#simulator", icon: Terminal },
    { name: "User Guide", href: "#user-guide", icon: BookOpen },
    { name: "Troubleshooting", href: "#faq", icon: HelpCircle },
  ];

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-[#07090e]/85 backdrop-blur-xl border-b border-white/[0.08] shadow-2xl shadow-cyan-950/20 py-3"
          : "bg-transparent py-5"
      }`}
    >
      <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        {/* Logo & Brand */}
        <a href="#" className="flex items-center gap-3 group">
          <div className="relative w-9 h-9 rounded-xl overflow-hidden p-1.5 bg-gradient-to-br from-cyan-500/20 to-purple-600/20 border border-cyan-500/30 group-hover:border-cyan-400/60 transition-colors">
            <Image
              src="/icon.svg"
              alt="ShadowTun Logo"
              width={32}
              height={32}
              className="w-full h-full object-contain"
            />
            <div className="absolute inset-0 bg-cyan-400/10 opacity-0 group-hover:opacity-100 transition-opacity rounded-xl" />
          </div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">
              ShadowTun
            </span>
            <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              v1.0.0
            </span>
          </div>
        </a>

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-1 bg-slate-900/60 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/[0.06]">
          {navLinks.map((link) => (
            <a
              key={link.name}
              href={link.href}
              onClick={() => {
                const target = link.href.replace("#", "");
                if (typeof window !== "undefined") {
                  window.dispatchEvent(new CustomEvent("switch-userguide-tab", { detail: target }));
                }
              }}
              className="flex items-center gap-1.5 px-3 py-1 text-sm font-medium text-slate-300 hover:text-cyan-400 hover:bg-white/[0.04] rounded-full transition-all duration-200"
            >
              <link.icon className="w-3.5 h-3.5 opacity-70" />
              {link.name}
            </a>
          ))}
        </nav>

        {/* Right Action CTA */}
        <div className="hidden sm:flex items-center gap-3">
          <a
            href="https://github.com/Script-By-Lin/Arch_VPN"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold text-slate-300 bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] hover:border-slate-600 rounded-lg transition-all"
          >
            <GithubIcon className="w-4 h-4 text-slate-300" />
            <span>GitHub</span>
          </a>

          <a
            href="#downlink"
            className="relative group overflow-hidden px-4 py-1.5 rounded-lg text-xs font-semibold text-black bg-gradient-to-r from-cyan-400 to-emerald-400 hover:from-cyan-300 hover:to-emerald-300 transition-all shadow-lg shadow-cyan-500/20 hover:shadow-cyan-400/30 flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Install Now</span>
          </a>
        </div>

        {/* Mobile Menu Toggle */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white bg-slate-900/80 border border-white/[0.08]"
          aria-label="Toggle Navigation Menu"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="md:hidden bg-[#0a0d17]/95 backdrop-blur-2xl border-b border-white/[0.08] px-4 py-4 space-y-2"
        >
          {navLinks.map((link) => (
            <a
              key={link.name}
              href={link.href}
              onClick={() => {
                setMobileMenuOpen(false);
                const target = link.href.replace("#", "");
                if (typeof window !== "undefined") {
                  window.dispatchEvent(new CustomEvent("switch-userguide-tab", { detail: target }));
                }
              }}
              className="flex items-center gap-2.5 px-3 py-2 text-sm font-medium text-slate-300 hover:text-cyan-400 hover:bg-white/[0.04] rounded-lg"
            >
              <link.icon className="w-4 h-4 text-cyan-400/80" />
              {link.name}
            </a>
          ))}
          <div className="pt-3 border-t border-white/[0.06] flex flex-col gap-2">
            <a
              href="https://github.com/Script-By-Lin/Arch_VPN"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 py-2 text-xs font-medium text-slate-300 bg-white/[0.04] rounded-lg"
            >
              <GithubIcon className="w-4 h-4" />
              <span>View Repository on GitHub</span>
            </a>
            <a
              href="#downlink"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center justify-center gap-2 py-2 text-xs font-semibold text-black bg-gradient-to-r from-cyan-400 to-emerald-400 rounded-lg"
            >
              <Download className="w-4 h-4" />
              <span>Quick Install (1-Line)</span>
            </a>
          </div>
        </motion.div>
      )}
    </header>
  );
}
