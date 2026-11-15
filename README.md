# EVOMIND-AI

Local-first personal AI workspace with persistent SQLite memory, feedback, approved reflection, safe declarative skills, specialist agents, an allow-listed tool registry, goals, tasks, and optional GGUF / LiteRT-LM runtimes.

## Features
- Local chat, chat history, approved memories and reviewable reflection candidates.
- Specialist agent modes: general assistant, planner, research analyst, writer, coder, data analyst, organizer, tutor, translator, reviewer, architect, product manager, debugger and creative partner.
- Safe local tools: arithmetic calculator, approved-memory search, goal reader, local clock and task creation.
- Task board with pending / in-progress / done / cancelled states.
- Local model inventory and optional Hugging Face model discovery/download.
- Responsive dashboard, runtime diagnostics, and SQLite persistence.
- No arbitrary generated Python, shell, filesystem, browser or network execution. Research mode analyzes supplied information; it does not pretend to browse the internet.

## Linux terminal setup
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
git clone https://github.com/abdulraheemnohri/EVOMIND-AI.git
cd EVOMIND-AI
git checkout feature/evomind-foundation
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,hf]"
python -m evomind
```
Open http://127.0.0.1:8000. The default bind is localhost. Do not expose it to a LAN or public network without authentication, TLS and a reviewed access-control layer.

## Start automatically on Linux reboot
After completing setup, run:
```bash
bash scripts/install_autostart.sh
```
This installs and enables a per-user systemd service. To start before login, the administrator may need to enable lingering:
```bash
sudo loginctl enable-linger "$USER"
```
Manage it with `systemctl --user status evomind`, `systemctl --user restart evomind` and `journalctl --user -u evomind -f`. Uninstall with `systemctl --user disable --now evomind` and remove `~/.config/systemd/user/evomind.service`.

## Android Debian / Termux note
A Debian proot container on Android normally does not run systemd as PID 1. Install Termux:Boot in the host Termux app, install `proot-distro`, clone this repository into Debian at `/root/EVOMIND-AI` (or set `EVOMIND_DEBIAN_DIR=/home/droid/EVOMIND-AI` in Termux if using the `droid` account), then download and run the installer from the Termux host shell (not inside Debian):
```bash
curl -fsSL https://raw.githubusercontent.com/abdulraheemnohri/EVOMIND-AI/feature/evomind-foundation/scripts/install_android_termux_boot.sh -o "$TMPDIR/install-evomind-boot.sh"
bash "$TMPDIR/install-evomind-boot.sh"
``` Android battery management can still stop background processes; this launcher is best-effort. Keep the phone charged and exempt Termux from battery optimization where Android permits.

## Windows
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,hf]"
python -m evomind
```

## Models
Put compatible `.gguf` or `.litertlm` files in `models/`. Install `pip install -e ".[gguf]"` for llama.cpp. LiteRT-LM is platform/API dependent; install its optional extra only where a compatible distribution is available. Verify model licence, gated access, file size, RAM and storage before downloading. The application defaults to demo mode until a model is selected.

## Safety and limitations
- Reflection only proposes memory; the user approves or rejects it.
- Skills and tools are allow-listed built-ins. The agent cannot run arbitrary code or shell commands.
- Agent output is not proof that an external action occurred. Human approval is required for consequential actions.
- Self-growth means persistent memory, feedback, goals and curated skills; it does not autonomously rewrite model weights.
- No built-in web search or unrestricted computer control is claimed.
- Back up the SQLite database and model directory before upgrades.

## Development
```bash
pip install -e ".[dev]"
pytest -q
```
Configuration: `EVOMIND_HOST`, `EVOMIND_PORT`, `EVOMIND_DATA_DIR`, `EVOMIND_MODELS_DIR`, `EVOMIND_DB`.
