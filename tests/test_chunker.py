"""Tests for Markdown-aware chunking."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chunker import chunk_artifact, extract_document_control


class TestExtractDocumentControl:
    def test_extracts_standard_fields(self, sample_artifact):
        dc = extract_document_control(sample_artifact)
        assert dc.get("artifact id") == "SAD-TESTINIT-001"
        assert dc.get("status") == "Frozen"
        assert dc.get("spec version") == "v1.1"

    def test_handles_missing_doc_control(self):
        dc = extract_document_control("# Just a heading\n\nSome text.")
        assert dc == {}


class TestChunkArtifact:
    def test_splits_on_h2_headings(self, sample_artifact):
        chunks = chunk_artifact(sample_artifact, "04-sad.md")
        headings = [c.heading for c in chunks]
        assert "§2 Architecture Overview" in headings
        assert "§3 Major Components" in headings
        assert "§4 Interface Contracts" in headings

    def test_skips_document_control(self, sample_artifact):
        chunks = chunk_artifact(sample_artifact, "04-sad.md")
        headings = [c.heading for c in chunks]
        assert "§1 Document Control" not in headings

    def test_preserves_tables(self, sample_artifact):
        chunks = chunk_artifact(sample_artifact, "04-sad.md")
        interface_chunk = [c for c in chunks if "Interface" in c.heading]
        assert interface_chunk
        assert "gRPC" in interface_chunk[0].text

    def test_assigns_chunk_indices(self, sample_artifact):
        chunks = chunk_artifact(sample_artifact, "04-sad.md")
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_builds_heading_path(self, sample_artifact):
        chunks = chunk_artifact(sample_artifact, "04-sad.md")
        assert all("04-sad" in c.heading_path for c in chunks)

    def test_skips_small_chunks(self):
        content = "## §1 Doc Control\n\n| F | V |\n\n## §2 Real\n\nSubstantive content here that is long enough to be meaningful and worth embedding into the vector store for future retrieval.\n\n## §3 Tiny\n\nX"
        chunks = chunk_artifact(content)
        headings = [c.heading for c in chunks]
        assert "§3 Tiny" not in headings

    def test_strips_html_comments(self):
        content = "## §2 Content\n\n<!-- Elicitation: pre-mortem applied -->\n\nActual content that is substantive enough to be a valid chunk for the vector store. This text needs to exceed the minimum chunk size threshold so the chunker doesn't skip it as too small. Adding more context about the architecture decisions made during the pre-mortem analysis session."
        chunks = chunk_artifact(content)
        assert chunks
        assert "Elicitation" not in chunks[0].text

    def test_empty_content_returns_no_chunks(self):
        assert chunk_artifact("") == []
