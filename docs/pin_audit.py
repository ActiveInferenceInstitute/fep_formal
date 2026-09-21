#!/usr/bin/env python3
"""Audit toolchain and model pins across project markdown for drift.

Canonical sources of truth (read at every invocation, never the docs):

- ``lean/lean-toolchain``                     -> Lean toolchain string
                                                  (e.g. ``leanprover/lean4:v4.33.1``)
- ``lean/lakefile.lean``                      -> Mathlib4 git tag
                                                  (e.g. ``v4.33.1``)
- ``lean/lake-manifest.json``                 -> resolved Mathlib Git revision
- ``config/settings.yaml::hermes.model``      -> Hermes primary model
                                                  (e.g. ``moonshotai/kimi-k2.6``)
- ``config/settings.yaml::gauss.default_model`` -> sanity cross-check;
                                                    must equal ``hermes.model``.

The script then walks every current ``*.md`` in this standalone checkout
(excluding ``manuscript/`` which uses ``{{...}}`` placeholders rendered from
``manuscript_vars.yaml``, completed historical specs, and
``docs/_generated/`` which is build output) and flags any *literal* pin that
does not match the canonical value. For ``CHANGELOG.md``, only the current
``Unreleased`` section is audited; older release notes intentionally retain
the toolchain they actually used.

Patterns checked
----------------

- ``leanprover/lean4:v\\d+\\.\\d+\\.\\d+``  (compared to canonical Lean toolchain)
- ``Lean ?4? v\\d+\\.\\d+\\.\\d+``          (informal mentions in prose)
- ``Mathlib ?4? v\\d+\\.\\d+\\.\\d+``       (compared to canonical Mathlib tag)
- ``moonshotai/kimi-k2\\.\\d+``             (compared to canonical primary model)

Fallback-chain entries other than the primary (``z-ai/glm-5.1``,
``moonshotai/kimi-k2-thinking``, ``qwen/qwen3-next-80b-a3b-instruct:free``,
etc.) are intentional narrative content and are NOT flagged. Sentinel codepaths
inside fenced code blocks are still inspected because pins matter just as much
in shell snippets as in prose.

Exit codes
----------

- ``0`` -- no drift.
- ``1`` -- at least one drifted pin (CI-friendly).

Usage
-----

.. code-block:: bash

    uv run python pin_audit.py            # default
    uv run python pin_audit.py --verbose  # also print every confirming sighting
    uv run python pin_audit.py --json     # machine-readable summary
    uv run python pin_audit.py --check-latest  # networked latest-stable policy
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DOCS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DOCS_DIR.parent

EXCLUDED_DIRS = (
    PROJECT_ROOT / "manuscript",
    PROJECT_ROOT / "docs" / "_generated",
)

# Path *fragments* (matched anywhere in the resolved path) to skip. Covers
# Lake's ``.lake/packages/`` tree which mirrors third-party RELEASE notes that
# legitimately mention older Lean toolchain pins, plus build/cache dirs that
# could be created by Python tooling.
EXCLUDED_PATH_FRAGMENTS = (
    "/.lake/",
    "/__pycache__/",
    "/.pytest_cache/",
    "/output/",
    "/specs/done/",
)

_RE_LEAN_TOOLCHAIN = re.compile(r"leanprover/lean4:v(\d+\.\d+\.\d+)")
_RE_LEAN_PROSE = re.compile(r"\bLean(?:\s+4)?\s+v?(\d+\.\d+\.\d+)\b")
_RE_MATHLIB = re.compile(r"\bMathlib\s?4?\s+`?v(\d+\.\d+\.\d+)\b")
_RE_KIMI = re.compile(r"moonshotai/kimi-k2\.\d+")
_RE_LAKEFILE_MATHLIB = re.compile(r"mathlib4\.git\"\s*@\s*\"(v\d+\.\d+\.\d+)\"")
_RE_STABLE_RELEASE_TAG = re.compile(r"^v\d+\.\d+\.\d+$")

LEAN_RELEASES_API = "https://api.github.com/repos/leanprover/lean4/releases?per_page=20"
MATHLIB_TAG_API = (
    "https://api.github.com/repos/leanprover-community/mathlib4/git/ref/tags/{tag}"
)


@dataclass
class CanonicalPins:
    lean_toolchain: str
    lean_version: str
    mathlib_tag: str
    primary_model: str
    mathlib_revision: str
    sources: dict[str, str] = field(default_factory=dict)


@dataclass
class Drift:
    path: Path
    line: int
    found: str
    expected: str
    pin_kind: str

    def format(self, root: Path) -> str:
        rel = self.path.relative_to(root)
        return (
            f"{rel}:{self.line}: {self.pin_kind} drift -- "
            f"found {self.found!r}, expected {self.expected!r}"
        )


@dataclass(frozen=True)
class LatestStableAudit:
    """Result of checking local pins against the latest stable release pair."""

    latest_lean_tag: str
    latest_compatible_tag: str
    newer_lean_without_mathlib: tuple[str, ...]
    mathlib_tag_available: bool
    mathlib_revision: str
    errors: tuple[str, ...]

    @property
    def current(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "current": self.current,
            "latest_lean_tag": self.latest_lean_tag,
            "latest_compatible_tag": self.latest_compatible_tag,
            "newer_lean_without_mathlib": list(self.newer_lean_without_mathlib),
            "mathlib_tag_available": self.mathlib_tag_available,
            "mathlib_revision": self.mathlib_revision,
            "errors": list(self.errors),
        }


def _fetch_json(url: str) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "fep-lean-pin-audit",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token := os.environ.get("GITHUB_TOKEN", "").strip():
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def audit_latest_stable(
    pins: CanonicalPins,
    *,
    fetch_json: Callable[[str], Any] = _fetch_json,
) -> LatestStableAudit:
    """Require the newest stable Lean release that has a matching Mathlib tag."""
    errors: list[str] = []
    stable_tags: list[str] = []
    try:
        releases = fetch_json(LEAN_RELEASES_API)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return LatestStableAudit(
            "", "", (), False, "", (f"Lean release lookup failed: {exc}",)
        )
    if not isinstance(releases, list):
        errors.append("Lean releases response must be a list")
    else:
        for release in releases:
            if not isinstance(release, dict):
                continue
            candidate = release.get("tag_name")
            if (
                isinstance(candidate, str)
                and _RE_STABLE_RELEASE_TAG.fullmatch(candidate) is not None
                and release.get("draft") is False
                and release.get("prerelease") is False
            ):
                stable_tags.append(candidate)
    stable_tags = sorted(
        set(stable_tags),
        key=lambda tag: tuple(int(part) for part in tag.removeprefix("v").split(".")),
        reverse=True,
    )
    if not stable_tags:
        errors.append("Lean releases response has no stable vX.Y.Z tag")
        return LatestStableAudit("", "", (), False, "", tuple(errors))

    latest_tag = stable_tags[0]
    compatible_tag = ""
    mathlib_revision = ""
    unmatched_tags: list[str] = []
    for candidate in stable_tags:
        try:
            mathlib_ref = fetch_json(MATHLIB_TAG_API.format(tag=candidate))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                unmatched_tags.append(candidate)
                continue
            errors.append(f"Mathlib {candidate} tag lookup failed: {exc}")
            break
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"Mathlib {candidate} tag lookup failed: {exc}")
            break
        if isinstance(mathlib_ref, dict) and mathlib_ref.get("ref") == (
            f"refs/tags/{candidate}"
        ):
            object_payload = mathlib_ref.get("object")
            revision = (
                object_payload.get("sha") if isinstance(object_payload, dict) else None
            )
            if isinstance(revision, str) and re.fullmatch(r"[0-9a-f]{40}", revision):
                compatible_tag = candidate
                mathlib_revision = revision
                break
        unmatched_tags.append(candidate)

    if not compatible_tag:
        if not errors:
            errors.append("No recent stable Lean release has a validated Mathlib tag")
        return LatestStableAudit(
            latest_tag, "", tuple(unmatched_tags), False, "", tuple(errors)
        )

    expected_toolchain = f"leanprover/lean4:{compatible_tag}"
    if pins.lean_toolchain != expected_toolchain:
        errors.append(
            f"Lean pin {pins.lean_toolchain} is stale; newest stable pair is "
            f"{expected_toolchain}"
        )
    if pins.mathlib_tag != compatible_tag:
        errors.append(
            f"Mathlib pin {pins.mathlib_tag} does not match newest stable pair "
            f"{compatible_tag}"
        )
    if pins.mathlib_revision != mathlib_revision:
        errors.append(
            f"locked Mathlib revision {pins.mathlib_revision} does not match "
            f"{compatible_tag} revision {mathlib_revision}"
        )

    return LatestStableAudit(
        latest_tag,
        compatible_tag,
        tuple(unmatched_tags),
        True,
        mathlib_revision,
        tuple(errors),
    )


def _read_lean_toolchain(root: Path) -> str:
    pin = (root / "lean" / "lean-toolchain").read_text(encoding="utf-8").strip()
    if not _RE_LEAN_TOOLCHAIN.fullmatch(pin):
        raise SystemExit(f"lean/lean-toolchain has unexpected format: {pin!r}")
    return pin


def _read_mathlib_tag(root: Path) -> str:
    text = (root / "lean" / "lakefile.lean").read_text(encoding="utf-8")
    m = _RE_LAKEFILE_MATHLIB.search(text)
    if not m:
        raise SystemExit(
            'lean/lakefile.lean: could not find a `mathlib4.git "@" "vX.Y.Z"` pin'
        )
    return m.group(1)


def _read_mathlib_revision(root: Path, expected_tag: str) -> str:
    path = root / "lean" / "lake-manifest.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"lean/lake-manifest.json cannot be read: {exc}") from exc
    packages = payload.get("packages") if isinstance(payload, dict) else None
    if not isinstance(packages, list):
        raise SystemExit("lean/lake-manifest.json lacks a packages list")
    matches = [
        package
        for package in packages
        if isinstance(package, dict) and package.get("name") == "mathlib"
    ]
    if len(matches) != 1:
        raise SystemExit(
            "lean/lake-manifest.json must contain exactly one mathlib package"
        )
    package = matches[0]
    revision = package.get("rev")
    if not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise SystemExit("lean/lake-manifest.json has an invalid Mathlib revision")
    if package.get("inputRev") != expected_tag:
        raise SystemExit(
            "lean/lake-manifest.json Mathlib inputRev does not match lakefile.lean"
        )
    return revision


def _read_settings(root: Path) -> tuple[str, str]:
    """Return ``(hermes.model, gauss.default_model)`` from ``config/settings.yaml``.

    We parse a tiny subset of YAML by hand to avoid pulling pyyaml as a runtime
    dep for what is otherwise a small audit script. The two keys we care about
    are top-level ``hermes:`` -> ``model:`` and ``gauss:`` -> ``default_model:``.
    """
    text = (root / "config" / "settings.yaml").read_text(encoding="utf-8")
    hermes_model = None
    gauss_model = None
    section = None
    for raw in text.splitlines():
        if raw.startswith(("hermes:", "gauss:")):
            section = raw.split(":", 1)[0]
            continue
        if not raw.startswith((" ", "\t")) and raw.strip() and not raw.startswith("#"):
            section = None
            continue
        line = raw.split("#", 1)[0].rstrip()
        m = re.match(r"\s+(\w+)\s*:\s*\"?([^\"]+?)\"?\s*$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        if section == "hermes" and key == "model":
            hermes_model = value
        elif section == "gauss" and key == "default_model":
            gauss_model = value
    if hermes_model is None:
        raise SystemExit("config/settings.yaml: hermes.model not found")
    if gauss_model is None:
        raise SystemExit("config/settings.yaml: gauss.default_model not found")
    return hermes_model, gauss_model


def load_canonical(root: Path) -> CanonicalPins:
    lean_toolchain = _read_lean_toolchain(root)
    lean_version = _RE_LEAN_TOOLCHAIN.fullmatch(lean_toolchain).group(1)  # type: ignore[union-attr]
    mathlib_tag = _read_mathlib_tag(root)
    mathlib_revision = _read_mathlib_revision(root, mathlib_tag)
    hermes_model, gauss_model = _read_settings(root)
    if hermes_model != gauss_model:
        raise SystemExit(
            "config/settings.yaml: hermes.model "
            f"({hermes_model!r}) != gauss.default_model ({gauss_model!r}); "
            "fix the source of truth before running the audit."
        )
    if lean_version != mathlib_tag.lstrip("v"):
        # Not strictly an error -- Mathlib can be pinned to a different tag than
        # the toolchain -- but worth surfacing so the human notices.
        print(
            f"note: Lean toolchain ({lean_version}) and Mathlib tag "
            f"({mathlib_tag}) differ; both will be enforced separately."
        )
    return CanonicalPins(
        lean_toolchain=lean_toolchain,
        lean_version=lean_version,
        mathlib_tag=mathlib_tag,
        primary_model=hermes_model,
        mathlib_revision=mathlib_revision,
        sources={
            "lean_toolchain": "lean/lean-toolchain",
            "mathlib_tag": "lean/lakefile.lean",
            "mathlib_revision": "lean/lake-manifest.json",
            "primary_model": "config/settings.yaml::hermes.model",
        },
    )


def _scan_file(path: Path, pins: CanonicalPins) -> list[Drift]:
    drifts: list[Drift] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [Drift(path, 0, str(exc), "", "io")]
    changelog_unreleased = path.name != "CHANGELOG.md"
    changelog_heading_seen = False
    for i, line in enumerate(text.splitlines(), start=1):
        if path.name == "CHANGELOG.md" and line.startswith("## "):
            changelog_unreleased = not changelog_heading_seen and line.startswith(
                "## Unreleased"
            )
            changelog_heading_seen = True
        if not changelog_unreleased:
            continue
        for m in _RE_LEAN_TOOLCHAIN.finditer(line):
            found = m.group(0)
            if found != pins.lean_toolchain:
                drifts.append(
                    Drift(path, i, found, pins.lean_toolchain, "lean_toolchain")
                )
        for m in _RE_LEAN_PROSE.finditer(line):
            found_version = m.group(1)
            if found_version != pins.lean_version:
                drifts.append(
                    Drift(
                        path,
                        i,
                        m.group(0),
                        f"Lean {pins.lean_version}",
                        "lean_prose",
                    )
                )
        for m in _RE_MATHLIB.finditer(line):
            found_version = "v" + m.group(1)
            if found_version != pins.mathlib_tag:
                drifts.append(
                    Drift(
                        path,
                        i,
                        m.group(0),
                        f"Mathlib4 {pins.mathlib_tag}",
                        "mathlib_tag",
                    )
                )
        for m in _RE_KIMI.finditer(line):
            found = m.group(0)
            if found != pins.primary_model:
                drifts.append(
                    Drift(path, i, found, pins.primary_model, "primary_model")
                )
    return drifts


def _gather_files(root: Path) -> list[Path]:
    excluded = tuple(p.resolve() for p in EXCLUDED_DIRS)
    files: list[Path] = []
    for path in sorted(root.rglob("*.md")):
        rp = path.resolve()
        rp_str = str(rp)
        if any(rp_str.startswith(str(ex) + "/") or rp == ex for ex in excluded):
            continue
        if any(frag in rp_str for frag in EXCLUDED_PATH_FRAGMENTS):
            continue
        files.append(path)
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print every confirming pin sighting (not only drift).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON summary instead of human text.",
    )
    parser.add_argument(
        "--check-latest",
        action="store_true",
        help="Check the pins against GitHub's latest stable Lean and Mathlib tags.",
    )
    args = parser.parse_args(argv)

    pins = load_canonical(PROJECT_ROOT)
    files = _gather_files(PROJECT_ROOT)
    latest = audit_latest_stable(pins) if args.check_latest else None

    all_drifts: list[Drift] = []
    confirmed = 0
    for path in files:
        drifts = _scan_file(path, pins)
        if drifts:
            all_drifts.extend(drifts)
        if args.verbose:
            text = path.read_text(encoding="utf-8")
            for pattern in (_RE_LEAN_TOOLCHAIN, _RE_LEAN_PROSE, _RE_MATHLIB, _RE_KIMI):
                confirmed += sum(1 for _ in pattern.finditer(text))

    if args.json:
        out = {
            "canonical": {
                "lean_toolchain": pins.lean_toolchain,
                "lean_version": pins.lean_version,
                "mathlib_tag": pins.mathlib_tag,
                "mathlib_revision": pins.mathlib_revision,
                "primary_model": pins.primary_model,
                "sources": pins.sources,
            },
            "files_scanned": len(files),
            "drift_count": len(all_drifts),
            "latest_stable": latest.as_dict() if latest is not None else None,
            "drifts": [
                {
                    "path": str(d.path.relative_to(PROJECT_ROOT)),
                    "line": d.line,
                    "found": d.found,
                    "expected": d.expected,
                    "kind": d.pin_kind,
                }
                for d in all_drifts
            ],
        }
        json.dump(out, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 1 if all_drifts or (latest is not None and not latest.current) else 0

    print("Canonical pins:")
    print(
        f"  lean_toolchain : {pins.lean_toolchain}  (from {pins.sources['lean_toolchain']})"
    )
    print(
        f"  mathlib_tag    : {pins.mathlib_tag}  (from {pins.sources['mathlib_tag']})"
    )
    print(
        "  mathlib_rev    : "
        f"{pins.mathlib_revision}  (from {pins.sources['mathlib_revision']})"
    )
    print(
        f"  primary_model  : {pins.primary_model}  (from {pins.sources['primary_model']})"
    )
    print()

    if latest is not None:
        if latest.current:
            print(
                "Newest stable Lean/Mathlib pair: "
                f"{latest.latest_compatible_tag}; Mathlib revision "
                f"{latest.mathlib_revision}"
            )
            if latest.newer_lean_without_mathlib:
                print(
                    "Awaiting matching Mathlib tag(s): "
                    + ", ".join(latest.newer_lean_without_mathlib)
                )
            print()
        else:
            for error in latest.errors:
                print(f"latest-stable error: {error}")
            print()

    if all_drifts or (latest is not None and not latest.current):
        for d in all_drifts:
            print(d.format(PROJECT_ROOT))
        print()
        print(
            f"FAIL: {len(all_drifts)} local drift(s) across {len(files)} file(s); "
            f"latest-stable current={latest.current if latest is not None else 'not checked'}"
        )
        return 1

    if args.verbose:
        print(
            f"OK: {len(files)} file(s) scanned, {confirmed} pin sighting(s) — no drift."
        )
    else:
        print(f"OK: {len(files)} file(s) scanned — no drift.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
