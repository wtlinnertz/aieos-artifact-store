"""Test fixtures for AIEOS Artifact Store tests."""

import pytest
from pathlib import Path


def pytest_addoption(parser):
    parser.addoption(
        "--run-slow", action="store_true", default=False,
        help="Run slow tests (embedding model download, full ingest cycle)"
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

AIEOS_ROOT = Path(__file__).parent.parent.parent  # aieos workspace root


@pytest.fixture
def sample_artifact():
    """A minimal frozen AIEOS artifact for testing."""
    return """# System Architecture Document

## §1 Document Control

| Field | Value |
|-------|-------|
| Artifact ID | SAD-TESTINIT-001 |
| Initiative | TESTINIT |
| Status | Frozen |
| Frozen Date | 2026-03-20 |
| Spec Version | v1.1 |
| Governance Model Version | v1.2 |

## §2 Architecture Overview

The system uses a microservices architecture with three core services: API Gateway, Auth Service, and Data Service. All inter-service communication uses gRPC with protobuf contracts.

The API Gateway handles request routing, rate limiting, and authentication token validation. It delegates to downstream services via service mesh.

## §3 Major Components

### API Gateway
Handles all external HTTP traffic. Routes requests to appropriate services. Implements rate limiting and circuit breaker patterns.

### Auth Service
Manages user authentication via OAuth2 with PKCE. Issues JWT tokens with 15-minute expiry. Supports refresh token rotation.

### Data Service
Provides CRUD operations on the core domain model. Uses PostgreSQL with read replicas. Implements event sourcing for audit trail.

## §4 Interface Contracts

| Interface | Provider | Consumer | Protocol | Contract |
|-----------|----------|----------|----------|----------|
| /api/v1/* | API Gateway | External clients | HTTP/REST | OpenAPI spec |
| auth.v1.AuthService | Auth Service | API Gateway | gRPC | auth.proto |
| data.v1.DataService | Data Service | API Gateway | gRPC | data.proto |

## §5 Deployment Architecture

Deployed on Kubernetes with 3 namespaces: production, staging, development. Each service runs 2 replicas minimum in production with horizontal pod autoscaler.

## §6 Architecture Decisions

### AD-001: gRPC for inter-service communication
Chosen over REST for type safety and performance. Protobuf contracts prevent interface drift.

### AD-002: Event sourcing for audit trail
Chosen over traditional audit logging for complete state reconstruction and compliance requirements.
"""


@pytest.fixture
def sample_draft_artifact():
    """A draft (not frozen) artifact — should be skipped during ingestion."""
    return """# Problem Framing Document

## §1 Document Control

| Field | Value |
|-------|-------|
| Artifact ID | PFD-TESTINIT-001 |
| Status | Draft |

## §2 Problem Definition

Users cannot find relevant search results.
"""


@pytest.fixture
def sample_er():
    """A minimal Engagement Record."""
    return """# Engagement Record — TESTINIT

## §1 Document Control

| Field | Value |
|-------|-------|
| ER ID | ER-TESTINIT-001 |
| Initiative | Test Initiative |
| Status | Active |
| Preset | P1 |

## §1b State Block

| Field | Value |
|-------|-------|
| Current Layer | 4 — Engineering Execution |
| Current Artifact | TDD |
| Frozen Count | 5 |
| Next Action | Generate TDD from frozen SAD |

## §2 Layer 2 — Product Intelligence

| Artifact Type | ID | Status |
|--------------|-----|--------|
| PFD | PFD-TESTINIT-001 | Frozen |
| VH | VH-TESTINIT-001 | Frozen |
"""


@pytest.fixture
def console_sdlc_dir():
    """Path to the real aieos-console SDLC directory (if it exists)."""
    path = AIEOS_ROOT / "aieos-console" / "docs" / "sdlc"
    if path.exists():
        return path
    pytest.skip("aieos-console not found — skipping real artifact test")
