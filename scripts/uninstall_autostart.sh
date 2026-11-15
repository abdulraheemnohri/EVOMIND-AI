#!/usr/bin/env bash
set -euo pipefail
SERVICE="$HOME/.config/systemd/user/evomind.service"
if command -v systemctl >/dev/null 2>&1 && systemctl --user show-environment >/dev/null 2>&1; then
  systemctl --user disable --now evomind.service || true
  systemctl --user daemon-reload
fi
rm -f "$SERVICE"
rmdir "$HOME/.config/systemd/user" 2>/dev/null || true
echo "EVOMIND user service removed. Project files and local data were not deleted."
