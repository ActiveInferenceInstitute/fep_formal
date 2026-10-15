"""Generate or inspect the minimal original-source custody unit fixture.

Generation needs the exact public Git object below. Offline ``--check`` and
normal tests use the committed artifact and never need historical Git objects.
The archived Lean/test bytes are custody inputs only, never executed here.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "5e1cc9095b5f0590772c739d27558c2c711f9a44"
RESOURCE = "tests/fixtures/historical_h3_custody_sources.json"
FIXTURE_SHA256 = "2e279ffd13826b1eb2a07a5652d8e07e52ce5e0e3590b041418ab46d8a126eb1"
ENCODING = "zlib+base64"
BOUNDARY = (
    "Original public source bytes for offline historical custody unit controls. "
    "No Lean/test execution, current native acceptance, or renewed scientific approval."
)
SOURCES = {
    "src/fep_lean/formal/compositions/h3_case_study.lean": (
        "7a8ba9346dc9ab700ac6276c26421b46c0437eabaab7cd448a2bc05998318849",
        252275,
    ),
    "tests/test_horizon2_gaussian_vfe_readiness.py": (
        "b36f3a1b9e80f7e83705178c31d7483b8a334e8c2d905508f39154e13fcb2455",
        34650,
    ),
}


def canonical(payload: dict[str, object]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()


def generate() -> dict[str, object]:
    sources: dict[str, object] = {}
    for relative, (expected_sha, expected_size) in SOURCES.items():
        result = subprocess.run(
            ["git", "show", f"{COMMIT}:{relative}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        data = result.stdout
        assert len(data) == expected_size, relative
        assert hashlib.sha256(data).hexdigest() == expected_sha, relative
        sources[relative] = {
            "sha256": expected_sha,
            "size": expected_size,
            "data": base64.b64encode(zlib.compress(data, level=9)).decode("ascii"),
        }
    return {
        "schema_version": 1,
        "kind": "historical-h3-custody-unit-sources",
        "source_commit": COMMIT,
        "encoding": ENCODING,
        "evidence_boundary": BOUNDARY,
        "files": sources,
    }


def check(raw: bytes) -> None:
    assert hashlib.sha256(raw).hexdigest() == FIXTURE_SHA256, "fixture identity changed"
    payload = json.loads(raw)
    assert raw == canonical(payload), "noncanonical fixture JSON"
    assert set(payload) == {
        "schema_version",
        "kind",
        "source_commit",
        "encoding",
        "evidence_boundary",
        "files",
    }
    assert type(payload["schema_version"]) is int and payload["schema_version"] == 1
    assert payload["kind"] == "historical-h3-custody-unit-sources"
    assert payload["source_commit"] == COMMIT
    assert payload["encoding"] == ENCODING
    assert payload["evidence_boundary"] == BOUNDARY
    assert set(payload["files"]) == set(SOURCES)
    addendum = json.loads(
        (
            ROOT / "specs/done/horizon-2-smooth-stochastic/readiness/repairs/"
            "07-gaussian-vfe-natural-gradient-h3-custody.json"
        ).read_bytes()
    )
    for relative, (expected_sha, expected_size) in SOURCES.items():
        entry = payload["files"][relative]
        assert set(entry) == {"sha256", "size", "data"}
        assert entry["sha256"] == expected_sha == addendum["source_sha256"][relative]
        assert type(entry["size"]) is int and entry["size"] == expected_size
        data = zlib.decompress(base64.b64decode(entry["data"], validate=True))
        assert len(data) == expected_size, relative
        assert hashlib.sha256(data).hexdigest() == expected_sha, relative


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="read original Git bytes")
    mode.add_argument("--check", action="store_true", help="validate offline fixture")
    args = parser.parse_args()
    resource = ROOT / RESOURCE
    if args.write:
        raw = canonical(generate())
        check(raw)
        resource.write_bytes(raw)
    else:
        raw = resource.read_bytes()
        check(raw)
    print(f"{RESOURCE}: {len(raw)} bytes; sha256={hashlib.sha256(raw).hexdigest()}")


if __name__ == "__main__":
    main()
