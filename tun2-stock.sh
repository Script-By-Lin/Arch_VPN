#!/usr/bin/env bash
# ==============================================================================
# AuraLink Standalone Shell Engine
# Supports direct ssconf:// URL parsing, automatic DNS resolution,
# and robust TUN routing.
# ==============================================================================
set -euo pipefail

CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/shadowsocks"
CONFIG="${CONFIG:-$CONFIG_DIR/config.json}"
TUN="${TUN:-tun0}"
SOCKS="${SOCKS:-127.0.0.1:1080}"
DNS="${DNS:-1.1.1.1}"
DNS_BACKUP="${DNS_BACKUP:-8.8.8.8}"
STATE_DIR="${XDG_RUNTIME_DIR:-/tmp}/tun2socks-vpn"

mkdir -p "$CONFIG_DIR" "$STATE_DIR"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "[ERROR] Missing required command: $1"; exit 1; }
}

need jq; need sslocal; need tun2socks; need ip; need curl

# Check if an ssconf:// or http URL is supplied
fetch_and_prepare_config() {
  local KEY_OR_FILE="${1:-}"
  if [[ -z "$KEY_OR_FILE" ]]; then
    if [[ ! -f "$CONFIG" ]]; then
      echo "[ERROR] No config found at $CONFIG and no ssconf:// key provided."
      echo "Usage: $0 start [ssconf://... | config.json]"
      exit 1
    fi
    return 0
  fi

  if [[ "$KEY_OR_FILE" =~ ^ssconf:// ]]; then
    local URL="${KEY_OR_FILE#ssconf://}"
    URL="${URL%%#*}" # Strip anchor
    if [[ ! "$URL" =~ ^https?:// ]]; then
      URL="https://$URL"
    fi
    echo "[+] Fetching Shadowsocks config from $URL..."
    local RAW_JSON
    RAW_JSON=$(curl -sSL -k "$URL")
    
    # Check for error in JSON
    if echo "$RAW_JSON" | jq -e '.error' >/dev/null 2>&1; then
      echo "[ERROR] Subscription server returned an error:"
      echo "$RAW_JSON" | jq -r '.error.message // .error'
      exit 1
    fi

    # Inject local_address and local_port
    echo "$RAW_JSON" | jq '. + {"local_address": "127.0.0.1", "local_port": 1080}' > "$CONFIG"
    echo "[✓] Saved active config to $CONFIG"
  elif [[ -f "$KEY_OR_FILE" ]]; then
    jq '. + {"local_address": "127.0.0.1", "local_port": 1080}' "$KEY_OR_FILE" > "$CONFIG"
    echo "[✓] Loaded config from $KEY_OR_FILE into $CONFIG"
  fi
}

server_host() { jq -r .server "$CONFIG"; }

resolve_ip() {
  local HOST="$1"
  if [[ "$HOST" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "$HOST"
  else
    getent ahosts "$HOST" 2>/dev/null | awk '/STREAM/ {print $1; exit}' || echo "$HOST"
  fi
}

wifi_gw() {
  ip -4 route show default 2>/dev/null | awk '/default/ && $0 !~ /'"$TUN"'/ && /via/ {print $3; exit}' || \
  ip -4 route get 1.1.1.1 2>/dev/null | awk '{print $3; exit}'
}

wifi_dev() {
  ip -4 route show default 2>/dev/null | awk '/default/ && $0 !~ /'"$TUN"'/ && /dev/ {print $5; exit}' || \
  ip -4 route get 1.1.1.1 2>/dev/null | awk '{print $5; exit}'
}

wait_port() {
  local HOST="${SOCKS%:*}"
  local PORT="${SOCKS##*:}"
  for _ in $(seq 1 25); do
    if bash -c "echo >/dev/tcp/$HOST/$PORT" 2>/dev/null; then
      return 0
    fi
    sleep 0.2
  done
  echo "[ERROR] sslocal did not listen on $SOCKS"
  return 1
}

start_vpn() {
  fetch_and_prepare_config "${1:-}"

  if ip link show "$TUN" >/dev/null 2>&1; then
    echo "[!] Interface $TUN already exists. Stopping existing session first..."
    stop_vpn
    sleep 1
  fi

  local HOST SERVER_IP GW DEV
  HOST=$(server_host)
  SERVER_IP=$(resolve_ip "$HOST")
  GW=$(wifi_gw)
  DEV=$(wifi_dev)

  if [[ -z "$SERVER_IP" || -z "$GW" || -z "$DEV" ]]; then
    echo "[ERROR] Could not detect server IP ($SERVER_IP), gateway ($GW), or physical device ($DEV)"
    exit 1
  fi

  echo "$GW $DEV $SERVER_IP" > "$STATE_DIR/path"

  echo "[+] Starting Shadowsocks Core (sslocal)..."
  pkill -u "$USER" -f "[s]slocal -c $CONFIG" 2>/dev/null || true
  sslocal -c "$CONFIG" >/tmp/sslocal.log 2>&1 &
  echo $! > "$STATE_DIR/sslocal.pid"
  wait_port

  echo "[+] Creating TUN device $TUN (10.0.0.2/24)..."
  sudo ip tuntap add mode tun dev "$TUN"
  sudo ip addr add 10.0.0.2/24 dev "$TUN"
  sudo ip link set "$TUN" up

  echo "[+] Starting tun2socks..."
  sudo tun2socks --device "$TUN" --proxy "socks5://$SOCKS" --loglevel info >/tmp/tun2socks.log 2>&1 &
  echo $! > "$STATE_DIR/tun2socks.pid"
  sleep 1

  echo "[+] Applying routing (Server $SERVER_IP pinned to $DEV via $GW)..."
  sudo ip route replace "$SERVER_IP/32" via "$GW" dev "$DEV"
  sudo ip route replace default dev "$TUN"

  echo "[+] Configuring DNS ($DNS, $DNS_BACKUP)..."
  if command -v resolvectl >/dev/null 2>&1; then
    sudo resolvectl dns "$TUN" "$DNS" "$DNS_BACKUP" 2>/dev/null || true
    sudo resolvectl domain "$TUN" "~." 2>/dev/null || true
    sudo resolvectl default-route "$TUN" yes 2>/dev/null || true
  fi

  echo "[+] Dropping default IPv6 route (killswitch)..."
  sudo ip -6 route del default 2>/dev/null || true

  echo ""
  echo "════════════════════════════════════════════════════════════"
  echo " [✓] VPN Connected! System traffic routed through $TUN"
  echo "     Server: $HOST ($SERVER_IP) via physical $DEV ($GW)"
  echo "════════════════════════════════════════════════════════════"
}

stop_vpn() {
  echo "[+] Tearing down VPN..."

  if [[ -f "$STATE_DIR/path" ]]; then
    read -r GW DEV SERVER_IP < "$STATE_DIR/path" || true
    if [[ -n "${GW:-}" && -n "${DEV:-}" ]]; then
      sudo ip route replace default via "$GW" dev "$DEV" 2>/dev/null || true
    fi
    if [[ -n "${SERVER_IP:-}" ]]; then
      sudo ip route del "$SERVER_IP/32" 2>/dev/null || true
    fi
  fi

  sudo ip route del default dev "$TUN" 2>/dev/null || true
  sudo ip link delete "$TUN" 2>/dev/null || true

  if [[ -f "$STATE_DIR/tun2socks.pid" ]]; then
    sudo kill "$(cat "$STATE_DIR/tun2socks.pid")" 2>/dev/null || true
  fi
  sudo pkill -f "tun2socks --device $TUN" 2>/dev/null || true
  sudo pkill -f "tun2socks" 2>/dev/null || true

  if [[ -f "$STATE_DIR/sslocal.pid" ]]; then
    kill "$(cat "$STATE_DIR/sslocal.pid")" 2>/dev/null || true
  fi
  pkill -u "$USER" -f "[s]slocal -c $CONFIG" 2>/dev/null || true

  if command -v resolvectl >/dev/null 2>&1; then
    sudo resolvectl revert "$TUN" 2>/dev/null || true
  fi

  rm -rf "$STATE_DIR"
  echo "[✓] VPN Disconnected. Physical routes restored."
}

status_vpn() {
  echo "=== Interface Status ==="
  ip -br link show "$TUN" 2>/dev/null || echo "$TUN: Down"
  echo ""
  echo "=== Routing Table ==="
  ip -4 route show default || true
  echo ""
  echo "=== Running Processes ==="
  ps aux | grep -E "sslocal|tun2socks" | grep -v grep || echo "None"
}

case "${1:-}" in
  start)
    shift || true
    start_vpn "${1:-}"
    ;;
  stop)
    stop_vpn
    ;;
  restart)
    shift || true
    stop_vpn
    sleep 1
    start_vpn "${1:-}"
    ;;
  status)
    status_vpn
    ;;
  *)
    echo "Usage: $0 {start [key_url]|stop|restart [key_url]|status}"
    echo "Example: $0 start 'ssconf://example.com/config.json#AuraLink'"
    exit 1
    ;;
esac
