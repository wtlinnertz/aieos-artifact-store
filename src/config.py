"""AIEOS Artifact Store — Configuration."""

import os
from pathlib import Path

# Paths
STORE_PATH = Path(os.environ.get("AIEOS_STORE_PATH", Path(__file__).parent.parent / "store" / "artifacts.lance"))
AIEOS_ROOT = Path(os.environ.get("AIEOS_ROOT", Path(__file__).parent.parent.parent))

# Embedding
EMBEDDING_MODEL = os.environ.get("AIEOS_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DIMENSIONS = int(os.environ.get("AIEOS_EMBEDDING_DIMENSIONS", "384"))

# Chunking
MAX_CHUNK_SIZE = int(os.environ.get("AIEOS_MAX_CHUNK_SIZE", "2000"))
MIN_CHUNK_SIZE = int(os.environ.get("AIEOS_MIN_CHUNK_SIZE", "100"))

# Query
DEFAULT_LIMIT = int(os.environ.get("AIEOS_QUERY_LIMIT", "10"))
HYBRID_WEIGHT = float(os.environ.get("AIEOS_HYBRID_WEIGHT", "0.7"))  # 70% semantic, 30% keyword

# Ingestion
SKIP_DRAFT = True
SKIP_FRAMEWORK = True  # Don't ingest specs/templates/prompts/validators
INGEST_ER = True
INGEST_JOURNAL = True
INGEST_RETROSPECTIVE = True

# Artifact type → kit → layer mapping
KIT_MAP = {
    "SBR": ("SDK", 1), "PPR": ("SDK", 1), "CLA": ("SDK", 1), "PCR": ("SDK", 1), "TIR": ("SDK", 1),
    "WCR": ("PIK", 2), "PFD": ("PIK", 2), "VH": ("PIK", 2), "AR": ("PIK", 2), "EL": ("PIK", 2), "DPRD": ("PIK", 2),
    "SOER": ("SSK", 3), "VER": ("SSK", 3), "SDR": ("SSK", 3),
    "KER": ("EEK", 4), "PRD": ("EEK", 4), "ACF": ("EEK", 4), "DKR": ("EEK", 4), "SAD": ("EEK", 4), "DCF": ("EEK", 4),
    "TDD": ("EEK", 4), "WDD": ("EEK", 4), "ORD": ("EEK", 4),
    "RER": ("REK", 5), "RCF": ("REK", 5), "RSA": ("REK", 5), "RP": ("REK", 5), "RR": ("REK", 5),
    "SRER": ("RRK", 6), "SRP": ("RRK", 6), "IR": ("RRK", 6), "RHR": ("RRK", 6),
    "ES": ("IEK", 7), "PES": ("IEK", 7),
    "DCR": ("ODK", 8), "INR": ("ODK", 8), "PMR": ("ODK", 8), "RB": ("ODK", 8),
    "QAER": ("QAK", 9), "VP": ("QAK", 9), "TCR": ("QAK", 9), "QGR": ("QAK", 9),
    "TM": ("SCK", 10), "SAR": ("SCK", 10), "CER": ("SCK", 10), "DAR": ("SCK", 10),
    "CSPEC": ("DCK", 11), "FFLR": ("DCK", 11), "DSR": ("DCK", 11), "DMR": ("DCK", 11),
    "PDR": ("PINFK", 12), "ISPEC": ("PINFK", 12), "EM": ("PINFK", 12), "SMR": ("PINFK", 12),
    "UDR": ("DKK", 13), "ARR": ("DKK", 13), "SKA": ("DKK", 13), "DHR": ("DKK", 13),
    "PRR": ("PRK", 14),
    "PIA": ("BPK", 15), "TP": ("BPK", 15), "RC": ("BPK", 15),
}
