"""AIEOS Artifact Store — Markdown-aware chunking.

Splits AIEOS artifacts by section heading, preserving metadata and hierarchy.
"""

import re
from dataclasses import dataclass
from src.config import MAX_CHUNK_SIZE, MIN_CHUNK_SIZE


@dataclass
class Chunk:
    """A chunk of artifact content with heading context."""
    text: str
    heading: str
    heading_path: str
    level: int
    chunk_index: int
    char_count: int


def extract_document_control(content: str) -> dict:
    """Extract Document Control fields from artifact header.

    Parses the first table in the document looking for common fields:
    artifact ID, status, version, dates, etc.

    Returns dict of field_name (lowercase) → value.
    """
    doc_control = {}
    # Look for a table early in the document (within first 2000 chars)
    header = content[:2000]

    # Match table rows: | Field | Value |
    rows = re.findall(r'\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|', header)
    for field, value in rows:
        field_clean = field.strip().lower()
        value_clean = value.strip()
        if field_clean not in ('---', 'field', ''):
            doc_control[field_clean] = value_clean

    return doc_control


def chunk_artifact(content: str, artifact_path: str = "") -> list[Chunk]:
    """Split a Markdown artifact into chunks by heading.

    Primary split: ## (h2) headings — these are the main sections in AIEOS artifacts.
    Secondary split: ### (h3) headings — used when an h2 section exceeds MAX_CHUNK_SIZE.
    Tertiary split: paragraph boundaries — used when h3 sections are still too large.

    The Document Control section is NOT returned as a chunk (it's metadata, not content).
    Markdown comments (<!-- ... -->) are stripped.

    Args:
        content: Full Markdown text of the artifact.
        artifact_path: Source file path (for context in heading_path).

    Returns:
        List of Chunk objects ordered by position in the document.
    """
    # Strip HTML comments
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

    # Get artifact filename for heading path root
    root_name = artifact_path.split('/')[-1].replace('.md', '') if artifact_path else "artifact"

    # Split on h2 headings
    h2_pattern = re.compile(r'^(## .+)$', re.MULTILINE)
    h2_sections = _split_by_heading(content, h2_pattern)

    chunks = []
    chunk_index = 0

    for heading, section_text in h2_sections:
        # Skip Document Control section
        if heading and re.search(r'document\s+control|doc.*control', heading, re.IGNORECASE):
            continue

        # Skip empty sections
        if len(section_text.strip()) < MIN_CHUNK_SIZE:
            continue

        heading_display = heading.lstrip('#').strip() if heading else "Introduction"

        # If section fits, keep as one chunk
        if len(section_text) <= MAX_CHUNK_SIZE:
            chunks.append(Chunk(
                text=section_text.strip(),
                heading=heading_display,
                heading_path=f"{root_name} > {heading_display}",
                level=2,
                chunk_index=chunk_index,
                char_count=len(section_text.strip()),
            ))
            chunk_index += 1
        else:
            # Split on h3 headings
            h3_pattern = re.compile(r'^(### .+)$', re.MULTILINE)
            h3_sections = _split_by_heading(section_text, h3_pattern)

            for sub_heading, sub_text in h3_sections:
                if len(sub_text.strip()) < MIN_CHUNK_SIZE:
                    continue

                sub_display = sub_heading.lstrip('#').strip() if sub_heading else heading_display
                full_path = f"{root_name} > {heading_display} > {sub_display}" if sub_heading else f"{root_name} > {heading_display}"

                # If still too large, split on paragraphs
                if len(sub_text) > MAX_CHUNK_SIZE:
                    paragraphs = _split_paragraphs(sub_text, MAX_CHUNK_SIZE)
                    for i, para in enumerate(paragraphs):
                        if len(para.strip()) < MIN_CHUNK_SIZE:
                            continue
                        chunks.append(Chunk(
                            text=para.strip(),
                            heading=f"{sub_display} (part {i+1})" if len(paragraphs) > 1 else sub_display,
                            heading_path=full_path,
                            level=3,
                            chunk_index=chunk_index,
                            char_count=len(para.strip()),
                        ))
                        chunk_index += 1
                else:
                    chunks.append(Chunk(
                        text=sub_text.strip(),
                        heading=sub_display,
                        heading_path=full_path,
                        level=3 if sub_heading else 2,
                        chunk_index=chunk_index,
                        char_count=len(sub_text.strip()),
                    ))
                    chunk_index += 1

    return chunks


def _split_by_heading(text: str, pattern: re.Pattern) -> list[tuple[str, str]]:
    """Split text by heading pattern into (heading, content) pairs.

    Content before the first heading is returned with heading="".
    """
    parts = pattern.split(text)
    sections = []

    # Content before first heading
    if parts[0].strip():
        sections.append(("", parts[0]))

    # Heading + content pairs
    for i in range(1, len(parts), 2):
        heading = parts[i] if i < len(parts) else ""
        content_part = parts[i + 1] if i + 1 < len(parts) else ""
        sections.append((heading, content_part))

    return sections


def _split_paragraphs(text: str, max_size: int) -> list[str]:
    """Split text on double newlines, combining small paragraphs to approach max_size."""
    paragraphs = re.split(r'\n\n+', text)
    result = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) > max_size and current:
            result.append(current)
            current = para
        else:
            current = current + "\n\n" + para if current else para

    if current:
        result.append(current)

    return result
