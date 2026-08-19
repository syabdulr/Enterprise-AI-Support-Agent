# Enterprise AI Support Agent - Demo Guide

## 🚀 Run the real test suite

This is the demo — it exercises actual code in `src/` (RAG, workflow
orchestration, self-reflection, Dataverse, Graph connector) instead
of printing a description of it.

```bash
cd /data/Claude/enterprise_ai_support_agent
pip install -r requirements.txt
pytest
```

Expect `125 passed, 12 skipped`. Every skip has an inline reason in
its test file — see the "Running Tests" section of README.md for
what each one means (a few stale assertions not covered by CI, one
needs live Azure OpenAI credentials, three are blocked on Python 3.14
by upstream `semantic-kernel`/`pyautogen` incompatibilities and pass
on Python ≤3.13).

## 📋 What It Actually Shows

- **RAG pipeline** — document loading, chunking, ChromaDB storage/retrieval
- **Multi-agent workflow orchestration** — triage → diagnose → resolve → escalate
- **Self-reflection** — the pipeline re-checking its own outputs
- **Dataverse integration** — governed, audited incident writes via the Functions/APIM gateway
- **Microsoft Graph connector** — permission-aware SharePoint retrieval into RAG
- **Error handling & API contract tests**

## 🐛 Troubleshooting

### `ModuleNotFoundError: No module named 'src'`
Either run `pytest` from the repo root (it now reads `pythonpath = ["."]`
from `pyproject.toml`), or set `PYTHONPATH=.` explicitly if you're on an
older pytest/config.

### A `semantic_kernel`/`autogen` test errors instead of skipping
You're likely on Python 3.14. Both packages have known incompatibilities
there (see README.md's "Running Tests" section). Run under Python 3.11–3.13
for full coverage, or trust the skip messages — they explain exactly what's
blocked and why.

## 🔗 Resources

- GitHub Repository: https://github.com/syabdulr/Enterprise-AI-Support-Agent
- LinkedIn Post: `docs/linkedin_post_ai_milestone.md`
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Full Documentation: [README.md](README.md)
