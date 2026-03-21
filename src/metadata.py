"""AIEOS Artifact Store — Metadata extraction from AIEOS artifacts.

Extracts structured metadata from Document Control sections, filenames,
and directory structure.
"""

import re
from pathlib import Path
from dataclasses import dataclass, field
from src.config import KIT_MAP
from src.chunker import extract_document_control


@dataclass
class ArtifactMetadata:
    """Metadata for a single artifact."""
    artifact_id: str = ""
    artifact_type: str = ""
    initiative: str = ""
    kit: str = ""
    layer: int = 0
    status: str = ""
    frozen_date: str = ""
    spec_version: str = ""
    completeness_score: int = 0
    file_path: str = ""


def extract_metadata(content: str, file_path: str) -> ArtifactMetadata:
    """Extract metadata from an artifact's content and file path.

    Priority:
    1. Document Control table fields (most authoritative)
    2. Artifact ID parsed for type and initiative
    3. File path and directory structure (fallback)

    Args:
        content: Full Markdown text of the artifact.
        file_path: Absolute or relative path to the artifact file.

    Returns:
        ArtifactMetadata with all extractable fields populated.
    """
    meta = ArtifactMetadata(file_path=file_path)

    # Extract from Document Control table
    doc_control = extract_document_control(content)

    # Artifact ID — try several common field names
    for key in ('artifact id', 'id', 'er id', 'artifact', 'record id'):
        if key in doc_control:
            meta.artifact_id = doc_control[key]
            break

    # If no ID in doc control, try to find one in the first 500 chars
    if not meta.artifact_id:
        id_match = re.search(r'([A-Z]{2,6})-([A-Z][A-Z0-9-]+)-(\d{3})', content[:500])
        if id_match:
            meta.artifact_id = id_match.group(0)

    # Parse artifact type and initiative from ID
    if meta.artifact_id:
        id_match = re.match(r'([A-Z]{2,6})-([A-Z][A-Z0-9-]+)-\d{3}', meta.artifact_id)
        if id_match:
            meta.artifact_type = id_match.group(1)
            meta.initiative = id_match.group(2)

    # If type not found from ID, try to derive from filename
    if not meta.artifact_type:
        filename = Path(file_path).stem
        # Strip numeric prefix (e.g., "04-sad" → "sad")
        type_from_name = re.sub(r'^\d+-', '', filename).upper().replace('-', '')
        # Check if it maps to a known type
        for known_type in KIT_MAP:
            if type_from_name.startswith(known_type):
                meta.artifact_type = known_type
                break

    # Derive kit and layer from artifact type
    if meta.artifact_type and meta.artifact_type in KIT_MAP:
        meta.kit, meta.layer = KIT_MAP[meta.artifact_type]

    # Initiative from directory structure if not found in ID
    if not meta.initiative:
        path_parts = Path(file_path).parts
        for part in path_parts:
            if part.startswith('aieos-') and part not in ('aieos-governance-foundation', 'aieos-sherpa', 'aieos-artifact-store'):
                meta.initiative = part.replace('aieos-', '').upper()
                break

    # Status
    for key in ('status',):
        if key in doc_control:
            meta.status = doc_control[key]
            break
    if not meta.status:
        if 'frozen' in content[:3000].lower():
            meta.status = "Frozen"
        elif 'draft' in content[:3000].lower():
            meta.status = "Draft"

    # Frozen date
    for key in ('frozen date', 'freeze date', 'frozen'):
        if key in doc_control:
            meta.frozen_date = doc_control[key]
            break

    # Spec version
    for key in ('spec version', 'version'):
        if key in doc_control:
            meta.spec_version = doc_control[key]
            break

    # Completeness score — look for it in content
    score_match = re.search(r'completeness[_\s]*score[:\s]*(\d+)', content, re.IGNORECASE)
    if score_match:
        meta.completeness_score = int(score_match.group(1))

    return meta


def is_frozen(content: str, metadata: ArtifactMetadata) -> bool:
    """Check if an artifact is frozen (should be ingested)."""
    if metadata.status.lower() == "frozen":
        return True
    # Check for Frozen in content near Document Control
    if re.search(r'\|\s*Status\s*\|\s*Frozen\s*\|', content[:3000], re.IGNORECASE):
        return True
    return False


def is_framework_file(file_path: str) -> bool:
    """Check if a file is a framework file (should NOT be ingested)."""
    path = Path(file_path)
    # Framework directories
    framework_dirs = {'specs', 'validators', 'prompts', 'artifacts', 'tools', 'bindings', 'principles'}
    return any(part in framework_dirs for part in path.parts)
