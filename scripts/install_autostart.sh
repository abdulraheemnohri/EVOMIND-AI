#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "Virtual environment missing. Run scripts/run.sh once first." >&2
  exit 1
fi
if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemd is not installed. This installer supports systemd-based Linux only." >&2
  exit 1
fi
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/evomind.service" <<EOF
[Unit]
Description=EVOMIND local AI assistant
After=default.target

[Service]
Type=simple
WorkingDirectory="$ROOT"
Environment=PYTHONUNBUFFERED=1
Environment=EVOMIND_HOST=127.0.0.1
Environment=EVOMIND_PORT=8000
ExecStart="$PYTHON" -m evomind
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=read-only
ReadWritePaths="$ROOT/data" "$ROOT/models" "$ROOT"

[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now evomind.service
echo "EVOMIND enabled for this user session."
if command -v loginctl >/dev/null 2>&1; then
  if loginctl enable-linger "$USER" 2>/dev/null; then
    echo "User lingering enabled: service can start at boot without interactive login."
  else
    echo "For boot before login, an administrator may need: sudo loginctl enable-linger $USER"
  fi
fi
echo "Status: systemctl --user status evomind.service"
echo "Logs:   journalctl --user -u evomind.service -f"
echo "Uninstall: bash scripts/uninstall_autostart.sh"
