# .aieos/ — pilot governance artifacts

This directory holds the frozen AIEOS CI and CD specs for the
`aieos-artifact-store` pilot (Milestone 6).

## Contents

| File | Purpose | Schema |
|---|---|---|
| `ci.spec.yaml` | Frozen CI spec — 11 action instances covering test, scan, SBOM, build, sign, publish | `aieos-governance-foundation/schema/ci-spec.schema.json @ v1.0-ci-spec-schema` |
| `cd.spec.yaml` | Frozen CD spec — 3 environments (dev, staging, prod), auto-promote dev→staging, manual-gate staging→prod | `aieos-governance-foundation/schema/cd-spec.schema.json @ v1.0-cd-spec-schema` |
| `chaos-tests.sh` | M6.7 failure-mode regression checks — four scenarios, all locally runnable | — |

## Spec freeze

Both specs validate against their frozen v1.0 schemas. Compute the hash
the pipeline runner requires before every run:

```bash
python3 -c "import hashlib; print(hashlib.sha256(open('.aieos/ci.spec.yaml','rb').read()).hexdigest())"
python3 -c "import hashlib; print(hashlib.sha256(open('.aieos/cd.spec.yaml','rb').read()).hexdigest())"
```

The runner refuses unfrozen specs (supplying a mismatched hash exits 2).

## Pilot state (M6)

- ✅ Containerized (`Containerfile`) — multi-stage, non-root, runs stdlib
  health server on 8080.
- ✅ Kubernetes manifests (`kustomize/` with `base/` + dev/staging/prod
  overlays).
- ✅ Flux config (`flux/` with `GitRepository` + three `Kustomization`
  resources).
- ✅ Frozen CI + CD specs (this directory).
- ✅ GHA workflow (`.github/workflows/aieos-ci.yml`) — dry-run against
  mock adapters on every push + PR.
- ✅ Chaos-test regression script (four in-scope scenarios).

## Deferred to a follow-on

- **Real-adapter wiring.** The ten v1 adapters live in separate repos
  with passing unit tests, but registering them with a running harness
  and producing real conformance attestations in adapter CI requires an
  operator-managed integration step.
- **Live Kubernetes + Flux cluster.** Actual CD execution (manifest
  commit → Flux reconcile → verify.smoke/health) needs a target cluster.
  Chaos scenario 6 (Flux refusing invalid YAML) is part of this integration.
- **CD artifact_ref re-freeze.** `cd.spec.yaml` carries a placeholder
  digest; the CD authoring flow re-freezes with the real digest after
  CI's `publish.artifact` produces it.

## Demonstration run

The M6 session produced a dry-run that exercises every action via the
mock adapter:

```text
run_id:  m6-pilot-ci-dry-run
actions: 11 (test.unit + test.integration + 3x security.* +
              sbom.generate + build.artifact + security.container-scan
              + sign.artifact + sign.attestation + publish.artifact)
events:  run.start + (task.start + task.evidence + task.result)*11 + run.end
result:  PASS (every criterion satisfied; record + report in artifact store)
exit:    0
```
