"""AIEOS Artifact Store — Ingestion pipeline.

Reads AIEOS artifacts, chunks by section, embeds, and stores in LanceDB.

Usage:
    python -m src.ingest --artifact path/to/artifact.md
    python -m src.ingest --initiative path/to/aieos-project/
    python -m src.ingest --all
"""

import argparse
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import lancedb
import pyarrow as pa

from src.config import STORE_PATH, AIEOS_ROOT, SKIP_DRAFT, SKIP_FRAMEWORK, INGEST_ER, INGEST_JOURNAL, INGEST_RETROSPECTIVE, EMBEDDING_DIMENSIONS
from src.chunker import chunk_artifact
from src.metadata import extract_metadata, is_frozen, is_framework_file
from src.embeddings import embed_texts


# LanceDB schema
SCHEMA = pa.schema([
    pa.field("id", pa.string()),                # Unique: artifact_id + chunk_index
    pa.field("content_hash", pa.string()),       # Hash of chunk text (for dedup)
    pa.field("text", pa.string()),               # Chunk text
    pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIMENSIONS)),
    pa.field("artifact_id", pa.string()),
    pa.field("artifact_type", pa.string()),
    pa.field("initiative", pa.string()),
    pa.field("kit", pa.string()),
    pa.field("layer", pa.int32()),
    pa.field("status", pa.string()),
    pa.field("frozen_date", pa.string()),
    pa.field("spec_version", pa.string()),
    pa.field("completeness_score", pa.int32()),
    pa.field("section_heading", pa.string()),
    pa.field("section_path", pa.string()),
    pa.field("file_path", pa.string()),
    pa.field("ingested_at", pa.string()),
    pa.field("chunk_index", pa.int32()),
    pa.field("char_count", pa.int32()),
])


def get_db():
    """Open or create the LanceDB database."""
    from src.config import STORE_PATH as _sp  # Re-read at call time for test overrides
    _sp.parent.mkdir(parents=True, exist_ok=True)
    return lancedb.connect(str(_sp.parent))


def get_or_create_table(db):
    """Get the artifacts table, creating it if needed."""
    table_name = "artifacts"
    if table_name in db.list_tables().tables:
        return db.open_table(table_name)
    return db.create_table(table_name, schema=SCHEMA)


def content_hash(text: str) -> str:
    """Generate a hash of chunk content for dedup."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def ingest_artifact(file_path: str, table=None, db=None) -> dict:
    """Ingest a single artifact file into the store.

    Args:
        file_path: Path to the Markdown artifact file.
        table: LanceDB table (opens default if None).
        db: LanceDB connection (opens default if None).

    Returns:
        Dict with ingestion results: {chunks, skipped, artifact_id, reason}.
    """
    path = Path(file_path)
    if not path.exists():
        return {"chunks": 0, "skipped": True, "artifact_id": "", "reason": "file not found"}

    if not path.suffix == '.md':
        return {"chunks": 0, "skipped": True, "artifact_id": "", "reason": "not a markdown file"}

    content = path.read_text(encoding='utf-8')

    # Extract metadata
    meta = extract_metadata(content, str(path))

    # Skip framework files
    if SKIP_FRAMEWORK and is_framework_file(str(path)):
        return {"chunks": 0, "skipped": True, "artifact_id": meta.artifact_id, "reason": "framework file"}

    # Skip draft artifacts
    if SKIP_DRAFT and not is_frozen(content, meta):
        return {"chunks": 0, "skipped": True, "artifact_id": meta.artifact_id, "reason": "not frozen"}

    # Chunk the artifact
    chunks = chunk_artifact(content, str(path))
    if not chunks:
        return {"chunks": 0, "skipped": True, "artifact_id": meta.artifact_id, "reason": "no chunks produced"}

    # Open store if needed
    if db is None:
        db = get_db()
    if table is None:
        table = get_or_create_table(db)

    # Embed all chunks
    texts = [c.text for c in chunks]
    vectors = embed_texts(texts)

    now = datetime.now(timezone.utc).isoformat()

    # Build records
    records = []
    for chunk, vector in zip(chunks, vectors):
        chunk_id = f"{meta.artifact_id}:{chunk.chunk_index}" if meta.artifact_id else f"{path.stem}:{chunk.chunk_index}"
        records.append({
            "id": chunk_id,
            "content_hash": content_hash(chunk.text),
            "text": chunk.text,
            "vector": vector,
            "artifact_id": meta.artifact_id,
            "artifact_type": meta.artifact_type,
            "initiative": meta.initiative,
            "kit": meta.kit,
            "layer": meta.layer,
            "status": meta.status,
            "frozen_date": meta.frozen_date,
            "spec_version": meta.spec_version,
            "completeness_score": meta.completeness_score,
            "section_heading": chunk.heading,
            "section_path": chunk.heading_path,
            "file_path": str(path),
            "ingested_at": now,
            "chunk_index": chunk.chunk_index,
            "char_count": chunk.char_count,
        })

    # Upsert (add — LanceDB handles overwrites via merge on id if needed)
    table.add(records)

    return {"chunks": len(records), "skipped": False, "artifact_id": meta.artifact_id, "reason": ""}


def ingest_initiative(initiative_path: str) -> dict:
    """Ingest all frozen artifacts from one initiative.

    Scans docs/sdlc/, docs/engagement/ for Markdown files.

    Returns:
        Summary dict: {total_files, ingested, skipped, total_chunks}.
    """
    base = Path(initiative_path)
    summary = {"total_files": 0, "ingested": 0, "skipped": 0, "total_chunks": 0, "details": []}

    db = get_db()
    table = get_or_create_table(db)

    # Collect artifact files
    artifact_files = []

    sdlc_dir = base / "docs" / "sdlc"
    if sdlc_dir.exists():
        artifact_files.extend(sorted(sdlc_dir.glob("*.md")))

    engagement_dir = base / "docs" / "engagement"
    if engagement_dir.exists():
        if INGEST_ER:
            artifact_files.extend(sorted(engagement_dir.glob("er-*.md")))
        if INGEST_JOURNAL:
            artifact_files.extend(sorted(engagement_dir.glob("sherpa-journal-*.md")))
        if INGEST_RETROSPECTIVE:
            artifact_files.extend(sorted(engagement_dir.glob("retrospective-*.md")))

    for f in artifact_files:
        summary["total_files"] += 1
        result = ingest_artifact(str(f), table=table, db=db)
        if result["skipped"]:
            summary["skipped"] += 1
        else:
            summary["ingested"] += 1
            summary["total_chunks"] += result["chunks"]
        summary["details"].append(result)

    return summary


def ingest_all(root_path: str = None) -> dict:
    """Ingest all frozen artifacts across all initiatives.

    Scans root directory for aieos-* project directories.

    Returns:
        Summary dict: {initiatives, total_files, ingested, skipped, total_chunks}.
    """
    root = Path(root_path) if root_path else AIEOS_ROOT
    summary = {"initiatives": 0, "total_files": 0, "ingested": 0, "skipped": 0, "total_chunks": 0}

    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        # Skip framework, sherpa, artifact-store
        if d.name in ('aieos-governance-foundation', 'aieos-sherpa', 'aieos-artifact-store'):
            continue
        if not d.name.startswith('aieos-'):
            continue
        # Skip kit repos (they have docs/specs, not docs/sdlc)
        if (d / "docs" / "specs").exists() and not (d / "docs" / "sdlc").exists():
            continue
        # This looks like an initiative project
        if (d / "docs" / "sdlc").exists() or (d / "docs" / "engagement").exists():
            summary["initiatives"] += 1
            result = ingest_initiative(str(d))
            summary["total_files"] += result["total_files"]
            summary["ingested"] += result["ingested"]
            summary["skipped"] += result["skipped"]
            summary["total_chunks"] += result["total_chunks"]
            print(f"  {d.name}: {result['ingested']} artifacts, {result['total_chunks']} chunks ({result['skipped']} skipped)")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Ingest AIEOS artifacts into the vector store.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--artifact", help="Path to a single artifact file")
    group.add_argument("--initiative", help="Path to an initiative project directory")
    group.add_argument("--all", action="store_true", help="Ingest all initiatives under AIEOS_ROOT")
    parser.add_argument("--root", help="Override AIEOS_ROOT path")

    args = parser.parse_args()

    if args.artifact:
        result = ingest_artifact(args.artifact)
        if result["skipped"]:
            print(f"Skipped: {result['reason']}")
        else:
            print(f"Ingested: {result['artifact_id']} — {result['chunks']} chunks")

    elif args.initiative:
        result = ingest_initiative(args.initiative)
        print(f"\nInitiative ingestion complete:")
        print(f"  Files scanned: {result['total_files']}")
        print(f"  Ingested: {result['ingested']} artifacts, {result['total_chunks']} chunks")
        print(f"  Skipped: {result['skipped']}")

    elif args.all:
        root = args.root if args.root else None
        print(f"Scanning {root or AIEOS_ROOT} for initiatives...")
        result = ingest_all(root)
        print(f"\nFull ingestion complete:")
        print(f"  Initiatives: {result['initiatives']}")
        print(f"  Files scanned: {result['total_files']}")
        print(f"  Ingested: {result['ingested']} artifacts, {result['total_chunks']} chunks")
        print(f"  Skipped: {result['skipped']}")


if __name__ == "__main__":
    main()
