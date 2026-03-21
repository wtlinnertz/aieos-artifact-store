# AIEOS Artifact Store

Cross-initiative vector search over frozen AIEOS governance artifacts. Powered by LanceDB.

## Quick Start

### Install

```bash
cd aieos-artifact-store
pip install -r requirements.txt
```

### Ingest

```bash
# Single initiative
bash scripts/ingest-initiative.sh ../aieos-console

# All initiatives
bash scripts/ingest-all.sh
```

### Query

```bash
# Semantic search
python -m src.query "authentication architecture"

# Filtered by initiative
python -m src.query "deployment strategy" --initiative CONSOLE

# Output as context block (for AI prompts)
python -m src.query "error handling patterns" --format context
```

## How It Works

1. **Chunking** — Markdown files are split on `##` headings. The `§1 Document Control` section is extracted for metadata but excluded from chunks. HTML comments are stripped. Chunks below a minimum size threshold are discarded.

2. **Metadata extraction** — Each chunk is tagged with artifact ID, type, initiative, kit, layer, and frozen status. Metadata is derived from the Document Control table and file path.

3. **Embedding** — Each chunk is embedded using a local sentence-transformer model (default: `all-MiniLM-L6-v2`). No external API calls required.

4. **Storage** — Embeddings and metadata are stored in a LanceDB table on the local filesystem (`store/` directory). LanceDB provides efficient vector search with metadata filtering.

5. **Query** — Queries are embedded with the same model and searched against the store using approximate nearest neighbor search. Results can be filtered by initiative, kit, layer, or artifact type.

## Usage

### Ingest Modes

| Mode | Command | Description |
|------|---------|-------------|
| Single file | `python -m src.ingest path/to/artifact.md` | Ingest one artifact |
| Initiative | `bash scripts/ingest-initiative.sh path/to/project/` | All frozen artifacts in one initiative |
| All | `bash scripts/ingest-all.sh [aieos-root]` | All frozen artifacts across all initiatives |
| Reindex | `bash scripts/reindex.sh [aieos-root]` | Drop store and rebuild from scratch |

Only frozen artifacts are ingested. Draft and in-progress artifacts are skipped.

### Query Modes

| Mode | Flag | Description |
|------|------|-------------|
| Semantic | (default) | Vector similarity search |
| Filtered | `--initiative`, `--kit`, `--layer`, `--type` | Combine with semantic search |
| Hybrid | `--keyword` | Keyword pre-filter + vector ranking |

### Output Formats

| Format | Flag | Description |
|--------|------|-------------|
| Text | `--format text` | Human-readable (default) |
| JSON | `--format json` | Machine-readable with all metadata |
| Context | `--format context` | Fenced block suitable for pasting into AI prompts |

### Statistics

```bash
bash scripts/stats.sh
```

Shows total chunks, unique artifacts, and breakdowns by initiative, artifact type, and kit.

## Sherpa Integration

The artifact store serves three integration points for the AIEOS sherpa:

### 1. Discovery Context

When generating a new artifact, the sherpa queries the store for related frozen artifacts from other initiatives. This provides architectural precedent and pattern examples without requiring the user to manually locate them.

### 2. Assumption Dedup

Before a new assumption is introduced in a PRD or SAD, the store is queried to check whether the same assumption was already validated (or invalidated) in a prior initiative.

### 3. Architecture Precedent

During SAD and TDD generation, the store surfaces prior architecture decisions from similar initiatives, helping maintain consistency across the portfolio.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `AIEOS_STORE_PATH` | `./store/artifacts.lance` | Path to the LanceDB store |
| `AIEOS_EMBED_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformer model name |
| `AIEOS_CHUNK_MIN_CHARS` | `50` | Minimum chunk size (characters) |
| `AIEOS_SEARCH_LIMIT` | `10` | Default number of search results |

## Testing

```bash
# Unit tests (no embedding model required)
pytest tests/ -v --ignore=tests/test_ingest.py

# All tests including integration (downloads embedding model on first run)
pytest tests/ -v --run-slow
```

## Project Structure

```
aieos-artifact-store/
  docs/
    embedding-models.md      # Model comparison and selection rationale
    integration-guide.md     # How sherpa and prompts query the store
  scripts/
    ingest-initiative.sh     # Ingest one initiative
    ingest-all.sh            # Ingest all initiatives
    reindex.sh               # Drop and rebuild store
    stats.sh                 # Show store statistics
  src/
    __init__.py
    chunker.py               # Markdown-aware chunking
    config.py                # Configuration and defaults
    ingest.py                # Ingestion pipeline
    metadata.py              # Metadata extraction from artifacts
    query.py                 # Search interface
  store/                     # LanceDB data (gitignored)
  tests/
    __init__.py
    conftest.py              # Shared fixtures
    test_chunker.py          # Chunking tests
    test_metadata.py         # Metadata extraction tests
    test_ingest.py           # Integration tests (slow)
  CLAUDE.md
  LICENSE
  README.md
  VERSION
  requirements.txt
```
