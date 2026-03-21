# Artifact Store Integration Guide

How the AIEOS sherpa and generation prompts query the artifact store.

## Three Integration Points

### 1. Discovery Context

When generating a new artifact (e.g., a SAD for initiative ALPHA), the sherpa queries the store for SADs from other initiatives to provide architectural precedent.

```bash
# From a generation prompt or sherpa script
python -m src.query "microservices architecture API gateway" \
    --type SAD \
    --format context \
    --limit 3
```

The `--format context` output is a fenced Markdown block ready to paste into an AI prompt's context section:

```
--- artifact-store result 1 of 3 ---
Source: SAD-CONSOLE-001 §3 Major Components (Layer 4, EEK)
Initiative: CONSOLE | Frozen: 2026-03-05

[chunk text here]
--- end result 1 ---
```

### 2. Assumption Dedup

Before introducing an assumption in a PRD or SAD, query the store for prior validated or invalidated assumptions:

```bash
python -m src.query "assumption: users prefer single sign-on" \
    --type PRD,SAD,VH \
    --format json \
    --limit 5
```

The JSON output includes metadata fields for programmatic checking:

```json
[
  {
    "text": "Assumption A3: Users strongly prefer SSO...",
    "artifact_id": "PRD-TASKFLOW-001",
    "initiative": "TASKFLOW",
    "kit": "PIK",
    "layer": 2,
    "heading_path": "PRD-TASKFLOW-001 > §4 Assumptions",
    "score": 0.87
  }
]
```

### 3. Architecture Precedent

During SAD and TDD generation, query for prior architecture decisions on similar topics:

```bash
python -m src.query "event sourcing audit trail" \
    --type SAD,TDD \
    --format context \
    --limit 3
```

This surfaces prior decisions, their rationale, and alternatives considered — helping maintain portfolio-wide architectural consistency.

## Querying from Any AI

For manual use with any AI assistant, run the query and paste the output into your prompt:

```bash
python -m src.query "your topic here" --format context
```

Then include the output in your AI prompt as:

```
## Prior Art (from artifact store)

[paste output here]

## Task

Generate the SAD for initiative ALPHA, considering the prior art above.
```

## Advisory-Only Rule

Store query results enrich context but never block artifact generation. Specifically:

- A generation prompt must not fail because the store is empty or unavailable.
- A validator must not check whether the store was consulted.
- Prior art from the store is input context, not a constraint. The current initiative's specs and frozen upstream artifacts always take precedence.

If the store is unavailable (not built, corrupted, or the query fails), the generation prompt proceeds without prior art context. No error is raised to the user. The sherpa may note that prior art was not available, but this is informational only.

## When the Store Is Empty

On a fresh AIEOS installation or when no initiatives have completed, the store contains no chunks. In this case:

- All queries return empty results.
- The `--format context` output is an empty string.
- Generation prompts proceed normally without prior art context.
- The sherpa may suggest running `bash scripts/ingest-all.sh` after the first initiative freezes artifacts.

There is no bootstrap problem: the store becomes useful after the first initiative produces frozen artifacts, and its value grows with each subsequent initiative.
