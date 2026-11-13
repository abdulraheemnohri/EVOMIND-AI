$ErrorActionPreference="Stop"
if (!(Test-Path ".venv")) { py -3.11 -m venv .venv }
. .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
python -m evomind
