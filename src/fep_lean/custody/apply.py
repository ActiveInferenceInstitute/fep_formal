"""Apply the dependency-ordered H2.7 custody refresh onto an explicit output tree.

The settled 14-phase order is authoritative (skill: ``fep-lean-custody-refresh``):
pin_evidence re-collection, acceptance.json re-bind, matrix receipt_sha256
(strictly after the re-bind, never before), 07 prior re-issue, h2_r0_custody
PRIOR_SHA256, 07 successor + probe maps, 05d/05b/06a re-issues, lifecycle
repair_sha256, precision-test constants, PREDECESSORS patch, reviews, diagnostics
regen, terminal packet, and the H3 spike PINNED_SOURCES/spike-receipt.json
lockstep last.

Write discipline:

- The gate runs :func:`fep_lean.custody.census.census` over ``specs_dir``/
  ``repo_root`` and refuses via :class:`ApplyRefused` unless
  :func:`fep_lean.custody.verify.verify` returns all-clear.
- Staged specs writes buffer in memory and flush into the explicit output
  directory only after every phase completes; a refusal leaves the output
  directory untouched. The live specs tree is never a write target.
- Repo-side phases (h2_r0_custody PRIOR_SHA256, precision-test constants, the
  PREDECESSORS constant) are byte-pinned/re-seal territory: this machinery
  computes count-validated byte-replacement directives against the live bytes
  and never writes those files; the coordinator applies them at the fold tip.
- Every JSON re-issue serializes ``sort_keys=True`` except
  ``05d-gaussian-conditioning-lifecycle.json`` and ``diagnostics.json``, which
  keep insertion order.
- Every byte-level replacement goes through :func:`byte_replace`, which aborts
  with :class:`ApplyRefused` unless the anchor occurs exactly once.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Collection, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from fep_lean.custody.census import census as census_from_tree
from fep_lean.custody.model import Census
from fep_lean.custody.verify import Expectations, gate_expectations
from fep_lean.custody.verify import verify as verify_gate
from fep_lean.verification._jsonutil import load_strict_json
from fep_lean.verification.horizon_acceptance import (
    CURRENT_FILES,
    diagnostic_record,
    native_source_paths,
)

BASE = "specs/horizon-2-smooth-stochastic/readiness/"
ACCEPTANCE = BASE + "acceptance.json"
MATRIX = BASE + "matrix.yaml"
PIN_EVIDENCE = BASE + "pin_evidence.json"
TERMINAL_PACKET = BASE + "terminal-acceptance.json"
PRIOR_07 = BASE + "repairs/07-gaussian-vfe-natural-gradient.json"
SUCCESSOR_07 = BASE + "repairs/07-gaussian-vfe-natural-gradient-custody.json"
LIFECYCLE_05D = BASE + "repairs/05d-gaussian-conditioning-lifecycle.json"
REPAIR_05D = BASE + "repairs/05d-gaussian-conditioning.json"
REPAIR_05B = BASE + "repairs/05b-transition-covariance.json"
REPAIR_06A = BASE + "repairs/06a-native-filter-posterior.json"
DIAGNOSTICS = BASE + "evidence/20260904-wave2/diagnostics.json"
SPIKE_RECEIPT = "specs/h3-case-study/spike-receipt.json"
SPIKE_MODULE = "specs/h3-case-study/h3_reference_study_spike.py"
H2_R0_CUSTODY = "tests/_support/h2_r0_custody.py"
PRECISION_TEST = "tests/test_horizon2_gaussian_precision_conditioning.py"
HORIZON_ACCEPTANCE_MODULE = "src/fep_lean/verification/horizon_acceptance.py"
MANIFEST_PATH = "src/fep_lean/formal/manifest.py"

_INSERTION_ORDER_FILES = frozenset(
    {"05d-gaussian-conditioning-lifecycle.json", "diagnostics.json"}
)


class ApplyRefused(RuntimeError):
    """A gate or fail-closed check refused the refresh; nothing has been written."""


def byte_replace(data: bytes, old: bytes, new: bytes) -> bytes:
    """Replace the single occurrence of ``old``; refuse otherwise.

    Every byte-level custody replacement goes through this helper: an anchor
    that appears zero or several times is an uninterpretable edit, so the
    caller aborts with :class:`ApplyRefused` and nothing is written.
    """
    count = data.count(old)
    if count != 1:
        preview = old[:16].decode("utf-8", errors="replace")
        raise ApplyRefused(f"byte_replace anchor count {count} != 1 ({preview!r}...)")
    return data.replace(old, new, 1)


def dump_json_bytes(payload: Mapping[str, Any], *, relative: str) -> bytes:
    """Serialize a custody JSON with the file's settled discipline.

    ``sort_keys=True`` everywhere except the two insertion-order surfaces
    (``05d-gaussian-conditioning-lifecycle.json`` and ``diagnostics.json``).
    """
    text = json.dumps(
        payload, indent=2, sort_keys=_sort_keys_for(relative), allow_nan=False
    )
    return (text + "\n").encode("utf-8")


def _sort_keys_for(relative: str) -> bool:
    return Path(relative).name not in _INSERTION_ORDER_FILES


@dataclass(frozen=True)
class PatchDirective:
    """A count-validated byte replacement for a repo-side surface.

    The apply machinery never writes repo-side custody files (the pinned
    ``h2_r0_custody`` support module, precision-test constants, and the
    ``PREDECESSORS`` constant); it computes the exact replacement and the
    coordinator applies it at the fold tip.
    """

    path: str
    anchor: bytes
    replacement: bytes
    phase: str


@dataclass(frozen=True)
class ApplyReport:
    """Outcome of one :func:`apply_refresh` walk."""

    phases: tuple[str, ...]
    mutations: tuple[str, ...]
    directives: tuple[PatchDirective, ...]
    output_dir: str
    files_written: int


class _StagedView:
    """Read-through byte view over the staged specs tree and the live repo.

    Reads resolve ``specs/`` surfaces from ``specs_dir`` (the staged copy) and
    everything else from ``repo_root`` (read-only). Writes buffer in memory;
    :meth:`flush` lands them into the output directory only after success.
    """

    def __init__(self, specs_dir: Path, repo_root: Path) -> None:
        self.specs_dir = specs_dir
        self.repo_root = repo_root
        self._modified: dict[str, bytes] = {}
        self._digests: dict[str, str] = {}
        self.issued: set[str] = set()

    def _resolve(self, relative: str) -> Path:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise ApplyRefused(f"path escapes project: {relative}")
        if relative.startswith("specs/"):
            target = self.specs_dir / relative[len("specs/") :]
        else:
            target = self.repo_root / relative
        if not target.is_file():
            raise ApplyRefused(f"missing staged/source file: {relative}")
        return target

    def read(self, relative: str) -> bytes:
        buffered = self._modified.get(relative)
        if buffered is not None:
            return buffered
        return self._resolve(relative).read_bytes()

    def digest(self, relative: str) -> str:
        cached = self._digests.get(relative)
        if cached is None:
            cached = hashlib.sha256(self.read(relative)).hexdigest()
            self._digests[relative] = cached
        return cached

    def put(self, relative: str, data: bytes) -> bool:
        if data == self.read(relative):
            return False
        self._modified[relative] = data
        self.issued.add(relative)
        self._digests[relative] = hashlib.sha256(data).hexdigest()
        return True

    def flush(self, output_dir: Path) -> int:
        """Write the full staged tree (source bytes plus buffered re-issues)."""
        written = 0
        for source in sorted(self.specs_dir.rglob("*")):
            relative = source.relative_to(self.specs_dir).as_posix()
            target = output_dir / relative
            if source.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if source.is_symlink():
                raise ApplyRefused(f"refusing symlinked specs file: {relative}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(self.read("specs/" + relative))
            written += 1
        return written


@dataclass
class _PhaseContext:
    """Per-walk state threaded through the ordered phases."""

    view: _StagedView
    authorized: frozenset[str]
    directives: list[PatchDirective] = field(default_factory=list)


def _load_json(view: _StagedView, relative: str, label: str) -> dict[str, Any]:
    data = load_strict_json(view.read(relative))
    if not isinstance(data, dict):
        raise ApplyRefused(f"{label}: JSON root must be an object")
    return data


def _read_digest_map(record: Mapping[str, Any], key: str, label: str) -> dict[str, str]:
    value = record.get(key)
    if not isinstance(value, dict):
        raise ApplyRefused(f"{label}: {key} map missing")
    result: dict[str, str] = {}
    for path, digest in value.items():
        if not isinstance(path, str) or not isinstance(digest, str):
            raise ApplyRefused(f"{label}: malformed {key} entry")
        result[path] = digest
    return result


def _write_json(view: _StagedView, relative: str, payload: Mapping[str, Any]) -> bool:
    return view.put(relative, dump_json_bytes(payload, relative=relative))


def _reissue_source_map(
    view: _StagedView,
    relative: str,
    *,
    authorized: frozenset[str],
    label: str,
    exempt: Iterable[str] = (),
) -> bool:
    """Re-bind a record's source_sha256 wholesale against the staged view.

    Exempt entries (the 07 prior's authorized permanent drift) are never
    recomputed; every other entry drift must sit inside the authorized
    forced-change set or surfaces this chore already re-issued.
    """
    record = _load_json(view, relative, label)
    recorded = _read_digest_map(record, "source_sha256", label)
    exempt_set = frozenset(exempt)
    unknown = exempt_set - recorded.keys()
    if unknown:
        raise ApplyRefused(f"{label}: exempt entries not present: {sorted(unknown)}")
    live_keys = {
        path: digest for path, digest in recorded.items() if path not in exempt_set
    }
    recomputed = {path: view.digest(path) for path in live_keys}
    changed = {path for path, digest in recomputed.items() if recorded[path] != digest}
    unexpected = changed - authorized - view.issued
    if unexpected:
        raise ApplyRefused(f"{label}: unexplained source drift: {sorted(unexpected)}")
    if not changed:
        return False
    record["source_sha256"] = {**recorded, **recomputed}
    return _write_json(view, relative, record)


def _emit_directive(
    ctx: _PhaseContext, path: str, old: str, new: str, phase: str
) -> None:
    """Validate a repo-side replacement against live bytes, then record it."""
    live = (ctx.view.repo_root / path).read_bytes()
    anchor = old.encode("ascii")
    replacement = new.encode("ascii")
    byte_replace(live, anchor, replacement)
    ctx.directives.append(
        PatchDirective(path=path, anchor=anchor, replacement=replacement, phase=phase)
    )


# ---------------------------------------------------------------------------
# The settled 14 phases. Order is authoritative: the matrix step strictly
# follows the acceptance.json re-bind; the H3 lockstep runs last.
# ---------------------------------------------------------------------------


def _phase_pin_evidence_recollection(ctx: _PhaseContext) -> None:
    """Validate the re-collected pin evidence against the local pin owners.

    Network re-collection (git ls-remote) belongs to the chore; this phase
    fail-closed-checks the re-collected artifact so downstream re-binds never
    pin an inconsistent pair.
    """
    record = _load_json(ctx.view, PIN_EVIDENCE, "pin_evidence")
    stable = record.get("stable_pair")
    if not isinstance(stable, dict) or not isinstance(stable.get("tag"), str):
        raise ApplyRefused("pin_evidence: stable_pair.tag missing")
    repositories = record.get("repositories")
    if not isinstance(repositories, list) or not repositories:
        raise ApplyRefused("pin_evidence: repositories roster missing")
    toolchain = ctx.view.read("lean/lean-toolchain").decode("utf-8").strip()
    tag = toolchain.rsplit(":", 1)[-1]
    if stable["tag"] != tag:
        raise ApplyRefused(
            f"pin_evidence: stable_pair tag {stable['tag']!r} != toolchain {tag!r}"
        )
    matrix = yaml.safe_load(ctx.view.read(MATRIX).decode("utf-8"))
    if not isinstance(matrix, dict):
        raise ApplyRefused("matrix: unparseable YAML")
    toolchain_block = matrix.get("toolchain")
    if not isinstance(toolchain_block, dict):
        raise ApplyRefused("matrix: toolchain block missing")
    expected = {
        "lean": tag,
        "mathlib_tag": stable["tag"],
        "mathlib_revision": stable.get("mathlib_revision"),
    }
    for key, value in expected.items():
        if toolchain_block.get(key) != value:
            raise ApplyRefused(
                f"pin_evidence: matrix toolchain {key} mismatch "
                f"({toolchain_block.get(key)!r} != {value!r})"
            )


def _phase_acceptance_rebind(ctx: _PhaseContext) -> None:
    _reissue_source_map(
        ctx.view, ACCEPTANCE, authorized=ctx.authorized, label="acceptance.json"
    )


def _phase_matrix_receipt_sha256(ctx: _PhaseContext) -> None:
    """Re-pin matrix.yaml's acceptance receipt digest (strictly post re-bind)."""
    data = ctx.view.read(MATRIX)
    pattern = re.compile(rb"\n  receipt_sha256: ([0-9a-f]{64})\n")
    matches = pattern.findall(data)
    if len(matches) != 1:
        raise ApplyRefused(f"matrix: receipt_sha256 anchor count {len(matches)} != 1")
    recorded = matches[0].decode("ascii")
    new_digest = ctx.view.digest(ACCEPTANCE)
    if recorded == new_digest:
        return
    data = byte_replace(
        data,
        f"\n  receipt_sha256: {recorded}\n".encode("ascii"),
        f"\n  receipt_sha256: {new_digest}\n".encode("ascii"),
    )
    ctx.view.put(MATRIX, data)


def _phase_prior_07_reissue(ctx: _PhaseContext) -> None:
    custody = _load_json(ctx.view, SUCCESSOR_07, "07 custody receipt")
    allowed = custody.get("allowed_prior_source_changes")
    if not isinstance(allowed, list) or not all(
        isinstance(item, str) for item in allowed
    ):
        raise ApplyRefused("07 custody receipt: allowed_prior_source_changes missing")
    _reissue_source_map(
        ctx.view,
        PRIOR_07,
        authorized=ctx.authorized,
        label="07 prior receipt",
        exempt=allowed,
    )


def _phase_h2_r0_custody_prior_sha256(ctx: _PhaseContext) -> None:
    """Directive phase: PRIOR_SHA256 must follow the re-issued prior receipt."""
    new_digest = ctx.view.digest(PRIOR_07)
    live = (ctx.view.repo_root / H2_R0_CUSTODY).read_bytes()
    pattern = re.compile(rb'PRIOR_SHA256 = "([0-9a-f]{64})"')
    matches = pattern.findall(live)
    if len(matches) != 1:
        raise ApplyRefused(
            f"h2_r0_custody: PRIOR_SHA256 anchor count {len(matches)} != 1"
        )
    recorded = matches[0].decode("ascii")
    if recorded == new_digest:
        return
    _emit_directive(
        ctx,
        H2_R0_CUSTODY,
        f'PRIOR_SHA256 = "{recorded}"',
        f'PRIOR_SHA256 = "{new_digest}"',
        "h2_r0_custody_prior_sha256",
    )


def _phase_successor_07_reissue(ctx: _PhaseContext) -> None:
    """Re-bind the successor custody map; its probe maps follow exactly."""
    record = _load_json(ctx.view, SUCCESSOR_07, "07 successor receipt")
    recorded = _read_digest_map(record, "source_sha256", "07 successor receipt")
    recomputed = {path: ctx.view.digest(path) for path in recorded}
    changed = {path for path, digest in recomputed.items() if recorded[path] != digest}
    unexpected = changed - ctx.authorized - ctx.view.issued
    if unexpected:
        raise ApplyRefused(
            f"07 successor receipt: unexplained source drift: {sorted(unexpected)}"
        )
    native = record.get("native_evidence")
    if not isinstance(native, dict):
        raise ApplyRefused("07 successor receipt: native_evidence missing")
    probes = native.get("probes")
    if not isinstance(probes, list) or not probes:
        raise ApplyRefused("07 successor receipt: native_evidence.probes missing")
    for probe in probes:
        if not isinstance(probe, dict) or probe.get("source_sha256") != recorded:
            raise ApplyRefused(
                "07 successor receipt: probe map differs from successor map"
            )
    transition = record.get("manifest_transition")
    if not isinstance(transition, dict) or not isinstance(
        transition.get("current_sha256"), str
    ):
        raise ApplyRefused("07 successor receipt: manifest_transition missing")
    prior_ref = record.get("prior")
    if not isinstance(prior_ref, dict) or not isinstance(prior_ref.get("sha256"), str):
        raise ApplyRefused("07 successor receipt: prior reference missing")
    current_manifest = ctx.view.digest(MANIFEST_PATH)
    if transition["current_sha256"] != recorded[MANIFEST_PATH]:
        raise ApplyRefused(
            "07 successor receipt: manifest_transition inconsistent with its map"
        )
    prior_digest = ctx.view.digest(PRIOR_07)
    prior_drift = prior_ref["sha256"] != prior_digest
    if prior_drift and PRIOR_07 not in ctx.view.issued:
        raise ApplyRefused(
            "07 successor receipt: prior reference drift without an issued re-issue"
        )
    if not changed and not prior_drift:
        return
    if changed:
        record["source_sha256"] = recomputed
        for probe in probes:
            probe["source_sha256"] = dict(recomputed)
        transition["current_sha256"] = current_manifest
    if prior_drift:
        prior_ref["sha256"] = prior_digest
    _write_json(ctx.view, SUCCESSOR_07, record)


def _phase_record_reissues(ctx: _PhaseContext) -> None:
    for relative in (REPAIR_05D, REPAIR_05B, REPAIR_06A):
        _reissue_source_map(
            ctx.view, relative, authorized=ctx.authorized, label=relative
        )


def _phase_lifecycle_repair_sha256(ctx: _PhaseContext) -> None:
    record = _load_json(ctx.view, LIFECYCLE_05D, "05d lifecycle receipt")
    corrected = record.get("corrected_artifact")
    if not isinstance(corrected, dict) or not isinstance(
        corrected.get("repair_sha256"), str
    ):
        raise ApplyRefused(
            "05d lifecycle receipt: corrected_artifact.repair_sha256 missing"
        )
    new_digest = ctx.view.digest(REPAIR_05D)
    if corrected["repair_sha256"] == new_digest:
        return
    if REPAIR_05D not in ctx.view.issued and REPAIR_05D not in ctx.authorized:
        raise ApplyRefused(
            "05d lifecycle receipt: repair_sha256 drift without an issued re-issue"
        )
    corrected["repair_sha256"] = new_digest
    _write_json(ctx.view, LIFECYCLE_05D, record)


def _phase_precision_test_constants(ctx: _PhaseContext) -> None:
    """Directive phase: precision-test digest constants follow the re-issues."""
    live = (ctx.view.repo_root / PRECISION_TEST).read_bytes()
    constants: tuple[tuple[str, str], ...] = (
        ("R0_REPAIR_SHA256", REPAIR_05D),
        ("R0_LIFECYCLE_SHA256", LIFECYCLE_05D),
    )
    for constant, relative in constants:
        pattern = re.compile((constant + r' = "([0-9a-f]{64})"').encode("ascii"))
        matches = pattern.findall(live)
        if len(matches) != 1:
            raise ApplyRefused(
                f"precision test: {constant} anchor count {len(matches)} != 1"
            )
        recorded = matches[0].decode("ascii")
        new_digest = ctx.view.digest(relative)
        if recorded == new_digest:
            continue
        _emit_directive(
            ctx,
            PRECISION_TEST,
            f'{constant} = "{recorded}"',
            f'{constant} = "{new_digest}"',
            "precision_test_constants",
        )


def _phase_predecessors_patch(ctx: _PhaseContext) -> None:
    """Directive phase: the PREDECESSORS constant follows the re-issued chain."""
    from fep_lean.verification import horizon_acceptance

    for relative, old_digest in sorted(horizon_acceptance.PREDECESSORS.items()):
        new_digest = ctx.view.digest(relative)
        if old_digest == new_digest:
            continue
        _emit_directive(
            ctx,
            HORIZON_ACCEPTANCE_MODULE,
            f'"{old_digest}"',
            f'"{new_digest}"',
            "predecessors_patch",
        )


def _phase_reviews_reissue(ctx: _PhaseContext) -> None:
    """Re-bind the three packet-referenced reviews to the native|current union."""
    packet = _load_json(ctx.view, TERMINAL_PACKET, "terminal packet")
    reviews = packet.get("reviews")
    if not isinstance(reviews, list) or not reviews:
        raise ApplyRefused("terminal packet: reviews roster missing")
    union = sorted(set(CURRENT_FILES) | set(native_source_paths(ctx.view.repo_root)))
    for entry in reviews:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ApplyRefused("terminal packet: malformed review ref")
        record = _load_json(ctx.view, entry["path"], entry["path"])
        recorded = _read_digest_map(record, "source_sha256", entry["path"])
        if set(recorded) != set(union):
            raise ApplyRefused(f"review: source roster drift: {entry['path']}")
        recomputed = {path: ctx.view.digest(path) for path in union}
        changed = {path for path in union if recorded[path] != recomputed[path]}
        unexpected = changed - ctx.authorized - ctx.view.issued
        if unexpected:
            raise ApplyRefused(
                f"review: unexplained source drift in {entry['path']}: {sorted(unexpected)}"
            )
        if not changed:
            continue
        record["source_sha256"] = recomputed
        _write_json(ctx.view, entry["path"], record)


def _phase_diagnostics_regen(ctx: _PhaseContext) -> None:
    """Regenerate diagnostics.json wholesale from the live tree (insertion order)."""
    record = diagnostic_record(ctx.view.repo_root)
    serialized = dump_json_bytes(record, relative=DIAGNOSTICS)
    staged = ctx.view.read(DIAGNOSTICS)
    if serialized == staged:
        return
    staged_record = _load_json(ctx.view, DIAGNOSTICS, "diagnostics")
    old_map = _read_digest_map(staged_record, "source_before", "diagnostics")
    new_map = _read_digest_map(record, "source_before", "diagnostics")
    if set(old_map) != set(new_map):
        raise ApplyRefused("diagnostics: source roster drift")
    drift = {path for path in new_map if old_map.get(path) != new_map[path]}
    unexpected = drift - ctx.authorized
    if unexpected:
        raise ApplyRefused(
            f"diagnostics: unexplained source drift: {sorted(unexpected)}"
        )
    if not drift:
        raise ApplyRefused("diagnostics: byte drift without source drift")
    ctx.view.put(DIAGNOSTICS, serialized)


def _pin_artifact_ref(
    ctx: _PhaseContext, ref: Any, label: str, changed: list[str]
) -> None:
    if not isinstance(ref, dict) or not isinstance(ref.get("path"), str):
        raise ApplyRefused(f"terminal packet: malformed {label} ref")
    new_digest = ctx.view.digest(ref["path"])
    if ref.get("sha256") == new_digest:
        return
    if ref["path"] not in ctx.view.issued and ref["path"] not in ctx.authorized:
        raise ApplyRefused(
            f"terminal packet: {label} drift outside this chore: {ref['path']}"
        )
    ref["sha256"] = new_digest
    changed.append(label)


def _phase_terminal_packet_reissue(ctx: _PhaseContext) -> None:
    """Re-pin the packet's refs and predecessor digests (native maps untouched)."""
    record = _load_json(ctx.view, TERMINAL_PACKET, "terminal packet")
    native = record.get("native_evidence")
    if not isinstance(native, dict):
        raise ApplyRefused("terminal packet: native_evidence missing")
    frozen: list[Any] = [native.get("collection"), native.get("junit")]
    supplement = native.get("heavy_probe_supplement")
    if isinstance(supplement, dict) and supplement.get("junit") is not None:
        frozen.append(supplement["junit"])
    for ref in frozen:
        if not isinstance(ref, dict) or not isinstance(ref.get("path"), str):
            raise ApplyRefused("terminal packet: malformed frozen artifact ref")
        if (
            not isinstance(ref.get("sha256"), str)
            or ctx.view.digest(ref["path"]) != ref["sha256"]
        ):
            raise ApplyRefused(
                f"terminal packet: frozen evidence drifted: {ref.get('path')}"
            )
    sources = _read_digest_map(record, "current_sources", "terminal packet")
    if set(sources) != set(CURRENT_FILES):
        raise ApplyRefused("terminal packet: current_sources roster drift")
    recomputed_sources = {path: ctx.view.digest(path) for path in sources}
    sources_changed = {
        path for path, digest in recomputed_sources.items() if sources[path] != digest
    }
    unexpected = sources_changed - ctx.authorized - ctx.view.issued
    if unexpected:
        raise ApplyRefused(
            f"terminal packet: unexplained current_sources drift: {sorted(unexpected)}"
        )
    changed: list[str] = []
    if sources_changed:
        record["current_sources"] = recomputed_sources
        changed.append("current_sources")
    predecessors = _read_digest_map(record, "predecessors", "terminal packet")
    for path in sorted(predecessors):
        new_digest = ctx.view.digest(path)
        if new_digest == predecessors[path]:
            continue
        if path not in ctx.view.issued and path not in ctx.authorized:
            raise ApplyRefused(
                f"terminal packet: predecessor drift outside this chore: {path}"
            )
        predecessors[path] = new_digest
        changed.append(f"predecessors:{path}")
    record["predecessors"] = predecessors
    _pin_artifact_ref(ctx, record.get("diagnostics"), "diagnostics", changed)
    reviews = record.get("reviews")
    if not isinstance(reviews, list):
        raise ApplyRefused("terminal packet: reviews roster missing")
    for ref in reviews:
        _pin_artifact_ref(ctx, ref, "review", changed)
    if changed:
        _write_json(ctx.view, TERMINAL_PACKET, record)


_PINNED_SOURCES_BLOCK = re.compile(
    r"PINNED_SOURCES: dict\[str, str\] = \{(?P<body>.*?)\n\}", re.DOTALL
)
_PINNED_ENTRY = re.compile(r'"(?P<path>[^"]+)": \(\s*"(?P<digest>[0-9a-f]{64})"\s*\),')


def _phase_h3_lockstep(ctx: _PhaseContext) -> None:
    """Lockstep-last: spike-receipt.json digests and the PINNED_SOURCES literal."""
    receipt = _load_json(ctx.view, SPIKE_RECEIPT, "spike receipt")
    digests = _read_digest_map(receipt, "digests", "spike receipt")
    recomputed = {path: ctx.view.digest(path) for path in digests}
    changed = {path for path in digests if digests[path] != recomputed[path]}
    unexpected = changed - ctx.authorized - ctx.view.issued
    if unexpected:
        raise ApplyRefused(
            f"spike receipt: unexplained digest drift: {sorted(unexpected)}"
        )
    if changed:
        receipt["digests"] = recomputed
        _write_json(ctx.view, SPIKE_RECEIPT, receipt)
    data = ctx.view.read(SPIKE_MODULE)
    text = data.decode("utf-8")
    match = _PINNED_SOURCES_BLOCK.search(text)
    if match is None:
        raise ApplyRefused("spike module: PINNED_SOURCES block missing")
    entries = {
        entry["path"]: entry["digest"]
        for entry in _PINNED_ENTRY.finditer(match["body"])
    }
    if set(entries) != set(recomputed):
        raise ApplyRefused("spike module: PINNED_SOURCES roster drift")
    for path in sorted(entries):
        old_digest = entries[path]
        new_digest = recomputed[path]
        if old_digest == new_digest:
            continue
        data = byte_replace(
            data, old_digest.encode("ascii"), new_digest.encode("ascii")
        )
    pinned = _PINNED_SOURCES_BLOCK.search(data.decode("utf-8"))
    if pinned is None:
        raise ApplyRefused("spike module: PINNED_SOURCES block missing after edit")
    updated = {
        entry["path"]: entry["digest"]
        for entry in _PINNED_ENTRY.finditer(pinned["body"])
    }
    if updated != recomputed:
        raise ApplyRefused("spike module: PINNED_SOURCES lockstep broke")
    ctx.view.put(SPIKE_MODULE, data)


_PHASES: tuple[tuple[str, Callable[[_PhaseContext], None]], ...] = (
    ("pin_evidence_recollection", _phase_pin_evidence_recollection),
    ("acceptance_rebind", _phase_acceptance_rebind),
    ("matrix_receipt_sha256", _phase_matrix_receipt_sha256),
    ("prior_07_reissue", _phase_prior_07_reissue),
    ("h2_r0_custody_prior_sha256", _phase_h2_r0_custody_prior_sha256),
    ("successor_07_reissue", _phase_successor_07_reissue),
    ("record_reissues", _phase_record_reissues),
    ("lifecycle_repair_sha256", _phase_lifecycle_repair_sha256),
    ("precision_test_constants", _phase_precision_test_constants),
    ("predecessors_patch", _phase_predecessors_patch),
    ("reviews_reissue", _phase_reviews_reissue),
    ("diagnostics_regen", _phase_diagnostics_regen),
    ("terminal_packet_reissue", _phase_terminal_packet_reissue),
    ("h3_lockstep", _phase_h3_lockstep),
)

#: The settled dependency-ordered procedure; the matrix step strictly follows
#: the acceptance.json re-bind and the H3 lockstep runs last.
PHASE_ORDER: tuple[str, ...] = tuple(name for name, _phase in _PHASES)


def apply_refresh(
    specs_dir: Path,
    repo_root: Path,
    output_dir: Path,
    expectations: Expectations | None = None,
    *,
    census: Census | None = None,
    authorized_changes: Collection[str] = (),
) -> ApplyReport:
    """Gate, then walk the settled 14-phase order onto ``output_dir``.

    ``census`` injects a precomputed census and ``expectations`` the declared
    gate state (the evidence-fixture pattern); otherwise the pure census over
    ``specs_dir``/``repo_root`` classifies the tree and the module's
    ``GATE_EXPECTATIONS`` guard it. The verify gate must return all-clear
    before anything runs, and the buffered staged writes flush into
    ``output_dir`` only after every phase completes — a refusal leaves the
    output directory untouched and the live specs tree unmodified.
    """
    if not specs_dir.is_dir():
        raise ValueError(f"specs dir not found: {specs_dir}")
    if not repo_root.is_dir():
        raise ValueError(f"repo root not found: {repo_root}")
    if output_dir.resolve() == specs_dir.resolve():
        raise ValueError("output dir must be a staging copy, not the live specs tree")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"output dir not empty: {output_dir}")
    resolved_census = (
        census if census is not None else census_from_tree(specs_dir, repo_root)
    )
    gate = expectations if expectations is not None else gate_expectations()
    ok, reasons = verify_gate(resolved_census, gate)
    if not ok:
        raise ApplyRefused("custody verify gate refused: " + "; ".join(reasons))
    view = _StagedView(specs_dir, repo_root)
    ctx = _PhaseContext(view=view, authorized=frozenset(authorized_changes))
    effects: list[str] = []
    for name, phase in _PHASES:
        before = (len(view.issued), len(ctx.directives))
        phase(ctx)
        after = (len(view.issued), len(ctx.directives))
        if after != before:
            effects.append(name)
    files_written = view.flush(output_dir)
    return ApplyReport(
        phases=tuple(effects),
        mutations=tuple(sorted(view.issued)),
        directives=tuple(ctx.directives),
        output_dir=str(output_dir),
        files_written=files_written,
    )
