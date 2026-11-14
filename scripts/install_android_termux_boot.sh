#!/data/data/com.termux/files/usr/bin/bash
# Run this installer inside Termux, not inside the Debian proot shell.
set -euo pipefail
ROOT="${EVOMIND_TERMUX_ROOT:-$HOME/evomind}"
mkdir -p "$HOME/.termux/boot"
cat > "$HOME/.termux/boot/start-evomind" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
proot-distro login debian -- bash -lc 'cd "$HOME/EVOMIND-AI" && . .venv/bin/activate && export EVOMIND_HOST=127.0.0.1 EVOMIND_PORT=8000 && nohup python -m evomind >> "$HOME/evomind.log" 2>&1 </dev/null &'
EOF
chmod +x "$HOME/.termux/boot/start-evomind"
echo "Termux:Boot launcher installed."
echo "Requirements: install Termux:Boot, install proot-distro, and clone EVOMIND-AI to Debian ~/EVOMIND-AI."
echo "Android may stop background processes under battery optimization; this is best-effort, not a systemd service."
