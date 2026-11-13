# EVOMIND-AI

Local-first self-growing assistant: SQLite chat history, approved memory, reflection candidates, safe allow-listed skills, goals, feedback, and optional GGUF / LiteRT-LM runtimes.

## Windows
    py -3.11 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -e ".[dev,gguf,hf]"
    python -m evomind
Open http://127.0.0.1:8000.

## Linux / Android Debian
    python3 -m venv .venv
    . .venv/bin/activate
    pip install -e ".[dev]"
    python -m evomind

Place compatible .gguf or .litertlm models in models/. Install the gguf extra for llama.cpp or litert extra where LiteRT-LM is supported. Runtime/model API compatibility varies by platform; errors are surfaced. Verify model licences, gated access, storage and RAM before downloading.

Reflection creates pending candidates; approve/reject in Memory Lab. Skills are declarative and map only to built-in actions. Arbitrary Python execution is disabled. This is cumulative memory/skill growth, not autonomous weight training or unrestricted self-modifying code. Server binds to localhost by default; add auth/TLS before network exposure.

Run tests with pytest -q. Environment: EVOMIND_HOST, EVOMIND_PORT, EVOMIND_DATA_DIR, EVOMIND_MODELS_DIR, EVOMIND_DB.

Donations: add your own GitHub Sponsors or donation URL when ready; no payment endpoint is fabricated. Apache-2.0.