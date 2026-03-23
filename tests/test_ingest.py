"""Integration tests for ingestion pipeline.

These tests require the embedding model to be downloaded.
Mark with @pytest.mark.slow for CI skipping.
"""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.mark.slow
class TestIngestArtifact:
    def test_ingests_frozen_artifact(self, sample_artifact, tmp_path):
        # Write sample to temp file
        artifact_file = tmp_path / "04-sad.md"
        artifact_file.write_text(sample_artifact, encoding="utf-8")

        # Override store path
        import src.config as config
        original_path = config.STORE_PATH
        config.STORE_PATH = tmp_path / "test.lance"

        try:
            from src.ingest import ingest_artifact
            result = ingest_artifact(str(artifact_file))
            assert not result["skipped"]
            assert result["chunks"] > 0
            assert result["artifact_id"] == "SAD-TESTINIT-001"
        finally:
            config.STORE_PATH = original_path

    def test_skips_draft_artifact(self, sample_draft_artifact, tmp_path):
        artifact_file = tmp_path / "03-pfd.md"
        artifact_file.write_text(sample_draft_artifact, encoding="utf-8")

        import src.config as config
        original_path = config.STORE_PATH
        config.STORE_PATH = tmp_path / "test.lance"

        try:
            from src.ingest import ingest_artifact
            result = ingest_artifact(str(artifact_file))
            assert result["skipped"]
            assert result["reason"] == "not frozen"
        finally:
            config.STORE_PATH = original_path


@pytest.mark.slow
class TestIngestAndQuery:
    def test_end_to_end(self, sample_artifact, tmp_path):
        """Ingest an artifact and query it."""
        artifact_file = tmp_path / "04-sad.md"
        artifact_file.write_text(sample_artifact, encoding="utf-8")

        import src.config as config
        original_path = config.STORE_PATH
        config.STORE_PATH = tmp_path / "test.lance"

        try:
            from src.ingest import ingest_artifact
            from src.embeddings import embed_query
            import lancedb

            # Ingest
            result = ingest_artifact(str(artifact_file))
            assert result["chunks"] > 0

            # Query directly against the temp store
            db = lancedb.connect(str(tmp_path))
            table = db.open_table("artifacts")
            query_vector = embed_query("authentication architecture")
            results_df = table.search(query_vector).limit(5).to_pandas()

            assert len(results_df) > 0
            assert any("auth" in str(row.get("text", "")).lower() for _, row in results_df.iterrows())
        finally:
            config.STORE_PATH = original_path
