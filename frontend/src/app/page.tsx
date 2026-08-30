import React from "react";
import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import DownlinkCard from "@/components/DownlinkCard";
import LinuxTerminalShowcase from "@/components/LinuxTerminalShowcase";
import LiveDemoWidget from "@/components/LiveDemoWidget";
import UserGuideSection from "@/components/UserGuideSection";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#07090e] text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-200">
      <Navbar />
      <Hero />
      <DownlinkCard />
      <LinuxTerminalShowcase />
      <LiveDemoWidget />
      <UserGuideSection />
      <Footer />
    </main>
  );
}
