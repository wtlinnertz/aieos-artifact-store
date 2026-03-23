# CLAUDE.md — AIEOS Artifact Store

## What This Project Is

The AIEOS Artifact Store provides cross-initiative vector search over frozen AIEOS governance artifacts. It ingests Markdown artifacts produced by the AIEOS framework, chunks them by section heading, embeds them using a local sentence-transformer model, and stores them in LanceDB for semantic retrieval.

The store is a supporting tool for the AIEOS sherpa and generation prompts. It is not a governance kit — it has no specs, templates, prompts, or validators. It is infrastructure.

## How to Develop

```bash
# Create and activate virtual environment (one-time setup)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run unit tests (no embedding model needed)
pytest tests/ -v --ignore=tests/test_ingest.py

# Run all tests including integration (downloads model on first run)
pytest tests/ -v --run-slow

# Ingest test data from a real initiative
bash scripts/ingest-initiative.sh ../aieos-console

# Check store statistics
bash scripts/stats.sh
```

Always activate the venv before running commands: `source .venv/bin/activate`

## Key Files

| File | Purpose |
|------|---------|
| `src/ingest.py` | Ingestion pipeline: reads files, chunks, embeds, stores |
| `src/query.py` | Search interface: embed query, search LanceDB, format results |
| `src/chunker.py` | Markdown-aware chunking: splits on H2, strips doc control and comments |
| `src/metadata.py` | Metadata extraction: artifact ID, type, kit, layer, initiative, status |
| `src/config.py` | Configuration defaults and environment variable overrides |

## Testing

- **Unit tests:** `pytest tests/ -v --ignore=tests/test_ingest.py` — tests chunker and metadata extraction without needing the embedding model.
- **Integration tests:** `pytest tests/ -v --run-slow` — requires the embedding model to be downloaded. Tests full ingest-and-query cycle.

## Important Notes

- The `store/` directory is gitignored. It contains the LanceDB data files. Regenerate it with `bash scripts/ingest-all.sh`.
- Only frozen artifacts are ingested. Draft artifacts are skipped.
- The default embedding model is `all-MiniLM-L6-v2` (384 dimensions, runs locally, no API key needed). See `docs/embedding-models.md` for alternatives.
- Shell scripts in `scripts/` need execute permission: `chmod +x scripts/*.sh`
