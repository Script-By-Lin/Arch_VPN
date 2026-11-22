import React from "react";
import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import DownlinkCard from "@/components/DownlinkCard";
import ArchitectureVisualizer from "@/components/ArchitectureVisualizer";
import LinuxTerminalShowcase from "@/components/LinuxTerminalShowcase";
import LiveDemoWidget from "@/components/LiveDemoWidget";
import UserGuideSection from "@/components/UserGuideSection";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#f8fafc] text-slate-900 selection:bg-sky-200 selection:text-sky-950">
      <Navbar />
      <Hero />
      <ArchitectureVisualizer />
      <LiveDemoWidget />
      <DownlinkCard />
      <LinuxTerminalShowcase />
      <UserGuideSection />
      <Footer />
    </main>
  );
}
