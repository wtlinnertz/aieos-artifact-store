#!/usr/bin/env bash
# Ingest all frozen artifacts from one initiative into the artifact store.
# Usage: bash scripts/ingest-initiative.sh path/to/aieos-project/

set -euo pipefail

STORE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INITIATIVE_PATH="${1:?Usage: bash scripts/ingest-initiative.sh path/to/aieos-project/}"

cd "$STORE_ROOT"
python -m src.ingest --initiative "$INITIATIVE_PATH"
