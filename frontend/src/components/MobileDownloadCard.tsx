"use client";

import React, { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Smartphone,
  Download,
  ShieldCheck,
  RefreshCw,
  Copy,
  Check,
  Globe,
  Loader2,
} from "lucide-react";

const MOBILE_BACKEND_URL = (
  process.env.NEXT_PUBLIC_MOBILE_BACKEND_URL ||
  "https://archvpn-production.up.railway.app"
).replace(/\/+$/, "");

interface MobileReleaseInfo {
  available: boolean;
  platform: string;
  version: string;
  download_url: string;
  direct_endpoint?: string;
  filename: string;
  size_bytes: number;
  sha256: string;
  release_notes: string;
  hosted_locally?: boolean;
  updated_at: string;
}

function formatBytes(bytes: number): string {
  if (!bytes || bytes <= 0) return "";
  const mb = bytes / (1024 * 1024);
  if (mb >= 1) return `${mb.toFixed(1)} MB`;
  return `${Math.round(bytes / 1024)} KB`;
}

export default function MobileDownloadCard() {
  const [release, setRelease] = useState<MobileReleaseInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedSha, setCopiedSha] = useState<boolean>(false);

  const fetchRelease = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${MOBILE_BACKEND_URL}/api/mobile/release`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data: MobileReleaseInfo = await res.json();
      setRelease(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to reach release backend");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRelease();
  }, [fetchRelease]);

  const handleCopySha = () => {
    if (!release?.sha256) return;
    navigator.clipboard.writeText(release.sha256);
    setCopiedSha(true);
    setTimeout(() => setCopiedSha(false), 2000);
  };

  const sizeLabel = release ? formatBytes(release.size_bytes) : "";

  return (
    <motion.div
      id="mobile-download"
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.35 }}
      className="p-6 rounded-2xl bg-gradient-to-br from-sky-50/90 via-white to-emerald-50/70 border border-sky-200/90 shadow-sm space-y-4"
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="w-12 h-12 rounded-2xl bg-sky-100 border border-sky-200 flex items-center justify-center text-sky-700 flex-shrink-0">
            <Smartphone className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-lg sm:text-xl font-extrabold text-slate-900">
                AuraLink Mobile for Android
              </h3>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                {release?.version ? `v${release.version}` : "APK"}
              </span>
              {sizeLabel && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-white text-slate-600 border border-slate-200">
                  {sizeLabel}
                </span>
              )}
            </div>
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed max-w-2xl">
              {release?.release_notes ||
                "Native Android VpnService (Shadowsocks-Rust + tun2socks ARM64) with IPv6 Leak Shield, 5-stage verified tunnel, and live Free Region Cards."}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {loading ? (
            <div className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-slate-100 border border-slate-200 text-slate-600 text-xs font-bold">
              <Loader2 className="w-4 h-4 animate-spin text-sky-600" />
              <span>Checking latest APK...</span>
            </div>
          ) : release?.available && release.download_url ? (
            <motion.a
              whileHover={{ y: -2, scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              href={release.download_url}
              download={release.filename || "AuraLink-VPN-Android.apk"}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-xl font-bold text-sm text-white bg-gradient-to-r from-sky-600 via-teal-600 to-emerald-600 hover:from-sky-500 hover:to-emerald-500 shadow-md shadow-sky-600/20 transition-all"
            >
              <Download className="w-4 h-4" />
              <span>Download Android APK</span>
            </motion.a>
          ) : (
            <button
              type="button"
              onClick={fetchRelease}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 text-xs font-bold cursor-pointer transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>
                {error ? "Retry Release Check" : "APK Pending Upload"}
              </span>
            </button>
          )}
        </div>
      </div>

      {/* Bottom Metadata & Live Backend Status Bar */}
      <div className="pt-3 border-t border-slate-200/80 flex flex-wrap items-center justify-between gap-3 text-[11px] font-mono text-slate-500">
        <div className="flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-1.5 text-emerald-700 font-semibold">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>ARM64 Native TUN + IPv6 Shield</span>
          </span>
          <span className="inline-flex items-center gap-1.5 text-sky-700 font-semibold">
            <Globe className="w-3.5 h-3.5" />
            <span>Live Link from Backend</span>
          </span>
        </div>

        {release?.sha256 && (
          <button
            type="button"
            onClick={handleCopySha}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white border border-slate-200 hover:border-sky-300 text-slate-600 hover:text-sky-700 cursor-pointer transition-colors"
            title="Copy APK SHA-256 checksum"
          >
            {copiedSha ? (
              <>
                <Check className="w-3 h-3 text-emerald-600" />
                <span className="text-emerald-700 font-bold">SHA-256 Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                <span>SHA-256: {release.sha256.slice(0, 12)}...</span>
              </>
            )}
          </button>
        )}
      </div>
    </motion.div>
  );
}
