#!/usr/bin/env python3
"""Re-freeze the CD spec with a real artifact digest.

The pilot's `.aieos/cd.spec.yaml` ships with a placeholder digest. When a
real CI run produces a digest via publish.artifact, run this script to
substitute it in and recompute the spec hash for the pipeline runner.

Usage:
    python3 .aieos/refreeze-cd.py <full-oci-ref-with-digest>

Example:
    python3 .aieos/refreeze-cd.py \\
        ghcr.io/wtlinnertz/aieos-artifact-store@sha256:abc123...

The script:
  1. Validates the input matches `<host>/<path>@sha256:<64-hex>` shape.
  2. Reads .aieos/cd.spec.yaml and substitutes artifact_ref.
  3. Writes the new content back, recomputes sha256, and prints the
     hash so the GHA workflow can pin --expected-hash.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

DIGEST_REF_PATTERN = re.compile(
    r"^[a-z0-9.-]+(/[a-z0-9._-]+)+@sha256:[0-9a-f]{64}$"
)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    new_ref = argv[1]
    if not DIGEST_REF_PATTERN.match(new_ref):
        print(
            f"[error] invalid OCI ref: {new_ref!r}\n"
            "expected <registry>/<path>@sha256:<64-hex>",
            file=sys.stderr,
        )
        return 1

    cd_path = Path(__file__).parent / "cd.spec.yaml"
    text = cd_path.read_text()

    # Replace the artifact_ref line conservatively — only the line beginning
    # with "artifact_ref:" gets touched.
    new_lines = []
    replaced = False
    for line in text.splitlines():
        if line.startswith("artifact_ref:") and not replaced:
            new_lines.append(f'artifact_ref: "{new_ref}"')
            replaced = True
        else:
            new_lines.append(line)
    if not replaced:
        print("[error] could not locate artifact_ref: line in cd.spec.yaml", file=sys.stderr)
        return 1

    new_text = "\n".join(new_lines) + "\n"
    if new_text == text:
        print(f"[noop] artifact_ref already set to {new_ref}")
        return 0

    cd_path.write_text(new_text)
    new_hash = hashlib.sha256(new_text.encode("utf-8")).hexdigest()
    print(f"refrozen {cd_path}")
    print(f"new artifact_ref: {new_ref}")
    print(f"new sha256:        {new_hash}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
