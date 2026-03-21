#!/usr/bin/env bash
# Drop and rebuild the entire artifact store.
# Use after changing embedding model or chunking strategy.
# Usage: bash scripts/reindex.sh [aieos-root-path]

set -euo pipefail

STORE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AIEOS_ROOT="${1:-$(cd "$STORE_ROOT/.." && pwd)}"

echo "WARNING: This will delete and rebuild the entire artifact store."
echo "Store location: $STORE_ROOT/store/"
read -p "Continue? [y/N] " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$STORE_ROOT/store/"
    echo "Store cleared. Re-indexing..."
    cd "$STORE_ROOT"
    python -m src.ingest --all --root "$AIEOS_ROOT"
    echo "Reindex complete."
else
    echo "Aborted."
fi
