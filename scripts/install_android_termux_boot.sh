#!/data/data/com.termux/files/usr/bin/bash
# Run from the Termux host shell. Requires Termux:Boot and proot-distro.
set -euo pipefail
if ! command -v proot-distro >/dev/null 2>&1; then
  echo "Install proot-distro in Termux first: pkg install proot-distro" >&2
  exit 1
fi
DEBIAN_DIR="${EVOMIND_DEBIAN_DIR:-$HOME/EVOMIND-AI}"
mkdir -p "$HOME/.termux/boot"
cat > "$HOME/.termux/boot/start-evomind" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock >/dev/null 2>&1 || true
proot-distro login debian -- bash -lc 'cd "$DEBIAN_DIR" && test -x .venv/bin/python && export EVOMIND_HOST=127.0.0.1 EVOMIND_PORT=8000 && nohup .venv/bin/python -m evomind >> "\$HOME/evomind.log" 2>&1 </dev/null &'
EOF
chmod +x "$HOME/.termux/boot/start-evomind"
echo "Termux:Boot launcher installed at ~/.termux/boot/start-evomind"
echo "Ensure the Debian repo exists at: $DEBIAN_DIR and has a working .venv."
echo "Android battery management may still stop background processes."
