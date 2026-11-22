"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Power,
  Activity,
  ArrowDown,
  ArrowUp,
  RefreshCw,
  Terminal,
  ChevronDown,
  Trash2,
  RotateCcw,
  X,
  AlertTriangle,
  ShieldCheck,
} from "lucide-react";

function Sparkline({
  values,
  stroke,
  fillId,
}: {
  values: number[];
  stroke: string;
  fillId: string;
}) {
  const maxVal = Math.max(...values, 10);
  const width = 160;
  const height = 28;
  const points = values.map((v, idx) => {
    const x = (idx / Math.max(values.length - 1, 1)) * width;
    const y = height - 3 - (v / maxVal) * (height - 6);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const linePath = points.length > 0 ? `M ${points.join(" L ")}` : "";
  const areaPath =
    points.length > 0 ? `${linePath} L ${width},${height} L 0,${height} Z` : "";

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-7 overflow-visible">
      <defs>
        <linearGradient id={fillId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={stroke} stopOpacity="0.25" />
          <stop offset="100%" stopColor={stroke} stopOpacity="0.01" />
        </linearGradient>
      </defs>
      {areaPath && <path d={areaPath} fill={`url(#${fillId})`} />}
      {linePath && (
        <path
          d={linePath}
          fill="none"
          stroke={stroke}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}
    </svg>
  );
}

export default function LiveDemoWidget() {
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [stage, setStage] = useState<"idle" | "resolving" | "sslocal" | "tun0" | "routing" | "connected">("idle");
  const [selectedTunnelNode, setSelectedTunnelNode] = useState<number>(1);
  const [clickShockwave, setClickShockwave] = useState<{ id: number; isDisconnect: boolean } | null>(null);
  const [activeNodeRipples, setActiveNodeRipples] = useState<Record<number, number>>({});
  const [modelingMode, setModelingMode] = useState<"none" | "connecting" | "disconnecting">("none");
  const [logWrap, setLogWrap] = useState<boolean>(false);
  const [downloadSpeed, setDownloadSpeed] = useState("0.0");
  const [uploadSpeed, setUploadSpeed] = useState("0.0");
  const [totalRecv, setTotalRecv] = useState<number>(0);
  const [totalSent, setTotalSent] = useState<number>(0);
  const [downSeries, setDownSeries] = useState<number[]>(Array(14).fill(0));
  const [upSeries, setUpSeries] = useState<number[]>(Array(14).fill(0));
  const [ping, setPing] = useState(24);
  const [pinging, setPinging] = useState(false);
  const [servers, setServers] = useState<string[]>([
    "Tokyo-Fast-01",
    "Singapore-02",
    "US-West-03",
  ]);
  const [activeProfile, setActiveProfile] = useState("Tokyo-Fast-01");
  const [selectedDns, setSelectedDns] = useState("Cloudflare (1.1.1.1 / 1.0.0.1)");
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [logs, setLogs] = useState<string[]>([
    "[12:00:00] [STATUS] AuraLink Daylight GUI ready.",
    "[12:00:01] [PROFILE] Active node: Tokyo-Fast-01 (198.51.100.42:8443).",
    "[12:00:02] [IDLE] System using standard physical route (192.168.1.1).",
  ]);

  const addLog = (tag: string, message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev.slice(-7), `[${timestamp}] [${tag}] ${message}`]);
  };

  const handleToggle = () => {
    if (connected) {
      setClickShockwave({ id: Date.now(), isDisconnect: true });
      setModelingMode("disconnecting");
      setTimeout(() => setModelingMode("none"), 1200);

      setConnected(false);
      setConnecting(false);
      setStage("idle");
      setDownloadSpeed("0.0");
      setUploadSpeed("0.0");
      setTotalRecv(0);
      setTotalSent(0);
      setDownSeries(Array(14).fill(0));
      setUpSeries(Array(14).fill(0));
      addLog("DISCONNECT", "Disconnecting tun0 interface...");
      addLog("CLEANUP", "Restoring physical default route, systemd-resolved, and IPv6 sysctl.");
      addLog("STATUS", "Tunnel terminated cleanly.");
    } else {
      if (!activeProfile) {
        addLog("ERROR", "No active server node selected. Please restore nodes first.");
        return;
      }
      setClickShockwave({ id: Date.now(), isDisconnect: false });
      setModelingMode("connecting");
      setTimeout(() => setModelingMode("none"), 1450);

      setConnecting(true);
      setStage("resolving");
      addLog("STAGE 1/4", `Resolving server endpoint for ${activeProfile} via wlan0...`);

      setTimeout(() => {
        setStage("sslocal");
        addLog("STAGE 2/4", "Launching Shadowsocks core daemon on 127.0.0.1:1080 (chacha20-ietf-poly1305)...");
      }, 350);

      setTimeout(() => {
        setStage("tun0");
        addLog("STAGE 3/4", "Creating tun0 (10.0.0.2/24) & disabling kernel IPv6 leak vectors...");
      }, 700);

      setTimeout(() => {
        setStage("routing");
        addLog("STAGE 4/4", `Hijacking default route -> tun0. Pinned server route via wlan0. DNS -> ${selectedDns.split(" ")[0]}`);
      }, 1050);

      setTimeout(() => {
        setConnecting(false);
        setConnected(true);
        setStage("connected");
        addLog("SUCCESS", "AuraLink connected! 100% full-tunnel + IPv6 shield active.");
      }, 1400);
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
      setConnecting(false);
      setStage("idle");
      setDownloadSpeed("0.0");
      setUploadSpeed("0.0");
      setTotalRecv(0);
      setTotalSent(0);
      setDownSeries(Array(14).fill(0));
      setUpSeries(Array(14).fill(0));
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

  useEffect(() => {
    if (!connected) return;
    let counter = 0;
    const interval = setInterval(() => {
      counter++;
      const downNum = Number((Math.random() * 25 + 38).toFixed(1));
      const upNum = Number((Math.random() * 8 + 8).toFixed(1));
      setDownloadSpeed(downNum.toFixed(1));
      setUploadSpeed(upNum.toFixed(1));
      setTotalRecv((prev) => Number((prev + downNum * 0.12).toFixed(1)));
      setTotalSent((prev) => Number((prev + upNum * 0.12).toFixed(1)));
      setDownSeries((prev) => [...prev.slice(1), downNum]);
      setUpSeries((prev) => [...prev.slice(1), upNum]);

      if (counter % 3 === 0) {
        const sampleHosts = ["1.1.1.1:443", "142.250.190.46:443", "104.21.48.1:443", "151.101.1.140:443"];
        const targetHost = sampleHosts[Math.floor(Math.random() * sampleHosts.length)];
        const bytes = (Math.random() * 64 + 16).toFixed(1);
        addLog("STREAM", `Forwarded ${bytes} KB TCP stream -> ${targetHost} via ss-rust cipher.`);
      }
    }, 1200);
    return () => clearInterval(interval);
  }, [connected]);

  return (
    <section id="simulator" className="py-20 md:py-28 relative overflow-hidden bg-[#f8fafc]">
      <div className="absolute top-1/2 left-1/4 -translate-y-1/2 w-96 h-96 bg-sky-200/35 rounded-full blur-[130px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-200/30 rounded-full blur-[130px] pointer-events-none" />

      <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-14">
          <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-sky-50 border border-sky-200 text-sky-700 text-xs font-bold uppercase tracking-wider mb-3 shadow-xs">
            <Activity className="w-3.5 h-3.5 text-sky-600 animate-pulse" />
            <span>Interactive Desktop Client Demo</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight">
            Try AuraLink Daylight GUI
          </h2>
          <p className="mt-3 text-slate-600 text-sm sm:text-base">
            Experience the light-mode PyQt5 connection switch, live throughput waveforms, IPv6 leak shield, latency probing, and DNS sinkhole controls interactively.
          </p>
        </div>

        {/* Balanced 12-col Desktop Client Simulator */}
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
          {/* LEFT WINDOW (5 cols): Connect Hub + Live Sparklines */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.45 }}
            className="lg:col-span-5 rounded-3xl bg-white border border-slate-200 hover:border-sky-300 p-6 sm:p-7 shadow-xl shadow-slate-900/[0.06] flex flex-col justify-between relative overflow-hidden"
          >
            {/* Top Bar */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-5">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-rose-400" />
                <div className="w-3 h-3 rounded-full bg-amber-400" />
                <div className="w-3 h-3 rounded-full bg-emerald-400" />
                <span className="text-xs font-mono font-bold text-slate-800 ml-2">
                  AuraLink GUI
                </span>
              </div>

              <span
                className={`text-[10.5px] font-mono font-bold tracking-wider px-3 py-1 rounded-full uppercase transition-all ${
                  connected
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : connecting
                    ? "bg-amber-50 text-amber-700 border border-amber-200 animate-pulse"
                    : "bg-slate-100 text-slate-600 border border-slate-200"
                }`}
              >
                {connecting ? "CONNECTING..." : connected ? "CONNECTED" : "DISCONNECTED"}
              </span>
            </div>

            {/* Central Circular Connect Button */}
            <div className="flex flex-col items-center justify-center my-6">
              <div className="relative flex items-center justify-center">
                {connected && (
                  <>
                    <motion.div
                      animate={{ scale: [1, 1.38, 1], opacity: [0.45, 0, 0.45] }}
                      transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
                      className="absolute -inset-5 rounded-full bg-emerald-400/25 blur-xl pointer-events-none"
                    />
                    <motion.div
                      animate={{ scale: [1, 1.22, 1], opacity: [0.75, 0.05, 0.75] }}
                      transition={{ duration: 1.9, repeat: Infinity, ease: "easeInOut" }}
                      className="absolute -inset-3 rounded-full border-2 border-emerald-400/50 pointer-events-none"
                    />
                  </>
                )}

                {connecting && (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1.1, repeat: Infinity, ease: "linear" }}
                    className="absolute -inset-2.5 rounded-full border-2 border-transparent border-t-amber-500 border-r-amber-300 pointer-events-none"
                  />
                )}

                {/* Tactile Click Shockwave Ring */}
                {clickShockwave && (
                  <motion.div
                    key={clickShockwave.id}
                    initial={{ scale: 1, opacity: 0.9 }}
                    animate={{ scale: 1.5, opacity: 0 }}
                    transition={{ duration: 0.65, ease: "easeOut" }}
                    className={`absolute -inset-1 rounded-full border-2 pointer-events-none ${
                      clickShockwave.isDisconnect ? "border-amber-500" : "border-emerald-500"
                    }`}
                  />
                )}

                <motion.button
                  whileHover={{ scale: 1.04 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleToggle}
                  disabled={connecting}
                  className={`w-44 h-44 rounded-full flex flex-col items-center justify-center gap-2.5 font-bold transition-all duration-300 shadow-lg cursor-pointer relative z-10 ${
                    connected
                      ? "bg-gradient-to-b from-white via-emerald-50/70 to-emerald-100/80 text-emerald-800 border-2 border-emerald-500 shadow-emerald-500/20"
                      : connecting
                      ? "bg-gradient-to-b from-white to-amber-50 text-amber-800 border-2 border-amber-400 shadow-amber-500/15"
                      : "bg-gradient-to-b from-white to-slate-50 text-slate-700 hover:text-sky-700 border-2 border-slate-200 hover:border-sky-400 shadow-slate-900/10"
                  }`}
                  aria-label="Toggle VPN Connection"
                >
                  <div
                    className={`p-3.5 rounded-full transition-colors ${
                      connected
                        ? "bg-emerald-100 text-emerald-600"
                        : connecting
                        ? "bg-amber-100 text-amber-600"
                        : "bg-sky-50 text-sky-600"
                    }`}
                  >
                    <Power className="w-9 h-9" />
                  </div>
                  <span className="text-[10.5px] font-mono font-extrabold tracking-widest uppercase px-3 text-center">
                    {connecting ? "CONNECTING..." : connected ? "TAP TO DISCONNECT" : "CLICK TO CONNECT"}
                  </span>
                </motion.button>
              </div>

              <div className="mt-5 flex flex-col items-center gap-1.5 text-center">
                <span className={`text-xs font-mono font-semibold ${connected ? "text-emerald-700" : "text-slate-500"}`}>
                  {connected
                    ? "Virtual tun0 active • 100% full-tunnel routed"
                    : "System using standard physical route"}
                </span>
                {connected && (
                  <motion.span
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-[10.5px] font-mono font-bold text-emerald-700"
                  >
                    <ShieldCheck className="w-3 h-3" />
                    <span>IPv6 Disabled (Zero Leaks)</span>
                  </motion.span>
                )}
              </div>
            </div>

            {/* Interactive 4-Hop Tunnel Model Widget */}
            <div className="mt-3 p-3 rounded-2xl bg-slate-50 border border-slate-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[9px] font-mono font-bold text-slate-500 uppercase tracking-wider">
                  Interactive Tunnel Model
                </span>
                <span
                  className={`text-[9.5px] font-mono font-bold ${
                    connected
                      ? "text-emerald-700"
                      : connecting
                      ? "text-amber-700"
                      : "text-slate-400"
                  }`}
                >
                  {connected
                    ? "LIVE FLOW"
                    : stage === "resolving"
                    ? "1/4: RESOLVING NODE"
                    : stage === "sslocal"
                    ? "2/4: SOCKS5 CORE"
                    : stage === "tun0"
                    ? "3/4: TUNNEL ARMED"
                    : stage === "routing"
                    ? "4/4: SECURING ROUTES"
                    : "IDLE • PHYSICAL ROUTE"}
                </span>
              </div>

              {/* 4-Node Pipeline Flow Graphic */}
              <div className="relative py-2 px-3 flex items-center justify-between">
                {/* Connecting Line Track */}
                <div className="absolute left-8 right-8 top-1/2 -translate-y-1/2 h-0.5 bg-slate-200 z-0">
                  <div
                    className={`h-full transition-all duration-500 ${
                      connected
                        ? "bg-emerald-500 w-full"
                        : stage === "routing"
                        ? "bg-amber-400 w-full"
                        : stage === "tun0"
                        ? "bg-amber-400 w-2/3 ml-1/3"
                        : stage === "sslocal"
                        ? "bg-amber-400 w-1/3 ml-2/3"
                        : "w-0"
                    }`}
                  />
                  {connected && (
                    <div className="absolute inset-0 flex items-center justify-around pointer-events-none overflow-hidden">
                      <motion.div
                        animate={{ x: [-12, 140] }}
                        transition={{ repeat: Infinity, duration: 1.4, ease: "linear" }}
                        className="w-1.5 h-1.5 rounded-full bg-emerald-600 shadow-sm shadow-emerald-500"
                      />
                      <motion.div
                        animate={{ x: [-12, 140] }}
                        transition={{ repeat: Infinity, duration: 1.4, delay: 0.7, ease: "linear" }}
                        className="w-1.5 h-1.5 rounded-full bg-emerald-600 shadow-sm shadow-emerald-500"
                      />
                    </div>
                  )}

                  {/* Traveling photon beam during connect modeling */}
                  {modelingMode === "connecting" && (
                    <motion.div
                      initial={{ left: "0%", width: "24px" }}
                      animate={{ left: "100%", width: "24px" }}
                      transition={{ duration: 1.25, ease: "easeInOut" }}
                      className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 h-2 rounded-full bg-emerald-400 shadow-lg shadow-emerald-400/80 pointer-events-none"
                    />
                  )}

                  {/* Dissolution teardown sweep during disconnect modeling */}
                  {modelingMode === "disconnecting" && (
                    <motion.div
                      initial={{ right: "0%", width: "28px" }}
                      animate={{ right: "100%", width: "28px" }}
                      transition={{ duration: 1.05, ease: "easeInOut" }}
                      className="absolute top-1/2 -translate-y-1/2 translate-x-1/2 h-2 rounded-full bg-amber-400/90 shadow-md shadow-amber-500/50 pointer-events-none"
                    />
                  )}
                </div>

                {/* 4 Nodes */}
                {[
                  { id: "apps", label: "Linux Apps", tag: "TCP/UDP" },
                  { id: "tun0", label: "tun0 L3", tag: "10.0.0.2" },
                  { id: "sslocal", label: "sslocal", tag: "AEAD" },
                  { id: "server", label: "VPN Node", tag: "WAN" },
                ].map((node, idx) => {
                  const isSelected = selectedTunnelNode === idx;
                  const isNodeActive =
                    connected ||
                    (stage === "routing" && idx <= 3) ||
                    (stage === "tun0" && idx >= 1) ||
                    (stage === "sslocal" && idx >= 2) ||
                    (stage === "resolving" && idx === 3) ||
                    (stage === "idle" && (idx === 0 || idx === 3));
                  const nodeBurst = activeNodeRipples[idx];

                  return (
                    <button
                      key={node.id}
                      onClick={() => {
                        setSelectedTunnelNode(idx);
                        setActiveNodeRipples((prev) => ({ ...prev, [idx]: Date.now() }));
                      }}
                      className="relative z-10 flex flex-col items-center gap-1 cursor-pointer focus:outline-hidden"
                    >
                      {/* Acoustic Shockwave Burst / Click Ripple */}
                      <AnimatePresence>
                        {nodeBurst && (
                          <motion.div
                            key={nodeBurst}
                            initial={{ scale: 1, opacity: 0.9 }}
                            animate={{ scale: 2.2, opacity: 0 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.55, ease: "easeOut" }}
                            className="absolute -inset-1 rounded-full border-2 border-sky-400 pointer-events-none"
                          />
                        )}
                        {modelingMode === "connecting" && (
                          <motion.div
                            initial={{ scale: 1, opacity: 0 }}
                            animate={{ scale: [1, 2.1], opacity: [0.85, 0] }}
                            transition={{ delay: idx * 0.32, duration: 0.6, ease: "easeOut" }}
                            className="absolute -inset-1 rounded-full border-2 border-emerald-400 pointer-events-none"
                          />
                        )}
                        {modelingMode === "disconnecting" && (
                          <motion.div
                            initial={{ scale: 1, opacity: 0 }}
                            animate={{ scale: [1, 2.0], opacity: [0.85, 0] }}
                            transition={{ delay: (3 - idx) * 0.25, duration: 0.55, ease: "easeOut" }}
                            className="absolute -inset-1 rounded-full border-2 border-amber-400 pointer-events-none"
                          />
                        )}
                      </AnimatePresence>

                      <motion.div
                        whileTap={{ scale: 0.88 }}
                        animate={isSelected ? { scale: [1, 1.12, 1] } : {}}
                        transition={{ duration: 0.28 }}
                        className={`w-7 h-7 rounded-full flex items-center justify-center transition-all duration-300 relative ${
                          isSelected ? "ring-4 ring-sky-100" : ""
                        } ${
                          connected
                            ? "bg-white border-2 border-emerald-500 shadow-sm shadow-emerald-500/20"
                            : connecting && isNodeActive
                            ? "bg-white border-2 border-amber-500 shadow-sm shadow-amber-500/20"
                            : isSelected
                            ? "bg-white border-2 border-sky-500"
                            : "bg-white border border-slate-300"
                        }`}
                      >
                        <div
                          className={`w-2 h-2 rounded-full transition-colors ${
                            connected
                              ? "bg-emerald-600"
                              : connecting && isNodeActive
                              ? "bg-amber-600 animate-pulse"
                              : isSelected
                              ? "bg-sky-600"
                              : "bg-slate-400"
                          }`}
                        />
                      </motion.div>
                      <span
                        className={`text-[9.5px] font-mono font-bold leading-none ${
                          isSelected ? "text-slate-900" : "text-slate-500"
                        }`}
                      >
                        {node.label}
                      </span>
                    </button>
                  );
                })}
              </div>

              {/* Inspector Pill */}
              <div
                className={`mt-2.5 px-3 py-1.5 rounded-lg border text-[10.5px] font-mono transition-colors ${
                  connected
                    ? "bg-emerald-50/70 border-emerald-200 text-emerald-800"
                    : connecting
                    ? "bg-amber-50/70 border-amber-200 text-amber-800"
                    : "bg-slate-100/80 border-slate-200 text-slate-700"
                }`}
              >
                {selectedTunnelNode === 0 && (
                  <span>
                    {connected
                      ? `Linux Apps • 100% Full-Tunnel Captured • DNS ${selectedDns.split(" ")[0]} • Live: ↓ ${downloadSpeed} MB/s`
                      : connecting
                      ? "Linux Apps • Preparing kernel default route switch -> tun0 (10.0.0.2/24)"
                      : "Linux Apps • Direct Physical Route • Gateway: 192.168.1.1 (wlan0) • Standard DNS"}
                  </span>
                )}
                {selectedTunnelNode === 1 && (
                  <span>
                    {connected
                      ? `tun0 L3 • 10.0.0.2/24 • IPv6 Shield Active • Recv: ${totalRecv} MB`
                      : connecting
                      ? "tun0 L3 • Provisioning Layer 3 interface & IPv6 leak shield..."
                      : "tun0 L3 • Interface Standby • IPv6 Guard Ready • 10.0.0.2/24"}
                  </span>
                )}
                {selectedTunnelNode === 2 && (
                  <span>
                    {connected
                      ? "sslocal • SOCKS5 127.0.0.1:1080 • Cipher: chacha20-ietf-poly1305 • ss-rust daemon"
                      : connecting
                      ? "sslocal • Launching SOCKS5 proxy daemon on 127.0.0.1:1080 with AEAD cipher..."
                      : "sslocal • SOCKS5 Daemon Stopped • Configured for 127.0.0.1:1080"}
                  </span>
                )}
                {selectedTunnelNode === 3 && (
                  <span>
                    {connected
                      ? `VPN Node • ${activeProfile} (198.51.100.42:8443) • Latency: ${ping}ms • WAN Encrypted`
                      : connecting
                      ? `VPN Node • Resolving ${activeProfile} & handshaking via physical gateway...`
                      : `VPN Node • ${activeProfile} (198.51.100.42:8443) • Latency: ${ping}ms • Standby`}
                  </span>
                )}
              </div>
            </div>

            {/* Live Speed Cards with Animated Sparklines */}
            <div className="grid grid-cols-2 gap-3 mt-3">
              <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-sky-100 border border-sky-200 flex items-center justify-center text-sky-600 shrink-0">
                      <ArrowDown className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider font-bold">
                        Download
                      </div>
                      <div className="text-base font-mono font-extrabold text-slate-900">
                        {downloadSpeed} <span className="text-[11px] text-slate-500">MB/s</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-[8.5px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                      Session Recv
                    </div>
                    <div className="text-[11px] font-mono font-bold text-slate-600">
                      {totalRecv} MB
                    </div>
                  </div>
                </div>
                <Sparkline values={downSeries} stroke="#0284c7" fillId="dlGrad" />
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-emerald-100 border border-emerald-200 flex items-center justify-center text-emerald-600 shrink-0">
                      <ArrowUp className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider font-bold">
                        Upload
                      </div>
                      <div className="text-base font-mono font-extrabold text-slate-900">
                        {uploadSpeed} <span className="text-[11px] text-slate-500">MB/s</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-[8.5px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                      Session Sent
                    </div>
                    <div className="text-[11px] font-mono font-bold text-slate-600">
                      {totalSent} MB
                    </div>
                  </div>
                </div>
                <Sparkline values={upSeries} stroke="#059669" fillId="ulGrad" />
              </div>
            </div>
          </motion.div>

          {/* RIGHT PANEL (7 cols): Node Controls & Live Log Stream */}
          <div className="lg:col-span-7 flex flex-col gap-6">
            {/* Control Deck */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.45, delay: 0.08 }}
              className="p-5 sm:p-6 rounded-3xl bg-white border border-slate-200 shadow-xl shadow-slate-900/[0.05] space-y-4"
            >
              <div className="flex items-center justify-between flex-wrap gap-2">
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-700">
                  ACTIVE SUBSCRIPTION NODE
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handlePingTest}
                    disabled={pinging || !activeProfile}
                    className="flex items-center gap-1.5 text-xs font-mono font-bold text-sky-700 hover:text-sky-800 px-3 py-1.5 rounded-xl bg-sky-50 border border-sky-200 hover:border-sky-400 transition-all cursor-pointer disabled:opacity-40"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${pinging ? "animate-spin" : ""}`} />
                    <span>Ping: {activeProfile ? `${ping}ms` : "--"}</span>
                  </button>
                  <button
                    onClick={() => setShowDeleteModal(true)}
                    disabled={servers.length === 0 || !activeProfile}
                    className="group flex items-center gap-1.5 text-xs font-mono font-bold text-rose-600 hover:text-rose-700 px-3 py-1.5 rounded-xl bg-rose-50 hover:bg-rose-100 border border-rose-200 transition-all cursor-pointer disabled:opacity-40"
                    title="Delete currently selected server profile"
                  >
                    <Trash2 className="w-3.5 h-3.5 transition-transform group-hover:scale-110" />
                    <span>Delete</span>
                  </button>
                </div>
              </div>

              {servers.length > 0 ? (
                <div className="grid grid-cols-3 gap-2.5 text-xs font-medium">
                  {servers.map((node) => {
                    const isActive = activeProfile === node;
                    return (
                      <motion.button
                        key={node}
                        whileHover={{ y: -1 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => {
                          setActiveProfile(node);
                          addLog("PROFILE", `Switched active node to ${node}.`);
                        }}
                        className={`py-2.5 px-2 rounded-xl text-center font-mono text-[11px] font-bold transition-all cursor-pointer ${
                          isActive
                            ? "bg-sky-600 text-white border border-sky-600 shadow-md shadow-sky-600/20"
                            : "bg-slate-50 text-slate-600 hover:text-sky-700 hover:bg-sky-50 border border-slate-200"
                        }`}
                      >
                        {node}
                      </motion.button>
                    );
                  })}
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-slate-50 border border-dashed border-slate-300 text-center space-y-2">
                  <span className="text-xs font-mono text-slate-500 block">
                    No server profiles remaining.
                  </span>
                  <button
                    onClick={handleResetServers}
                    className="inline-flex items-center gap-1.5 text-[11px] font-mono font-bold text-sky-700 hover:text-sky-800 px-3 py-1.5 rounded-lg bg-sky-50 border border-sky-200 transition-colors cursor-pointer"
                  >
                    <RotateCcw className="w-3 h-3" />
                    <span>Restore Default Nodes</span>
                  </button>
                </div>
              )}

              {/* DNS Upstream Resolver */}
              <div>
                <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-500 block mb-2">
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
                    className="w-full appearance-none bg-slate-50 border border-slate-200 hover:border-sky-400 rounded-xl px-3.5 py-2.5 text-xs font-mono text-slate-800 focus:outline-none focus:border-sky-500 transition-colors cursor-pointer font-medium"
                  >
                    <option>Cloudflare (1.1.1.1 / 1.0.0.1)</option>
                    <option>Google (8.8.8.8 / 8.8.4.4)</option>
                    <option>Quad9 (9.9.9.9 / 149.112.112.112)</option>
                    <option>AdGuard (94.140.14.14 / 94.140.15.15)</option>
                  </select>
                  <ChevronDown className="w-4 h-4 text-slate-500 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </div>
            </motion.div>

            {/* Real-Time Log Stream */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.45, delay: 0.14 }}
              className="p-5 sm:p-6 rounded-3xl bg-white border border-slate-200 font-mono text-xs text-slate-700 flex-1 flex flex-col justify-between shadow-xl shadow-slate-900/[0.05]"
            >
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3 text-[11px]">
                <div className="flex items-center gap-1.5 font-bold text-slate-800">
                  <Terminal className="w-3.5 h-3.5 text-sky-600" />
                  <span>Real-Time Log Stream</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setLogs([])}
                    className="px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 font-mono text-[9.5px] font-bold transition-colors cursor-pointer"
                  >
                    Clear
                  </button>
                  <button
                    onClick={() => setLogWrap(!logWrap)}
                    className="px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 font-mono text-[9.5px] font-bold transition-colors cursor-pointer"
                  >
                    {logWrap ? "Wrap: On" : "Wrap: Off"}
                  </button>
                  <span className="text-[10px] text-emerald-600 font-bold flex items-center gap-1.5 ml-1">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                    LIVE
                  </span>
                </div>
              </div>

              <div
                suppressHydrationWarning
                className={`space-y-1 overflow-y-auto max-h-[168px] text-[10.5px] scrollbar-thin p-3 rounded-xl bg-slate-50 border border-slate-200/80 font-mono ${
                  logWrap ? "whitespace-normal break-words" : "whitespace-nowrap overflow-x-auto"
                }`}
              >
                {logs.map((log, index) => {
                  const m = log.match(/^\[([^\]]+)\]\s*(?:\[([^\]]+)\]\s*)?(.*)$/);
                  const time = m ? m[1] : "";
                  const tag = m && m[2] ? m[2] : "SYSTEM";
                  const msg = m && m[2] ? m[3] : (m ? m[3] : log);

                  const tagLower = tag.toLowerCase();
                  const isSuccess = tagLower.includes("success") || tagLower.includes("ipv6");
                  const isWarn = tagLower.includes("disconnect") || tagLower.includes("warn");
                  const isNet = tagLower.includes("sslocal") || tagLower.includes("routing") || tagLower.includes("tun") || tagLower.includes("dns");

                  return (
                    <div key={index} className="flex items-center gap-2 py-0.5 leading-relaxed">
                      {time && <span className="text-slate-400">[{time}]</span>}
                      <span
                        className={`font-bold px-1.5 py-0.5 rounded text-[9.5px] uppercase ${
                          isSuccess
                            ? "bg-emerald-100/80 text-emerald-700"
                            : isWarn
                            ? "bg-amber-100/80 text-amber-700"
                            : isNet
                            ? "bg-sky-100/80 text-sky-700"
                            : "bg-indigo-100/80 text-indigo-700"
                        }`}
                      >
                        [{tag}]
                      </span>
                      <span className="text-slate-700">{msg}</span>
                    </div>
                  );
                })}
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 text-[10.5px] text-slate-500 flex items-center justify-between">
                <span>Direct /proc/net/dev telemetry</span>
                <span className="text-sky-700 font-mono font-bold">127.0.0.1:1080</span>
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Light Theme Delete Confirmation Modal */}
      <AnimatePresence>
        {showDeleteModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowDeleteModal(false)}
              className="absolute inset-0 bg-slate-900/35 backdrop-blur-sm"
            />

            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ duration: 0.16 }}
              className="relative w-full max-w-md bg-white border border-rose-200 rounded-2xl p-6 shadow-2xl space-y-4 z-10"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600">
                    <Trash2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-900 font-mono">
                      Delete Server Profile
                    </h3>
                    <p className="text-xs text-slate-500">
                      Are you sure you want to remove this profile?
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowDeleteModal(false)}
                  className="text-slate-400 hover:text-slate-700 p-1 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="text-xs font-mono font-semibold text-slate-700">
                  Profile: <span className="text-slate-900 font-bold">{activeProfile}</span>
                </div>
                <div className="flex flex-wrap gap-2 text-[11px] font-mono">
                  <span className="px-2 py-0.5 rounded-md bg-sky-50 text-sky-700 border border-sky-200">
                    🌐 198.51.100.42:8443
                  </span>
                  <span className="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200">
                    🔒 chacha20-ietf-poly1305
                  </span>
                </div>
              </div>

              {connected && (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <p className="text-[11px] text-rose-800 font-medium leading-relaxed">
                    <strong className="font-bold">Active Tunnel Warning:</strong> Deleting this active server will terminate the tunnel and restore your physical route.
                  </p>
                </div>
              )}

              {servers.length === 1 && !connected && (
                <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <p className="text-[11px] text-amber-900 font-medium leading-relaxed">
                    This is your only remaining server profile. You can restore defaults afterwards.
                  </p>
                </div>
              )}

              <div className="flex items-center justify-end gap-2.5 pt-2">
                <button
                  onClick={() => setShowDeleteModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-all text-xs font-bold font-mono cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    setShowDeleteModal(false);
                    handleDeleteServer();
                  }}
                  className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs font-mono shadow-sm flex items-center gap-1.5 transition-all cursor-pointer"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Delete Profile</span>
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </section>
  );
}
