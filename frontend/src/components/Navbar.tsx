"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { Download, Terminal, BookOpen, Shield, HelpCircle, Menu, X, Network } from "lucide-react";
import GithubIcon from "@/components/GithubIcon";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 18);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { name: "Interactive Model", href: "#architecture", icon: Network },
    { name: "Live Demo", href: "#simulator", icon: Terminal },
    { name: "Install", href: "#downlink", icon: Download },
    { name: "Kernel Stack", href: "#kernel-integration", icon: Shield },
    { name: "User Guide", href: "#user-guide", icon: BookOpen },
    { name: "FAQ", href: "#faq", icon: HelpCircle },
  ];

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-white/85 backdrop-blur-xl border-b border-slate-200/80 shadow-sm shadow-slate-900/[0.04] py-3"
          : "bg-transparent py-5"
      }`}
    >
      <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        {/* Logo & Brand */}
        <a href="#" className="flex items-center gap-3 group">
          <motion.div
            whileHover={{ rotate: 6, scale: 1.06 }}
            transition={{ type: "spring", stiffness: 360, damping: 20 }}
            className="relative w-9 h-9 rounded-xl overflow-hidden p-0.5 bg-gradient-to-br from-sky-500/20 to-emerald-500/20 border border-sky-200 group-hover:border-sky-400 transition-colors shadow-sm"
          >
            <Image
              src="/icon.png"
              alt="AuraLink Logo"
              width={36}
              height={36}
              className="w-full h-full object-cover rounded-lg"
            />
          </motion.div>
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-lg tracking-tight text-slate-900">
              AuraLink
            </span>
            <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200">
              v1.0.0
            </span>
          </div>
        </a>

        {/* Desktop Navigation Links */}
        <nav className="hidden lg:flex items-center gap-1 bg-white/80 backdrop-blur-md px-2.5 py-1.5 rounded-full border border-slate-200/90 shadow-sm">
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
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-sky-700 hover:bg-sky-50 rounded-full transition-all duration-200"
            >
              <link.icon className="w-3.5 h-3.5 text-slate-400" />
              {link.name}
            </a>
          ))}
        </nav>

        {/* Right Action CTA */}
        <div className="hidden sm:flex items-center gap-2.5">
          <a
            href="https://github.com/Script-By-Lin/Arch_VPN"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 hover:border-slate-300 rounded-xl transition-all shadow-xs"
          >
            <GithubIcon className="w-4 h-4 text-slate-700" />
            <span>GitHub</span>
          </a>

          <motion.a
            whileHover={{ y: -1, scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            href="#downlink"
            className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-sky-600 to-emerald-600 hover:from-sky-500 hover:to-emerald-500 transition-all shadow-md shadow-sky-600/20 flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Install Now</span>
          </motion.a>
        </div>

        {/* Mobile Menu Toggle */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="lg:hidden p-2 rounded-xl text-slate-600 hover:text-slate-900 bg-white border border-slate-200 shadow-xs"
          aria-label="Toggle Navigation Menu"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Menu Dropdown */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="lg:hidden bg-white/95 backdrop-blur-2xl border-b border-slate-200 px-4 py-4 space-y-1.5 shadow-lg"
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
                className="flex items-center gap-2.5 px-3 py-2.5 text-sm font-semibold text-slate-700 hover:text-sky-700 hover:bg-sky-50 rounded-xl"
              >
                <link.icon className="w-4 h-4 text-sky-600" />
                {link.name}
              </a>
            ))}
            <div className="pt-3 border-t border-slate-200 flex flex-col gap-2">
              <a
                href="https://github.com/Script-By-Lin/Arch_VPN"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 py-2.5 text-xs font-semibold text-slate-700 bg-slate-100 rounded-xl"
              >
                <GithubIcon className="w-4 h-4" />
                <span>View Repository on GitHub</span>
              </a>
              <a
                href="#downlink"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center justify-center gap-2 py-2.5 text-xs font-bold text-white bg-gradient-to-r from-sky-600 to-emerald-600 rounded-xl"
              >
                <Download className="w-4 h-4" />
                <span>Quick Install (1-Line)</span>
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
