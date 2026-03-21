"""AIEOS Artifact Store — Query interface.

Semantic, filtered, and hybrid search across ingested AIEOS artifacts.

Usage:
    python -m src.query "authentication architecture decisions"
    python -m src.query "failure modes" --type SAD --layer 4
    python -m src.query "user behavior assumptions" --type AR --hybrid
    python -m src.query "sunset" --type CLA --format json
"""

import argparse
import json
import sys
from pathlib import Path

import lancedb

from src.config import STORE_PATH, DEFAULT_LIMIT
from src.embeddings import embed_query


def get_table():
    """Open the artifacts table."""
    from src.config import STORE_PATH as _sp  # Re-read at call time for test overrides
    db = lancedb.connect(str(_sp.parent))
    table_names = db.list_tables().tables
    if "artifacts" not in table_names:
        print("Error: Artifact store is empty. Run ingest first.", file=sys.stderr)
        sys.exit(1)
    return db.open_table("artifacts")


def search(
    query: str,
    artifact_type: str = None,
    initiative: str = None,
    kit: str = None,
    layer: int = None,
    limit: int = None,
    hybrid: bool = False,
) -> list[dict]:
    """Search the artifact store.

    Args:
        query: Natural language search query.
        artifact_type: Filter by artifact type (e.g., "SAD", "AR").
        initiative: Filter by initiative name (e.g., "TASKFLOW").
        kit: Filter by kit (e.g., "EEK", "PIK").
        layer: Filter by layer number (1-15).
        limit: Maximum results to return.
        hybrid: Use hybrid vector + full-text search.

    Returns:
        List of result dicts with text, metadata, and score.
    """
    table = get_table()
    limit = limit or DEFAULT_LIMIT

    # Build the query
    query_vector = embed_query(query)

    # Start with vector search
    search_builder = table.search(query_vector).limit(limit)

    # Apply metadata filters
    filters = []
    if artifact_type:
        filters.append(f"artifact_type = '{artifact_type.upper()}'")
    if initiative:
        filters.append(f"initiative = '{initiative.upper()}'")
    if kit:
        filters.append(f"kit = '{kit.upper()}'")
    if layer is not None:
        filters.append(f"layer = {layer}")

    if filters:
        where_clause = " AND ".join(filters)
        search_builder = search_builder.where(where_clause)

    results = search_builder.to_pandas()

    # Convert to list of dicts
    output = []
    for _, row in results.iterrows():
        output.append({
            "text": row.get("text", ""),
            "artifact_id": row.get("artifact_id", ""),
            "artifact_type": row.get("artifact_type", ""),
            "initiative": row.get("initiative", ""),
            "kit": row.get("kit", ""),
            "layer": int(row.get("layer", 0)),
            "section_heading": row.get("section_heading", ""),
            "section_path": row.get("section_path", ""),
            "file_path": row.get("file_path", ""),
            "status": row.get("status", ""),
            "frozen_date": row.get("frozen_date", ""),
            "score": float(row.get("_distance", 0)),
        })

    return output


def format_text(results: list[dict], query: str) -> str:
    """Format results as human-readable text."""
    if not results:
        return f'Query: "{query}"\nNo results found.'

    initiatives = set(r["initiative"] for r in results if r["initiative"])
    lines = [
        f'Query: "{query}"',
        f"Results: {len(results)} matches across {len(initiatives)} initiative(s)",
        "",
    ]

    for i, r in enumerate(results, 1):
        score_pct = max(0, (1 - r["score"]) * 100)  # Convert distance to similarity %
        lines.append(f'[{i}] {r["artifact_id"]} {r["section_heading"]} (score: {score_pct:.0f}%)')
        lines.append(f'    Initiative: {r["initiative"]} | Kit: {r["kit"]} | Frozen: {r["frozen_date"]}')
        # Truncate text preview
        preview = r["text"][:200].replace("\n", " ")
        if len(r["text"]) > 200:
            preview += "..."
        lines.append(f'    "{preview}"')
        lines.append("")

    return "\n".join(lines)


def format_json(results: list[dict]) -> str:
    """Format results as JSON."""
    return json.dumps(results, indent=2)


def format_context(results: list[dict], query: str) -> str:
    """Format results as a context block for pasting into an AI session."""
    if not results:
        return f"No prior organizational knowledge found for: {query}"

    lines = [
        f"## Prior Organizational Knowledge: {query}",
        f"",
        f"The artifact store found {len(results)} relevant chunks from prior initiatives:",
        "",
    ]

    for i, r in enumerate(results, 1):
        lines.append(f"### [{i}] {r['artifact_id']} — {r['section_heading']}")
        lines.append(f"*Initiative: {r['initiative']} | Kit: {r['kit']} | Layer: {r['layer']}*")
        lines.append("")
        lines.append(r["text"])
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Query the AIEOS artifact store.")
    parser.add_argument("query", help="Natural language search query")
    parser.add_argument("--type", dest="artifact_type", help="Filter by artifact type (e.g., SAD, AR)")
    parser.add_argument("--initiative", help="Filter by initiative name")
    parser.add_argument("--kit", help="Filter by kit (e.g., EEK, PIK)")
    parser.add_argument("--layer", type=int, help="Filter by layer number (1-15)")
    parser.add_argument("--limit", type=int, help=f"Maximum results (default: {DEFAULT_LIMIT})")
    parser.add_argument("--hybrid", action="store_true", help="Use hybrid vector + keyword search")
    parser.add_argument("--format", choices=["text", "json", "context"], default="text", help="Output format")

    args = parser.parse_args()

    results = search(
        query=args.query,
        artifact_type=args.artifact_type,
        initiative=args.initiative,
        kit=args.kit,
        layer=args.layer,
        limit=args.limit,
        hybrid=args.hybrid,
    )

    if args.format == "json":
        print(format_json(results))
    elif args.format == "context":
        print(format_context(results, args.query))
    else:
        print(format_text(results, args.query))


if __name__ == "__main__":
    main()
