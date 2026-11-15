#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "Virtual environment missing. Run scripts/run.sh once first." >&2
  exit 1
fi
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/evomind.service" <<EOF
[Unit]
Description=EVOMIND local AI assistant
After=network.target

[Service]
Type=simple
WorkingDirectory=$ROOT
Environment=PYTHONUNBUFFERED=1
Environment=EVOMIND_HOST=127.0.0.1
Environment=EVOMIND_PORT=8000
ExecStart=$PYTHON -m evomind
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=default.target
EOF
if ! command -v systemctl >/dev/null 2>&1 || ! systemctl --user show-environment >/dev/null 2>&1; then
  echo "systemd user session is unavailable. Service file created; use scripts/run.sh manually or enable user systemd on this Linux installation."
  exit 0
fi
systemctl --user daemon-reload
systemctl --user enable --now evomind.service
echo "EVOMIND enabled for this user session."
if command -v loginctl >/dev/null 2>&1 && loginctl enable-linger "$USER" 2>/dev/null; then
  echo "User lingering enabled: service can start at boot without an interactive login."
else
  echo "For start-at-boot before login, an administrator may need: sudo loginctl enable-linger $USER"
fi
echo "Status: systemctl --user status evomind.service"
echo "Logs:   journalctl --user -u evomind.service -f"
