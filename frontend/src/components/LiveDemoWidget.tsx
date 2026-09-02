"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { 
  Power, 
  Activity, 
  ArrowDown, 
  ArrowUp, 
  RefreshCw, 
  Terminal, 
  ChevronDown,
  Trash2,
  RotateCcw
} from "lucide-react";

export default function LiveDemoWidget() {
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [downloadSpeed, setDownloadSpeed] = useState("0.0");
  const [uploadSpeed, setUploadSpeed] = useState("0.0");
  const [ping, setPing] = useState(24);
  const [pinging, setPinging] = useState(false);
  const [servers, setServers] = useState<string[]>([
    "Tokyo-Fast-01",
    "Singapore-02",
    "US-West-03"
  ]);
  const [activeProfile, setActiveProfile] = useState("Tokyo-Fast-01");
  const [selectedDns, setSelectedDns] = useState("Cloudflare (1.1.1.1 / 1.0.0.1)");
  const [logs, setLogs] = useState<string[]>([
    "[12:00:00] [STATUS] ShadowTun GUI ready.",
    "[12:00:01] [PROFILE] Active node: Tokyo-Fast-01 (198.51.100.42:8443).",
    "[12:00:02] [IDLE] System using standard physical route (192.168.1.1)."
  ]);

  const addLog = (tag: string, message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev.slice(-7), `[${timestamp}] [${tag}] ${message}`]);
  };

  const handleToggle = () => {
    if (connected) {
      // Disconnecting
      setConnected(false);
      setDownloadSpeed("0.0");
      setUploadSpeed("0.0");
      addLog("DISCONNECT", "Disconnecting tun0 interface...");
      addLog("CLEANUP", "Restoring physical default route and reverting systemd-resolved.");
      addLog("STATUS", "Tunnel terminated cleanly.");
    } else {
      // Connecting
      if (!activeProfile) {
        addLog("ERROR", "No active server node selected. Please restore nodes first.");
        return;
      }
      setConnecting(true);
      addLog("INIT", "Requesting privileged route setup from /usr/bin/vpn-core-helper...");
      
      setTimeout(() => {
        addLog("KERNEL", "tun0 (10.0.0.2/24) created. sslocal listening on 127.0.0.1:1080.");
      }, 450);

      setTimeout(() => {
        addLog("DNS", `Injected resolvectl domain tun0 "~." with DNS ${selectedDns.split(" ")[0]}.`);
        addLog("ROUTING", "Default route hijacked -> tun0. Pinned server route via wlan0.");
        setConnecting(false);
        setConnected(true);
        addLog("SUCCESS", "ShadowTun connected! 100% full-tunnel active.");
      }, 1000);
    }
  };

  const handlePingTest = () => {
    if (!activeProfile) return;
    setPinging(true);
    addLog("PING", `Probing ${activeProfile} via TCP SYN/ACK handshake...`);
    setTimeout(() => {
      const newPing = Math.floor(Math.random() * 12) + 18;
      setPing(newPing);
      setPinging(false);
      addLog("PING", `Response received from ${activeProfile}: ${newPing}ms (0% packet loss).`);
    }, 450);
  };

  const handleDeleteServer = () => {
    if (!activeProfile) return;
    const target = activeProfile;
    const remaining = servers.filter((s) => s !== target);
    setServers(remaining);
    addLog("DELETE", `Deleted server profile '${target}'.`);

    if (connected) {
      setConnected(false);
      setDownloadSpeed("0.0");
      setUploadSpeed("0.0");
      addLog("DISCONNECT", `Active tunnel node '${target}' deleted; disconnected.`);
    }

    if (remaining.length > 0) {
      setActiveProfile(remaining[0]);
      addLog("PROFILE", `Switched active node to ${remaining[0]}.`);
    } else {
      setActiveProfile("");
      addLog("WARNING", "No server profiles remaining. Click Restore to reset default nodes.");
    }
  };

  const handleResetServers = () => {
    const defaults = ["Tokyo-Fast-01", "Singapore-02", "US-West-03"];
    setServers(defaults);
    setActiveProfile(defaults[0]);
    addLog("CONFIG", "Default server profiles restored.");
  };

  // Live telemetry speed generator when connected
  useEffect(() => {
    if (!connected) return;
    const interval = setInterval(() => {
      const down = (Math.random() * 25 + 38).toFixed(1);
      const up = (Math.random() * 8 + 8).toFixed(1);
      setDownloadSpeed(down);
      setUploadSpeed(up);
    }, 1400);
    return () => clearInterval(interval);
  }, [connected]);

  return (
    <section id="simulator" className="py-20 md:py-28 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/2 left-1/4 -translate-y-1/2 w-96 h-96 bg-cyan-500/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-[140px] pointer-events-none" />

      <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-14">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-cyan-300 text-xs font-semibold uppercase tracking-wider mb-3 shadow-lg shadow-cyan-950/40">
            <Activity className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            <span>Interactive Live Simulation</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight">
            Try ShadowTun in Your Browser
          </h2>
          <p className="mt-3 text-slate-300 text-sm sm:text-base">
            Test the PyQt5 GUI connection switch, live telemetry counters, ping latency testing, and DNS sinkhole behavior interactively.
          </p>
        </div>

        {/* The Enhanced GUI Simulator Container */}
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
          
          {/* LEFT WINDOW: ShadowTun GUI Client */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="lg:col-span-7 rounded-3xl bg-[#090d16]/95 border border-[#1a2538] hover:border-cyan-500/30 p-6 sm:p-8 shadow-2xl shadow-cyan-950/30 flex flex-col justify-between relative overflow-hidden backdrop-blur-xl"
          >
            {/* Top Bar of the App Window */}
            <div className="flex items-center justify-between pb-5 border-b border-white/[0.06] mb-6">
              <div className="flex items-center gap-2.5">
                <div className="w-3 h-3 rounded-full bg-[#ef4444] shadow-sm shadow-rose-950" />
                <div className="w-3 h-3 rounded-full bg-[#f59e0b] shadow-sm shadow-amber-950" />
                <div className="w-3 h-3 rounded-full bg-[#10b981] shadow-sm shadow-emerald-950" />
                <span className="text-xs font-mono font-medium text-slate-300 ml-2">
                  ShadowTun GUI
                </span>
              </div>
              
              {/* Connection Status Pill Badge */}
              <div>
                <span className={`text-[10.5px] font-mono font-bold tracking-wider px-3 py-1 rounded-full uppercase transition-all ${
                  connected 
                    ? "bg-[#064e3b]/80 text-[#34d399] border border-[#059669]/50 shadow-md shadow-emerald-950/40" 
                    : connecting
                    ? "bg-[#78350f]/80 text-[#fbbf24] border border-[#d97706]/50 animate-pulse"
                    : "bg-[#111827] text-slate-400 border border-white/[0.08]"
                }`}>
                  {connecting ? "CONNECTING..." : connected ? "CONNECTED" : "DISCONNECTED"}
                </span>
              </div>
            </div>

            {/* Central Circular Connect Button */}
            <div className="flex flex-col items-center justify-center my-8">
              <div className="relative flex items-center justify-center">
                
                {/* Radiant Concentric Waves when connected */}
                {connected && (
                  <>
                    <motion.div
                      animate={{ scale: [1, 1.4, 1], opacity: [0.5, 0, 0.5] }}
                      transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut" }}
                      className="absolute -inset-6 rounded-full bg-emerald-500/20 blur-xl pointer-events-none"
                    />
                    <motion.div
                      animate={{ scale: [1, 1.25, 1], opacity: [0.8, 0.1, 0.8] }}
                      transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                      className="absolute -inset-4 rounded-full border border-emerald-400/40 pointer-events-none"
                    />
                  </>
                )}

                {/* The Circular Connect Switch */}
                <motion.button
                  whileHover={{ scale: 1.04 }}
                  whileTap={{ scale: 0.96 }}
                  onClick={handleToggle}
                  disabled={connecting}
                  className={`w-44 h-44 sm:w-48 sm:h-48 rounded-full flex flex-col items-center justify-center gap-2.5 font-bold transition-all duration-300 shadow-2xl cursor-pointer relative z-10 ${
                    connected
                      ? "bg-gradient-to-b from-[#0e3b2e] via-[#092920] to-[#041712] text-white border-2 border-[#10b981] shadow-emerald-950/60"
                      : connecting
                      ? "bg-gradient-to-b from-[#3b2a0e] to-[#1a1205] text-[#fcd34d] border-2 border-amber-400 animate-pulse"
                      : "bg-gradient-to-b from-[#141b2d] via-[#0d121f] to-[#080b13] text-slate-200 hover:text-white border-2 border-[#1e293b] hover:border-cyan-400/60 shadow-black/80"
                  }`}
                  aria-label="Toggle VPN Connection"
                >
                  <div className={`p-3.5 rounded-full transition-colors ${
                    connected ? "bg-emerald-500/20 text-emerald-300" : "bg-cyan-500/10 text-cyan-400"
                  }`}>
                    <Power className={`w-9 h-9 sm:w-10 sm:h-10 ${connected ? "text-emerald-400" : "text-cyan-400"}`} />
                  </div>
                  <span className="text-[11px] sm:text-xs font-mono font-extrabold tracking-widest uppercase">
                    {connecting ? "CONNECTING..." : connected ? "CLICK TO DISCONNECT" : "CLICK TO CONNECT"}
                  </span>
                </motion.button>
              </div>

              {/* Status Caption under Button */}
              <div className="mt-6 text-center">
                <span className="text-xs font-mono text-slate-400">
                  {connected 
                    ? "Virtual tun0 interface active • 100% full-tunnel routed" 
                    : "System using standard physical route"}
                </span>
              </div>
            </div>

            {/* Bottom Live Speed Counters Split Box */}
            <div className="grid grid-cols-2 gap-4 pt-5 border-t border-white/[0.06]">
              
              {/* Download Speed Card */}
              <div className="p-4 rounded-2xl bg-[#060a12]/80 border border-white/[0.06] flex items-center gap-3.5 shadow-inner">
                <div className="w-10 h-10 rounded-xl bg-cyan-500/15 text-cyan-400 flex items-center justify-center flex-shrink-0">
                  <ArrowDown className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400 block mb-0.5">
                    DOWNLOAD SPEED
                  </span>
                  <div className="text-lg sm:text-xl font-mono font-bold text-white tracking-tight">
                    {downloadSpeed} <span className="text-xs text-cyan-400 font-normal">MB/s</span>
                  </div>
                </div>
              </div>

              {/* Upload Speed Card */}
              <div className="p-4 rounded-2xl bg-[#060a12]/80 border border-white/[0.06] flex items-center gap-3.5 shadow-inner">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/15 text-emerald-400 flex items-center justify-center flex-shrink-0">
                  <ArrowUp className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400 block mb-0.5">
                    UPLOAD SPEED
                  </span>
                  <div className="text-lg sm:text-xl font-mono font-bold text-white tracking-tight">
                    {uploadSpeed} <span className="text-xs text-emerald-400 font-normal">MB/s</span>
                  </div>
                </div>
              </div>

            </div>

          </motion.div>

          {/* RIGHT COLUMN: Active Node, DNS Upstream & Live Log Stream */}
          <div className="lg:col-span-5 flex flex-col justify-between space-y-5">
            
            {/* Top Card: Active Subscription Node & DNS Selector */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="p-5 sm:p-6 rounded-3xl bg-[#090d16]/95 border border-[#1a2538] hover:border-cyan-500/30 space-y-5 shadow-2xl backdrop-blur-xl"
            >
              {/* Header with Ping Probe & Server Delete Button */}
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
                  ACTIVE SUBSCRIPTION NODE
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handlePingTest}
                    disabled={pinging || !activeProfile}
                    className="flex items-center gap-1.5 text-xs font-mono font-semibold text-cyan-400 hover:text-cyan-300 px-3 py-1 rounded-xl bg-cyan-500/10 border border-cyan-500/25 hover:border-cyan-400/50 transition-all cursor-pointer shadow-sm disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${pinging ? "animate-spin" : ""}`} />
                    <span>Ping: {activeProfile ? `${ping}ms` : "--"}</span>
                  </button>
                  <button
                    onClick={handleDeleteServer}
                    disabled={servers.length === 0}
                    className="flex items-center gap-1.5 text-xs font-mono font-semibold text-rose-400 hover:text-rose-300 px-2.5 py-1 rounded-xl bg-rose-500/10 border border-rose-500/25 hover:border-rose-400/50 transition-all cursor-pointer shadow-sm disabled:opacity-40 disabled:cursor-not-allowed"
                    title="Delete currently selected server profile"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Delete</span>
                  </button>
                </div>
              </div>

              {/* Node Pills or Empty State */}
              {servers.length > 0 ? (
                <div className="grid grid-cols-3 gap-2 text-xs font-medium">
                  {servers.map((node) => {
                    const isActive = activeProfile === node;
                    return (
                      <button
                        key={node}
                        onClick={() => {
                          setActiveProfile(node);
                          addLog("PROFILE", `Switched active node to ${node}.`);
                        }}
                        className={`py-2 px-2 rounded-xl text-center font-mono text-[11px] font-semibold transition-all cursor-pointer ${
                          isActive
                            ? "bg-cyan-500/20 text-cyan-300 border border-cyan-400/60 shadow-lg shadow-cyan-950/40"
                            : "bg-[#060a12] text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] border border-white/[0.06]"
                        }`}
                      >
                        {node}
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="p-3 rounded-xl bg-[#060a12] border border-dashed border-white/[0.1] text-center space-y-2">
                  <span className="text-xs font-mono text-slate-400 block">
                    No server profiles remaining.
                  </span>
                  <button
                    onClick={handleResetServers}
                    className="inline-flex items-center gap-1.5 text-[11px] font-mono font-bold text-cyan-400 hover:text-cyan-300 px-3 py-1 rounded-lg bg-cyan-500/10 border border-cyan-500/30 transition-colors cursor-pointer"
                  >
                    <RotateCcw className="w-3 h-3" />
                    <span>Restore Default Nodes</span>
                  </button>
                </div>
              )}

              {/* DNS Upstream Resolver Section */}
              <div>
                <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-400 block mb-2">
                  DNS UPSTREAM RESOLVER
                </span>
                <div className="relative">
                  <select
                    value={selectedDns}
                    onChange={(e) => {
                      setSelectedDns(e.target.value);
                      addLog("DNS", `Selected upstream resolver: ${e.target.value}.`);
                    }}
                    aria-label="Select DNS Upstream Resolver"
                    className="w-full appearance-none bg-[#060a12] border border-white/[0.08] hover:border-cyan-500/30 rounded-xl px-3.5 py-2.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-400 transition-colors cursor-pointer"
                  >
                    <option>Cloudflare (1.1.1.1 / 1.0.0.1)</option>
                    <option>Google (8.8.8.8 / 8.8.4.4)</option>
                    <option>Quad9 (9.9.9.9 / 149.112.112.112)</option>
                    <option>AdGuard (94.140.14.14 / 94.140.15.15)</option>
                  </select>
                  <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </div>
            </motion.div>

            {/* Bottom Card: Real-Time Log Stream Window */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="p-5 sm:p-6 rounded-3xl bg-[#090d16]/95 border border-[#1a2538] font-mono text-xs text-slate-300 flex-1 flex flex-col justify-between shadow-2xl backdrop-blur-xl"
            >
              <div className="flex items-center justify-between pb-3 border-b border-white/[0.06] mb-3 text-slate-400 text-[11px]">
                <div className="flex items-center gap-1.5 font-semibold text-slate-300">
                  <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Real-Time Log Stream</span>
                </div>
                <span className="text-[10px] text-emerald-400 font-bold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                  ● LIVE
                </span>
              </div>

              <div suppressHydrationWarning className="space-y-1.5 overflow-y-auto max-h-[150px] text-[11px] leading-relaxed scrollbar-thin pr-1">
                {logs.map((log, index) => {
                  const isSuccess = log.includes("[SUCCESS]");
                  const isDisconnect = log.includes("[DISCONNECT]");
                  const isClean = log.includes("[CLEANUP]");
                  const isRouting = log.includes("[ROUTING]") || log.includes("[KERNEL]");
                  const isDns = log.includes("[DNS]");

                  return (
                    <div
                      key={index}
                      className={
                        isSuccess
                          ? "text-emerald-400 font-bold"
                          : isDisconnect
                          ? "text-amber-400 font-medium"
                          : isClean
                          ? "text-slate-300"
                          : isRouting || isDns
                          ? "text-cyan-300"
                          : "text-slate-400"
                      }
                    >
                      {log}
                    </div>
                  );
                })}
              </div>

              <div className="mt-4 pt-3 border-t border-white/[0.06] text-[10px] text-slate-400 flex items-center justify-between">
                <span>Direct /proc/net/dev telemetry</span>
                <span className="text-cyan-400 font-mono font-semibold">127.0.0.1:1080</span>
              </div>
            </motion.div>

          </div>

        </div>

      </div>
    </section>
  );
}
