#!/usr/bin/env bash
# AIEOS M6.7 chaos tests — deliberate failure scenarios.
#
# Exercises the five failure modes that don't require a live Kubernetes
# cluster. Each must fail LOUDLY with a specific exit code and a clear
# diagnostic on stderr. Silent passes are regressions.
#
# Scenario 6 (Flux refusing to reconcile invalid YAML) requires a live
# Flux installation and is deferred to operator integration tests.
#
# Usage: bash .aieos/chaos-tests.sh
# Exit 0 if every scenario behaved as expected; 1 on any surprise.

set -euo pipefail

cd "$(dirname "$0")/.."
WORKDIR=$(mktemp -d -t aieos-chaos-XXXXXX)
trap 'rm -rf "$WORKDIR"' EXIT

EXPECTED_CI_HASH=$(python3 -c "import hashlib; print(hashlib.sha256(open('.aieos/ci.spec.yaml','rb').read()).hexdigest())")

overall=0
report_result() {
    local name="$1" expected="$2" actual="$3"
    if [[ "$expected" == "$actual" ]]; then
        printf "  [PASS] %-40s (exit %s)\n" "$name" "$actual"
    else
        printf "  [FAIL] %-40s expected exit %s, got %s\n" "$name" "$expected" "$actual"
        overall=1
    fi
}

echo "=== scenario 2: submit unfrozen spec (hash mismatch) ==="
cp .aieos/ci.spec.yaml "$WORKDIR/mangled.yaml"
printf '\n# deliberate mutation\n' >> "$WORKDIR/mangled.yaml"
set +e
aieos-pipeline-runner run \
    --spec "$WORKDIR/mangled.yaml" \
    --expected-hash "$EXPECTED_CI_HASH" \
    --use-mock-adapters \
    --run-id chaos-2 \
    >/dev/null 2> "$WORKDIR/chaos-2.err"
code=$?
set -e
report_result "unfrozen spec -> runner refuses" 2 "$code"
grep -q "hash" "$WORKDIR/chaos-2.err" || { echo "  missing 'hash' in diagnostic"; overall=1; }

echo
echo "=== scenario 3: spec references an action not in the taxonomy ==="
python3 <<EOF > "$WORKDIR/bogus-action.yaml"
import yaml
with open(".aieos/ci.spec.yaml") as f:
    doc = yaml.safe_load(f)
doc["actions"].insert(0, {"action": "bogus.action", "criteria": {}})
print(yaml.safe_dump(doc, sort_keys=False))
EOF
BOGUS_HASH=$(python3 -c "import hashlib; print(hashlib.sha256(open('$WORKDIR/bogus-action.yaml','rb').read()).hexdigest())")
set +e
aieos-pipeline-runner run \
    --spec "$WORKDIR/bogus-action.yaml" \
    --expected-hash "$BOGUS_HASH" \
    --use-mock-adapters \
    --run-id chaos-3 \
    >/dev/null 2> "$WORKDIR/chaos-3.err"
code=$?
set -e
report_result "unknown action -> spec validator fails" 1 "$code"
grep -q "bogus.action" "$WORKDIR/chaos-3.err" || { echo "  missing 'bogus.action' in diagnostic"; overall=1; }

echo
echo "=== scenario 4a: non-mock flag refused in v1 ==="
set +e
aieos-pipeline-runner run \
    --spec .aieos/ci.spec.yaml \
    --expected-hash "$EXPECTED_CI_HASH" \
    --run-id chaos-4a \
    >/dev/null 2> "$WORKDIR/chaos-4a.err"
code=$?
set -e
report_result "non-mock adapters -> infra error" 2 "$code"
grep -q "non-mock" "$WORKDIR/chaos-4a.err" || { echo "  missing 'non-mock' in diagnostic"; overall=1; }

echo
echo "=== scenario 5: cyclic dependency fails spec validation ==="
python3 <<EOF > "$WORKDIR/cyclic.yaml"
import yaml
with open(".aieos/ci.spec.yaml") as f:
    doc = yaml.safe_load(f)
# Force test.unit to depend on build.artifact while build.artifact already
# depends on test.unit -> cycle.
for a in doc["actions"]:
    if a["action"] == "test.unit":
        a["depends_on"] = ["build.artifact"]
print(yaml.safe_dump(doc, sort_keys=False))
EOF
CYCLE_HASH=$(python3 -c "import hashlib; print(hashlib.sha256(open('$WORKDIR/cyclic.yaml','rb').read()).hexdigest())")
set +e
aieos-pipeline-runner run \
    --spec "$WORKDIR/cyclic.yaml" \
    --expected-hash "$CYCLE_HASH" \
    --use-mock-adapters \
    --run-id chaos-5 \
    >/dev/null 2> "$WORKDIR/chaos-5.err"
code=$?
set -e
report_result "cyclic DAG -> spec validator fails" 1 "$code"
grep -q "cycle" "$WORKDIR/chaos-5.err" || { echo "  missing 'cycle' in diagnostic"; overall=1; }

echo
echo "=== scenario 6 (deferred): Flux refusing invalid YAML ==="
echo "  [SKIP] requires a live Flux installation; covered by operator"
echo "         integration tests in a later milestone."

echo
if [[ $overall -eq 0 ]]; then
    echo "ALL CHAOS SCENARIOS BEHAVED AS EXPECTED"
else
    echo "ONE OR MORE CHAOS SCENARIOS REGRESSED"
fi
exit $overall
