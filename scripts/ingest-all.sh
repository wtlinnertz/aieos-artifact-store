#!/usr/bin/env bash
# Ingest all frozen artifacts across all initiatives.
# Usage: bash scripts/ingest-all.sh [aieos-root-path]

set -euo pipefail

STORE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AIEOS_ROOT="${1:-$(cd "$STORE_ROOT/.." && pwd)}"

cd "$STORE_ROOT"
python -m src.ingest --all --root "$AIEOS_ROOT"
