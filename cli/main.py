#!/usr/bin/env python3
"""
CLI Interface for ShadowTun Linux VPN.
Provides rich interactive and non-interactive command line management.
"""

import os
import sys
import time
import argparse

# Add project root to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core import (
    VPNService,
    ConfigManager,
    ConfigError,
    StatsMonitor,
    STATE_CONNECTED,
    STATE_CONNECTING,
    STATE_DISCONNECTED,
    STATE_DISCONNECTING,
    STATE_ERROR
)

# ANSI Color Codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_banner():
    print(f"""{CYAN}{BOLD}
    ╔═══════════════════════════════════════════════╗
    ║          ShadowTun Linux VPN Client           ║
    ║   Cross-Distro Shadowsocks + tun2socks VPN    ║
    ╚═══════════════════════════════════════════════╝{RESET}
""")


def cmd_connect(args, service: VPNService):
    target = args.target
    print(f"{CYAN}[*]{RESET} Preparing connection...")

    def on_event(event_type: str, data: dict):
        msg = data.get("message", "")
        if event_type == "progress":
            print(f"  {DIM}→{RESET} {msg}")
        elif event_type == "connected":
            print(f"{GREEN}{BOLD}[✓] Connected successfully!{RESET}")
            prof = data.get("profile", {})
            print(f"    Profile : {BOLD}{prof.get('name')}{RESET}")
            print(f"    Server  : {prof.get('server')}:{prof.get('server_port')}")
            print(f"    TUN Dev : {data.get('tun_dev')}")
        elif event_type == "error":
            print(f"{RED}{BOLD}[✗] Connection failed:{RESET} {data.get('error')}")

    service.add_listener(on_event)
    success = service.connect(target)
    if not success:
        sys.exit(1)

    if args.monitor:
        print(f"\n{CYAN}[i]{RESET} Monitoring live traffic (Ctrl+C to stop monitor, VPN stays up)...")
        try:
            while service.state == STATE_CONNECTED:
                stats = service.get_stats()
                print(f"\r  {GREEN}● UP{RESET} | Dur: {stats['duration_str']} | ↓ {stats['rx_speed_str']} ({stats['rx_total_str']}) | ↑ {stats['tx_speed_str']} ({stats['tx_total_str']})   ", end="", flush=True)
                time.sleep(1.0)
        except KeyboardInterrupt:
            print("\nExiting monitor.")


def cmd_disconnect(args, service: VPNService):
    print(f"{YELLOW}[*]{RESET} Disconnecting VPN...")
    def on_event(event_type: str, data: dict):
        if event_type == "disconnected":
            print(f"{GREEN}{BOLD}[✓] Disconnected successfully. Default routes and DNS restored.{RESET}")
        elif event_type == "error":
            print(f"{RED}{BOLD}[✗] Disconnect error:{RESET} {data.get('error')}")

    service.add_listener(on_event)
    success = service.disconnect()
    if not success:
        sys.exit(1)


def cmd_status(args, service: VPNService):
    state = service.state
    state_color = GREEN if state == STATE_CONNECTED else (YELLOW if state in (STATE_CONNECTING, STATE_DISCONNECTING) else RED)

    print(f"\n{BOLD}VPN Status:{RESET} {state_color}{BOLD}{state}{RESET}")

    if state == STATE_CONNECTED:
        prof = service.active_profile
        if prof:
            print(f"  Profile : {BOLD}{prof.get('name')}{RESET} (ID: {prof.get('id')})")
            print(f"  Server  : {prof.get('server')}:{prof.get('server_port')}")
            print(f"  Method  : {prof.get('method')}")
        
        stats = service.get_stats()
        print(f"  Uptime  : {stats['duration_str']}")
        print(f"  Download: {BOLD}{stats['rx_total_str']}{RESET} ({stats['rx_speed_str']})")
        print(f"  Upload  : {BOLD}{stats['tx_total_str']}{RESET} ({stats['tx_speed_str']})")
    elif service.last_error:
        print(f"  Last Err: {RED}{service.last_error}{RESET}")
    print("")


def cmd_import(args, service: VPNService):
    key = args.key
    cm = service.config_mgr
    print(f"{CYAN}[*]{RESET} Parsing and fetching key: {key[:50]}...")
    try:
        profile = cm.parse_key(key)
        saved = cm.add_or_update_profile(profile)
        print(f"{GREEN}{BOLD}[✓] Successfully imported profile!{RESET}")
        print(f"    ID     : {saved['id']}")
        print(f"    Name   : {BOLD}{saved['name']}{RESET}")
        print(f"    Server : {saved['server']}:{saved['server_port']}")
        print(f"    Method : {saved['method']}")
        if saved.get("prefix"):
            print(f"    Prefix : Enabled (Anti-Censorship)")
        print(f"\nTo connect: {BOLD}shadowtun-vpn connect {saved['id']}{RESET}")
    except ConfigError as e:
        print(f"{RED}{BOLD}[✗] Import failed:{RESET}\n{e}")
        sys.exit(1)


def cmd_list(args, service: VPNService):
    profiles = service.config_mgr.get_profiles()
    settings = service.config_mgr.get_settings()
    active_id = settings.get("active_profile_id")

    if not profiles:
        print(f"{YELLOW}No saved profiles.{RESET} Import one using: {BOLD}shadowtun-vpn import <key>{RESET}")
        return

    print(f"\n{BOLD}Saved VPN Profiles ({len(profiles)}):{RESET}")
    print(f"{'ID':<10} {'NAME':<32} {'SERVER':<22} {'PORT':<6} {'STATUS'}")
    print("-" * 78)

    for p in profiles:
        p_id = p.get("id", "")
        name = (p.get("name") or "Unnamed")[:30]
        server = (p.get("server") or "")[:20]
        port = str(p.get("server_port") or 443)
        status = ""
        if p_id == active_id and service.state == STATE_CONNECTED:
            status = f"{GREEN}● ACTIVE{RESET}"
        elif p_id == active_id:
            status = f"{CYAN}SELECTED{RESET}"

        print(f"{p_id:<10} {name:<32} {server:<22} {port:<6} {status}")
    print("")


def cmd_delete(args, service: VPNService):
    target = args.target
    cm = service.config_mgr
    prof = cm.get_profile_by_id(target) or cm.get_profile_by_name(target)
    if not prof:
        print(f"{RED}[✗] Profile not found:{RESET} {target}")
        sys.exit(1)

    if cm.delete_profile(prof["id"]):
        print(f"{GREEN}[✓] Deleted profile:{RESET} {prof.get('name')} ({prof['id']})")
    else:
        print(f"{RED}[✗] Failed to delete profile.{RESET}")


def cmd_test(args, service: VPNService):
    cm = service.config_mgr
    target = args.target
    profiles = []
    if target:
        p = cm.get_profile_by_id(target) or cm.get_profile_by_name(target)
        if not p:
            print(f"{RED}[✗] Profile not found:{RESET} {target}")
            sys.exit(1)
        profiles = [p]
    else:
        profiles = cm.get_profiles()

    if not profiles:
        print(f"{YELLOW}No profiles to test.{RESET}")
        return

    print(f"{CYAN}[*]{RESET} Testing server latencies...")
    for p in profiles:
        server = p.get("server")
        port = p.get("server_port", 443)
        print(f"  Pinging {p.get('name')} ({server}:{port})... ", end="", flush=True)
        ping = StatsMonitor.measure_ping(server, port, timeout=3.0)
        if ping is not None:
            color = GREEN if ping < 150 else (YELLOW if ping < 350 else RED)
            print(f"{color}{BOLD}{ping} ms{RESET}")
        else:
            print(f"{RED}Unreachable / Timeout{RESET}")


def format_log_entry(line: str) -> str:
    if line.startswith("[sslocal]"):
        return f"{CYAN}[sslocal]{RESET}" + line[len("[sslocal]"):]
    elif line.startswith("[tun2socks]"):
        return f"{YELLOW}[tun2socks]{RESET}" + line[len("[tun2socks]"):]
    return line


def cmd_logs(args, service: VPNService):
    if args.follow:
        print(f"{CYAN}[*]{RESET} Streaming real-time VPN logs (Ctrl+C to stop)...")
        try:
            for line in service.process_mgr.follow_logs(max_lines=args.lines):
                print(format_log_entry(line), flush=True)
        except KeyboardInterrupt:
            print(f"\n{DIM}Stopped following logs.{RESET}")
    else:
        logs = service.process_mgr.get_recent_logs(max_lines=args.lines)
        if not logs:
            print(f"{DIM}No log entries found.{RESET}")
            return
        print(f"{BOLD}Recent VPN Logs:{RESET}")
        for line in logs:
            print(format_log_entry(line))


def cmd_gui(args, service: VPNService):
    try:
        from gui.app import launch_gui
        launch_gui()
    except ImportError as e:
        print(f"{RED}[✗] GUI failed to launch: {e}{RESET}")
        print("Please ensure PyQt5 is installed: sudo pacman -S python-pyqt5 (Arch) or sudo apt install python3-pyqt5 (Debian/Ubuntu)")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="ShadowTun Linux VPN Client",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Connect / Switch
    p_conn = subparsers.add_parser("connect", help="Connect to VPN (by key, profile ID, or name)")
    p_conn.add_argument("target", nargs="?", help="ssconf:// URL, ss:// URI, Profile ID, or Name")
    p_conn.add_argument("-m", "--monitor", action="store_true", help="Keep running and stream live traffic stats")

    # Switch (Alias for connect)
    p_switch = subparsers.add_parser("switch", help="Switch VPN server (by Profile ID or Name)")
    p_switch.add_argument("target", help="Profile ID or Name to switch to")
    p_switch.add_argument("-m", "--monitor", action="store_true", help="Keep running and stream live traffic stats")

    # Disconnect
    subparsers.add_parser("disconnect", help="Disconnect active VPN")

    # Status
    subparsers.add_parser("status", help="Show current VPN status, stats, and active server")

    # Import
    p_import = subparsers.add_parser("import", help="Import a new key (ssconf://, ss://, json)")
    p_import.add_argument("key", help="The key / URL string to import")

    # List
    subparsers.add_parser("list", help="List all saved profiles")

    # Delete
    p_del = subparsers.add_parser("delete", help="Delete a saved profile")
    p_del.add_argument("target", help="Profile ID or Name")

    # Test
    p_test = subparsers.add_parser("test", help="Test latency / ping to server(s)")
    p_test.add_argument("target", nargs="?", help="Profile ID or Name (optional)")

    # Logs
    p_logs = subparsers.add_parser("logs", help="View recent VPN core logs")
    p_logs.add_argument("-n", "--lines", type=int, default=40, help="Number of log lines to show")
    p_logs.add_argument("-f", "--follow", action="store_true", help="Follow log stream in real time")

    # GUI
    subparsers.add_parser("gui", help="Launch the Modern Desktop GUI")

    args = parser.parse_args()

    service = VPNService()

    if args.command in ("connect", "switch"):
        cmd_connect(args, service)
    elif args.command == "disconnect":
        cmd_disconnect(args, service)
    elif args.command == "status":
        cmd_status(args, service)
    elif args.command == "import":
        cmd_import(args, service)
    elif args.command == "list":
        cmd_list(args, service)
    elif args.command == "delete":
        cmd_delete(args, service)
    elif args.command == "test":
        cmd_test(args, service)
    elif args.command == "logs":
        cmd_logs(args, service)
    elif args.command == "gui" or args.command is None:
        if args.command is None:
            # If run without arguments in an interactive terminal, if DISPLAY is set, launch GUI; else show help
            if "DISPLAY" in os.environ or "WAYLAND_DISPLAY" in os.environ:
                cmd_gui(args, service)
            else:
                print_banner()
                parser.print_help()
        else:
            cmd_gui(args, service)
    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Exiting...")
        sys.exit(0)
