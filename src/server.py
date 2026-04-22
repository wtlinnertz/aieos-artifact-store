"""Minimal HTTP health-check server for Kubernetes liveness/readiness probes.

Stdlib-only. Serves /healthz and /readyz on port 8080. Runs on the main
thread and is the container's default entrypoint; the artifact-store
ingest/query operations continue to be invoked via `python -m src.ingest`
or `python -m src.query` as separate one-shot workloads, unchanged.

The rationale for a trivial health endpoint rather than a full FastAPI
service is honesty: the pilot's purpose is to exercise the AIEOS pipeline
(test, build, scan, sign, publish, deploy, verify), not to retrofit a
web-service architecture onto a batch library. K8s still needs an always-on
pod for verify.smoke + verify.health to probe; this server provides it
without dragging in new dependencies.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "0.0.0.0"  # noqa: S104 — intentional: pod network exposure
PORT = 8080


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._ok({"status": "ok", "service": "aieos-artifact-store"})
        elif self.path == "/readyz":
            self._ok({"ready": True})
        else:
            self.send_error(404)

    def _ok(self, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # Silence access logs; k8s probes spam them.
    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def main() -> None:
    server = HTTPServer((HOST, PORT), _Handler)
    print(f"health server listening on {HOST}:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
