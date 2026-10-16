"""Latest-stable Lean/Mathlib policy checks."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _audit_module():
    spec = importlib.util.spec_from_file_location(
        "pin_audit_latest", PROJECT_ROOT / "docs" / "pin_audit.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_pin_audit_keeps_history_journals_out_of_current_guidance(
    tmp_path: Path,
) -> None:
    audit = _audit_module()
    names = (
        "specs/comprehensive-science-improvement/evidence/retained/REPORT.md",
        "specs/comprehensive-science-improvement/NEXT.md",
        "docs/evidence/README.md",
    )
    paths = [tmp_path / name for name in names]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Historical Lean v4.33.1; current instructions use this pin.\n")
    pins = audit.CanonicalPins(
        lean_toolchain="leanprover/lean4:v4.34.1",
        lean_version="4.34.1",
        mathlib_tag="v4.34.1",
        primary_model="fixture/model",
        mathlib_revision="d" * 40,
    )

    current = audit._gather_files(tmp_path)

    assert set(current) == set(paths[1:])
    assert all(audit._scan_file(path, pins) for path in current)


def test_latest_release_audit_accepts_matching_stable_pair() -> None:
    audit = _audit_module()
    pins = audit.CanonicalPins(
        lean_toolchain="leanprover/lean4:v4.33.1",
        lean_version="4.33.1",
        mathlib_tag="v4.33.1",
        primary_model="fixture/model",
        mathlib_revision="d" * 40,
    )
    requested: list[str] = []

    def fetch_json(url: str):
        requested.append(url)
        if url == audit.LEAN_RELEASES_API:
            return [
                {
                    "tag_name": "v4.33.1",
                    "draft": False,
                    "prerelease": False,
                }
            ]
        return {"ref": "refs/tags/v4.33.1", "object": {"sha": "d" * 40}}

    result = audit.audit_latest_stable(pins, fetch_json=fetch_json)

    assert result.current
    assert result.latest_lean_tag == "v4.33.1"
    assert result.latest_compatible_tag == "v4.33.1"
    assert result.newer_lean_without_mathlib == ()
    assert result.mathlib_tag_available
    assert result.errors == ()
    assert requested == [
        audit.LEAN_RELEASES_API,
        audit.MATHLIB_TAG_API.format(tag="v4.33.1"),
    ]


def test_latest_release_audit_rejects_stale_local_pins() -> None:
    audit = _audit_module()
    pins = audit.CanonicalPins(
        lean_toolchain="leanprover/lean4:v4.32.2",
        lean_version="4.32.2",
        mathlib_tag="v4.32.2",
        primary_model="fixture/model",
        mathlib_revision="d" * 40,
    )

    def fetch_json(url: str):
        if url == audit.LEAN_RELEASES_API:
            return [
                {
                    "tag_name": "v4.33.1",
                    "draft": False,
                    "prerelease": False,
                }
            ]
        return {"ref": "refs/tags/v4.33.1", "object": {"sha": "d" * 40}}

    result = audit.audit_latest_stable(pins, fetch_json=fetch_json)

    assert not result.current
    assert any("Lean pin" in error and "stale" in error for error in result.errors)
    assert any("Mathlib pin" in error for error in result.errors)


def test_latest_release_audit_rejects_a_stale_locked_mathlib_revision() -> None:
    audit = _audit_module()
    pins = audit.CanonicalPins(
        lean_toolchain="leanprover/lean4:v4.33.1",
        lean_version="4.33.1",
        mathlib_tag="v4.33.1",
        primary_model="fixture/model",
        mathlib_revision="c" * 40,
    )

    def fetch_json(url: str):
        if url == audit.LEAN_RELEASES_API:
            return [
                {
                    "tag_name": "v4.33.1",
                    "draft": False,
                    "prerelease": False,
                }
            ]
        return {"ref": "refs/tags/v4.33.1", "object": {"sha": "d" * 40}}

    result = audit.audit_latest_stable(pins, fetch_json=fetch_json)

    assert not result.current
    assert "locked Mathlib revision " + "c" * 40 in "\n".join(result.errors)


def test_latest_release_audit_rejects_prerelease_or_missing_mathlib_tag() -> None:
    audit = _audit_module()
    pins = audit.CanonicalPins(
        lean_toolchain="leanprover/lean4:v4.33.1",
        lean_version="4.33.1",
        mathlib_tag="v4.33.1",
        primary_model="fixture/model",
        mathlib_revision="d" * 40,
    )

    prerelease = audit.audit_latest_stable(
        pins,
        fetch_json=lambda _url: [
            {
                "tag_name": "v4.34.0",
                "draft": False,
                "prerelease": True,
            }
        ],
    )
    assert not prerelease.current
    assert any("no stable" in error for error in prerelease.errors)

    def missing_mathlib(url: str):
        if url == audit.LEAN_RELEASES_API:
            return [
                {
                    "tag_name": "v4.33.1",
                    "draft": False,
                    "prerelease": False,
                }
            ]
        return {"message": "Not Found"}

    missing = audit.audit_latest_stable(pins, fetch_json=missing_mathlib)
    assert not missing.current
    assert any("No recent stable Lean release" in error for error in missing.errors)


def test_latest_release_audit_waits_for_matching_mathlib_release() -> None:
    audit = _audit_module()
    pins = audit.CanonicalPins(
        lean_toolchain="leanprover/lean4:v4.33.0",
        lean_version="4.33.0",
        mathlib_tag="v4.33.0",
        primary_model="fixture/model",
        mathlib_revision="d" * 40,
    )

    def fetch_json(url: str):
        if url == audit.LEAN_RELEASES_API:
            return [
                {
                    "tag_name": "v4.33.0",
                    "draft": False,
                    "prerelease": False,
                },
                {
                    "tag_name": "v4.33.1",
                    "draft": False,
                    "prerelease": False,
                },
            ]
        if url == audit.MATHLIB_TAG_API.format(tag="v4.33.1"):
            return {"message": "Not Found"}
        return {"ref": "refs/tags/v4.33.0", "object": {"sha": "d" * 40}}

    result = audit.audit_latest_stable(pins, fetch_json=fetch_json)

    assert result.current
    assert result.latest_lean_tag == "v4.33.1"
    assert result.latest_compatible_tag == "v4.33.0"
    assert result.newer_lean_without_mathlib == ("v4.33.1",)
    assert result.mathlib_revision == "d" * 40


def test_local_audit_catches_plain_lean_version_but_preserves_changelog_history(
    tmp_path: Path,
) -> None:
    audit = _audit_module()
    pins = audit.CanonicalPins(
        lean_toolchain="leanprover/lean4:v4.33.1",
        lean_version="4.33.1",
        mathlib_tag="v4.33.1",
        primary_model="fixture/model",
        mathlib_revision="d" * 40,
    )
    current = tmp_path / "README.md"
    current.write_text("Pinned Lean 4.32.0.\n", encoding="utf-8")
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "## Unreleased\n\nLean 4.33.1.\n\n## 1.0.0\n\nHistorical Lean 4.29.0.\n",
        encoding="utf-8",
    )

    drift = audit._scan_file(current, pins)

    assert [(item.pin_kind, item.found) for item in drift] == [
        ("lean_prose", "Lean 4.32.0")
    ]
    assert audit._scan_file(changelog, pins) == []


@pytest.mark.parametrize(
    "pin",
    (
        "leanprover/lean4:v4.34.0-rc1",
        "leanprover/lean4:nightly-2026-08-21",
        "leanprover/lean4:master",
        "leanprover/lean4:stable",
    ),
)
def test_local_toolchain_owner_rejects_nonstable_or_floating_pins(
    tmp_path: Path,
    pin: str,
) -> None:
    audit = _audit_module()
    lean_dir = tmp_path / "lean"
    lean_dir.mkdir()
    (lean_dir / "lean-toolchain").write_text(pin + "\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="unexpected format"):
        audit._read_lean_toolchain(tmp_path)


@pytest.mark.parametrize(
    "mathlib_ref",
    ("v4.34.0-rc1", "master", "nightly-2026-08-21"),
)
def test_local_mathlib_owner_rejects_nonstable_or_floating_refs(
    tmp_path: Path,
    mathlib_ref: str,
) -> None:
    audit = _audit_module()
    lean_dir = tmp_path / "lean"
    lean_dir.mkdir()
    (lean_dir / "lakefile.lean").write_text(
        "require mathlib from git\n"
        '  "https://github.com/leanprover-community/mathlib4.git" '
        f'@ "{mathlib_ref}"\n',
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="could not find"):
        audit._read_mathlib_tag(tmp_path)


def test_local_mathlib_revision_owner_is_bound_to_the_pinned_tag(
    tmp_path: Path,
) -> None:
    audit = _audit_module()
    lean_dir = tmp_path / "lean"
    lean_dir.mkdir()
    manifest = lean_dir / "lake-manifest.json"
    manifest.write_text(
        '{"packages":[{"name":"mathlib","inputRev":"v4.33.1",'
        '"rev":"' + "d" * 40 + '"}]}\n',
        encoding="utf-8",
    )

    assert audit._read_mathlib_revision(tmp_path, "v4.33.1") == "d" * 40

    with pytest.raises(SystemExit, match="inputRev does not match"):
        audit._read_mathlib_revision(tmp_path, "v4.33.0")


def test_fetch_json_retries_a_truncated_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import http.client

    audit = _audit_module()
    outcomes: list[object] = [
        http.client.IncompleteRead(b"partial"),
        contextlib.nullcontext(io.BytesIO(b'{"ok": true}')),
    ]

    def fake_urlopen(*_args: object, **_kwargs: object) -> object:
        outcome = outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    monkeypatch.setattr(audit.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(audit.time, "sleep", lambda _seconds: None)
    assert audit._fetch_json("https://example.invalid") == {"ok": True}
    assert outcomes == []


def test_fetch_json_exhausted_transient_failure_is_a_readable_oserror(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import http.client

    audit = _audit_module()
    calls = 0

    def fake_urlopen(*_args: object, **_kwargs: object) -> object:
        nonlocal calls
        calls += 1
        raise http.client.IncompleteRead(b"partial")

    monkeypatch.setattr(audit.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(audit.time, "sleep", lambda _seconds: None)
    with pytest.raises(OSError, match="IncompleteRead"):
        audit._fetch_json("https://example.invalid")
    assert calls == audit._FETCH_ATTEMPTS


def test_fetch_json_does_not_retry_a_not_found_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import urllib.error

    audit = _audit_module()
    calls = 0

    def fake_urlopen(*_args: object, **_kwargs: object) -> object:
        nonlocal calls
        calls += 1
        raise urllib.error.HTTPError(
            "https://example.invalid", 404, "Not Found", None, None
        )

    monkeypatch.setattr(audit.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(audit.time, "sleep", lambda _seconds: None)
    with pytest.raises(urllib.error.HTTPError):
        audit._fetch_json("https://example.invalid")
    assert calls == 1


@pytest.mark.parametrize("status", [404, 503])
def test_fetch_json_closes_error_responses_before_retry_or_reraise(
    monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    import urllib.error

    audit = _audit_module()
    bodies: list[io.BytesIO] = []

    def fail(*_args: object, **_kwargs: object) -> object:
        body = io.BytesIO(b"error body")
        bodies.append(body)
        raise urllib.error.HTTPError(
            "https://example.invalid", status, "error", None, body
        )

    def sleep(_seconds: float) -> None:
        assert all(body.closed for body in bodies)

    monkeypatch.setattr(audit.urllib.request, "urlopen", fail)
    monkeypatch.setattr(audit.time, "sleep", sleep)
    with pytest.raises(urllib.error.HTTPError) as failure:
        audit._fetch_json("https://example.invalid")
    assert failure.value.code == status
    assert len(bodies) == (1 if status == 404 else audit._FETCH_ATTEMPTS)
    assert all(body.closed for body in bodies)
