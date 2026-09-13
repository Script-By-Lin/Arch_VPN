import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AuraLink — Universal Shadowsocks & tun2socks VPN Client for Linux",
  description: "Next-generation high-performance VPN client for Arch Linux, Debian, Ubuntu, Fedora, and openSUSE. Full TUN kernel routing, anti-censorship prefixes, and zero-leak DNS.",
  keywords: ["AuraLink", "Shadowsocks", "tun2socks", "Linux VPN", "Arch Linux", "CachyOS", "Debian", "Ubuntu", "Fedora", "DPI Bypass", "Anti-Censorship", "ssconf"],
  authors: [{ name: "Script-By-Lin" }],
  icons: {
    icon: "/icon.png",
    apple: "/icon.png",
  },
  openGraph: {
    title: "AuraLink — Universal Shadowsocks & tun2socks VPN Client for Linux",
    description: "High-performance TUN-based VPN client with anti-censorship TLS prefixes and zero-leak DNS for all Linux distributions.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex flex-col bg-[#07090e] text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-200">
        {children}
      </body>
    </html>
  );
}
