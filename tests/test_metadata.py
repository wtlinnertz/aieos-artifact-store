"""Tests for metadata extraction."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.metadata import extract_metadata, is_frozen, is_framework_file


class TestExtractMetadata:
    def test_extracts_from_document_control(self, sample_artifact):
        meta = extract_metadata(sample_artifact, "aieos-testinit/docs/sdlc/04-sad.md")
        assert meta.artifact_id == "SAD-TESTINIT-001"
        assert meta.artifact_type == "SAD"
        assert meta.initiative == "TESTINIT"
        assert meta.kit == "EEK"
        assert meta.layer == 4
        assert meta.status == "Frozen"

    def test_derives_kit_from_type(self, sample_artifact):
        meta = extract_metadata(sample_artifact, "04-sad.md")
        assert meta.kit == "EEK"
        assert meta.layer == 4

    def test_handles_missing_fields(self):
        content = "# Just a heading\n\nSome content."
        meta = extract_metadata(content, "unknown.md")
        assert meta.artifact_id == ""
        assert meta.artifact_type == ""

    def test_extracts_initiative_from_path(self):
        content = "## §1 Doc Control\n\n| Field | Value |\n|---|---|\n| Status | Frozen |"
        meta = extract_metadata(content, "/home/user/aieos-taskflow/docs/sdlc/04-sad.md")
        assert meta.initiative == "TASKFLOW"


class TestIsFrozen:
    def test_frozen_status(self, sample_artifact):
        meta = extract_metadata(sample_artifact, "sad.md")
        assert is_frozen(sample_artifact, meta) is True

    def test_draft_status(self, sample_draft_artifact):
        meta = extract_metadata(sample_draft_artifact, "pfd.md")
        assert is_frozen(sample_draft_artifact, meta) is False


class TestIsFrameworkFile:
    def test_spec_file(self):
        assert is_framework_file("aieos-eek/docs/specs/sad-spec.md") is True

    def test_validator_file(self):
        assert is_framework_file("aieos-eek/docs/validators/sad-validator.md") is True

    def test_sdlc_file(self):
        assert is_framework_file("aieos-console/docs/sdlc/04-sad.md") is False

    def test_engagement_file(self):
        assert is_framework_file("aieos-console/docs/engagement/er-CONSOLE-001.md") is False
