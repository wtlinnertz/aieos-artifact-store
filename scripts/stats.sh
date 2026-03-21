#!/usr/bin/env bash
# Show artifact store statistics.
# Usage: bash scripts/stats.sh

set -euo pipefail

STORE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$STORE_ROOT"
python -c "
import lancedb
from pathlib import Path
from src.config import STORE_PATH

db = lancedb.connect(str(STORE_PATH.parent))
if 'artifacts' not in db.list_tables().tables:
    print('Artifact store is empty. Run ingest first.')
    exit(0)

table = db.open_table('artifacts')
df = table.to_pandas()

print(f'Artifact Store Statistics')
print(f'========================')
print(f'Total chunks: {len(df)}')
print(f'Unique artifacts: {df[\"artifact_id\"].nunique()}')
print(f'Initiatives: {df[\"initiative\"].nunique()}')
print()
print(f'By initiative:')
for init, count in df.groupby('initiative')['artifact_id'].nunique().items():
    print(f'  {init}: {count} artifacts')
print()
print(f'By artifact type:')
for atype, count in df.groupby('artifact_type')['artifact_id'].nunique().items():
    print(f'  {atype}: {count}')
print()
print(f'By kit:')
for kit, count in df.groupby('kit')['artifact_id'].nunique().items():
    print(f'  {kit}: {count} artifacts')
"
