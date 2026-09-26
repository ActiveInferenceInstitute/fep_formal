#!/usr/bin/env python3
"""Validate the source-bound H2.0 readiness decision matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path, PurePosixPath

import yaml

_SPEC_RELATIVE = Path("specs/done/horizon-2-smooth-stochastic")
_MATRIX_RELATIVE = _SPEC_RELATIVE / "readiness/matrix.yaml"
_EXPECTED_STATUS = "complete_with_boundaries"
_EXPECTED_COMMAND = (
    "uv run pytest -q tests/test_horizon2_readiness.py --no-cov "
    "--no-header --no-summary"
)
_PIN_EVIDENCE_RELATIVE = _SPEC_RELATIVE / "readiness/pin_evidence.json"
_EXPECTED_PIN_REPOSITORIES = {
    "https://github.com/leanprover/lean4": "lean_revision",
    "https://github.com/leanprover-community/mathlib4": "mathlib_revision",
}
_NO_GO_EDGE_SEMANTICS = (
    "row-to-slice readiness closures, not canonical scheduling DAG arcs"
)
_SEALED_DECISIONS = frozenset(
    {"go", "optional_no_go", "blocking_no_go", "upstream_required"}
)
_H2_FORMAL_RESOURCES = frozenset(
    {
        "gaussian_information_geometry.lean",
        "smooth_information_geometry.lean",
        "posterior_convergence.lean",
        "markov_semigroup.lean",
        "scalar_gaussian_semigroup.lean",
        "linear_gaussian_semigroup.lean",
        "fin4_gaussian_semigroup.lean",
        "gaussian_precision_conditioning.lean",
        "compositions/gaussian_filter.lean",
        "compositions/gaussian_control.lean",
        "compositions/gaussian_grid_path.lean",
        "compositions/smooth_reference_kernel.lean",
    }
)
_HEX_DIGEST_LENGTH = 64


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def canonical_rows_sha256(rows: object) -> str:
    """Return the stable scientific-contract digest for the ordered rows.

    Per-row acceptance pointers are excluded because they contain the receipt
    digest. The receipt independently binds this digest, and the validator
    requires every row to reference that one receipt, avoiding a hash cycle.
    """

    contract_rows: object
    if isinstance(rows, list):
        contract_rows = [
            {key: value for key, value in row.items() if key != "evidence"}
            if isinstance(row, Mapping)
            else row
            for row in rows
        ]
    else:
        contract_rows = rows

    encoded = json.dumps(
        contract_rows,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def _safe_project_file(project_root: Path, relative: object) -> Path | None:
    if not isinstance(relative, str):
        return None
    pure = PurePosixPath(relative)
    if (
        not relative
        or "\\" in relative
        or pure.is_absolute()
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        return None
    candidate = project_root.joinpath(*pure.parts)
    if candidate.is_symlink() or not candidate.is_file():
        return None
    try:
        candidate.resolve().relative_to(project_root.resolve())
    except ValueError:
        return None
    return candidate


def _load_mapping(path: Path) -> Mapping[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise TypeError(f"expected a mapping in {path}")
    return payload


def _pin_evidence_errors(
    project_root: Path,
    *,
    rows: Sequence[Mapping[str, object]],
    toolchain: object,
) -> tuple[str, ...]:
    """Validate the canonical upstream-tag receipt owned by ``pin_identity``."""

    errors: list[str] = []
    pin_rows = [row for row in rows if row.get("id") == "pin_identity"]
    expected_probe = {
        "kind": "metadata",
        "path": "readiness/pin_evidence.json",
        "anchor": "latest_stable",
    }
    if len(pin_rows) != 1 or pin_rows[0].get("probe") != expected_probe:
        errors.append("pin_identity must own the canonical latest-stable evidence")

    pin_path = _safe_project_file(project_root, _PIN_EVIDENCE_RELATIVE.as_posix())
    if pin_path is None:
        return (*errors, "pin evidence is missing or unsafe")
    try:
        pin_text = pin_path.read_text(encoding="utf-8")
        pin = json.loads(pin_text)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        return (*errors, f"pin evidence is not canonical JSON: {error}")
    if not isinstance(pin, Mapping):
        return (*errors, "pin evidence must be a JSON object")
    canonical_pin = (
        json.dumps(
            pin,
            ensure_ascii=True,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    if pin_text != canonical_pin:
        errors.append("pin evidence JSON is not canonical")
    if set(pin) != {
        "checked_at_utc",
        "conclusion",
        "repositories",
        "schema_version",
        "stable_pair",
    }:
        errors.append("pin evidence keys are noncanonical")
    if pin.get("schema_version") != 1:
        errors.append("pin evidence schema_version must be 1")
    checked_at = pin.get("checked_at_utc")
    if not isinstance(checked_at, str) or not checked_at.endswith("Z"):
        errors.append("pin evidence checked_at_utc must be a UTC timestamp")

    if not isinstance(toolchain, Mapping):
        errors.append("toolchain must be a mapping for pin validation")
        expected_tag = None
        expected_mathlib_revision = None
    else:
        lean_tag = toolchain.get("lean")
        mathlib_tag = toolchain.get("mathlib_tag")
        expected_tag = lean_tag if lean_tag == mathlib_tag else None
        expected_mathlib_revision = toolchain.get("mathlib_revision")
        if expected_tag is None:
            errors.append("Lean and Mathlib pin tags must match")

    stable_pair = pin.get("stable_pair")
    if not isinstance(stable_pair, Mapping):
        errors.append("pin evidence stable_pair must be a mapping")
        stable_pair = {}
    if set(stable_pair) != {"lean_revision", "mathlib_revision", "tag"}:
        errors.append("pin evidence stable_pair keys are noncanonical")
    if stable_pair.get("tag") != expected_tag:
        errors.append("pin evidence stable tag does not match the local toolchain")
    if stable_pair.get("mathlib_revision") != expected_mathlib_revision:
        errors.append(
            "pin evidence Mathlib revision does not match the local toolchain"
        )

    repositories = pin.get("repositories")
    if not isinstance(repositories, list) or not all(
        isinstance(repository, Mapping) for repository in repositories
    ):
        errors.append("pin evidence repositories must be a mapping list")
        return tuple(errors)
    if [repository.get("repository") for repository in repositories] != list(
        _EXPECTED_PIN_REPOSITORIES
    ):
        errors.append("pin evidence repository roster or order is noncanonical")
        return tuple(errors)
    for repository in repositories:
        repository_url = repository.get("repository")
        assert isinstance(repository_url, str)
        revision_key = _EXPECTED_PIN_REPOSITORIES[repository_url]
        refs = repository.get("refs")
        argv = repository.get("argv")
        if (
            not isinstance(refs, Mapping)
            or not isinstance(argv, list)
            or not all(isinstance(argument, str) for argument in argv)
        ):
            errors.append(f"pin evidence query is malformed: {repository_url}")
            continue
        tag = stable_pair.get("tag")
        stable_ref = f"refs/tags/{tag}"
        if refs.get(stable_ref) != stable_pair.get(revision_key):
            errors.append(f"pin evidence stable revision mismatch: {repository_url}")
        next_stable_ref = "refs/tags/v4.35.0"
        if next_stable_ref in refs or next_stable_ref not in argv:
            errors.append(
                f"pin evidence must query and exclude {next_stable_ref}: {repository_url}"
            )
    return tuple(errors)


def _default_formal_resources() -> tuple[str, ...]:
    from fep_lean.formal.manifest import FORMAL_MODULES

    return tuple(module.resource for module in FORMAL_MODULES)


def _receipt_errors(
    project_root: Path,
    evidence: object,
    *,
    expected_rows_sha256: str,
    expected_source_paths: frozenset[str],
    expected_search_results: Sequence[Mapping[str, object]],
) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(evidence, Mapping):
        return ("acceptance_evidence must be a mapping",)
    if set(evidence) != {"receipt_path", "receipt_sha256"}:
        errors.append(
            "acceptance_evidence must contain only receipt_path and receipt_sha256"
        )
        return tuple(errors)

    receipt_path = _safe_project_file(project_root, evidence.get("receipt_path"))
    if receipt_path is None:
        errors.append("acceptance receipt is missing or unsafe")
        return tuple(errors)
    expected_receipt_sha = evidence.get("receipt_sha256")
    actual_receipt_sha = _sha256_file(receipt_path)
    if expected_receipt_sha != actual_receipt_sha:
        errors.append(
            "acceptance receipt digest mismatch: "
            f"expected {expected_receipt_sha}, got {actual_receipt_sha}"
        )

    try:
        receipt_text = receipt_path.read_text(encoding="utf-8")
        receipt = json.loads(receipt_text)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        errors.append(f"acceptance receipt is not canonical JSON: {error}")
        return tuple(errors)
    if not isinstance(receipt, Mapping):
        errors.append("acceptance receipt must be a JSON object")
        return tuple(errors)
    canonical_receipt = (
        json.dumps(
            receipt,
            ensure_ascii=True,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    if receipt_text != canonical_receipt:
        errors.append("acceptance receipt JSON is not canonical")

    expected_keys = {
        "schema_version",
        "horizon",
        "command",
        "canonical_rows_sha256",
        "cwd",
        "exit_code",
        "formal_resources_at_capture",
        "tests",
        "warning_count",
        "warning_sha256",
        "output",
        "output_sha256",
        "source_sha256",
        "search_results",
    }
    if set(receipt) != expected_keys:
        errors.append("acceptance receipt keys are noncanonical")
    if receipt.get("schema_version") != 1:
        errors.append("acceptance receipt schema_version must be 1")
    if receipt.get("horizon") != "H2.0":
        errors.append("acceptance receipt horizon must be H2.0")
    if receipt.get("canonical_rows_sha256") != expected_rows_sha256:
        errors.append("acceptance receipt canonical row digest mismatch")
    if receipt.get("command") != _EXPECTED_COMMAND:
        errors.append("acceptance receipt command is noncanonical")
    if receipt.get("cwd") != ".":
        errors.append("acceptance receipt cwd must be '.'")
    if receipt.get("exit_code") != 0:
        errors.append("acceptance receipt exit_code must be 0")
    if receipt.get("formal_resources_at_capture") != []:
        errors.append("H2.0 acceptance must capture an empty H2 formal resource roster")

    tests = receipt.get("tests")
    if not isinstance(tests, Mapping):
        errors.append("acceptance receipt tests must be a mapping")
    else:
        collected = tests.get("collected")
        if (
            not isinstance(collected, int)
            or isinstance(collected, bool)
            or collected <= 0
            or tests.get("passed") != collected
            or tests.get("failed") != 0
            or tests.get("skipped") != 0
        ):
            errors.append("acceptance receipt test result is not an all-pass run")

    if receipt.get("warning_count") != 0:
        errors.append("acceptance receipt warning_count must be 0")
    if receipt.get("warning_sha256") != _sha256_bytes(b""):
        errors.append("acceptance receipt warning digest must bind empty output")
    output = receipt.get("output")
    if not isinstance(output, str):
        errors.append("acceptance receipt output must be text")
    elif receipt.get("output_sha256") != _sha256_bytes(output.encode("utf-8")):
        errors.append("acceptance receipt output digest mismatch")

    source_sha256 = receipt.get("source_sha256")
    if not isinstance(source_sha256, Mapping) or not source_sha256:
        errors.append("acceptance receipt source_sha256 must be a nonempty mapping")
    else:
        if set(source_sha256) != expected_source_paths:
            errors.append("acceptance receipt source roster is noncanonical")
        for relative, expected_sha in source_sha256.items():
            source_path = _safe_project_file(project_root, relative)
            if source_path is None:
                errors.append(f"acceptance source is missing or unsafe: {relative}")
            elif expected_sha != _sha256_file(source_path):
                errors.append(f"acceptance source digest mismatch: {relative}")

    search_results = receipt.get("search_results")
    if not isinstance(search_results, Sequence) or isinstance(
        search_results, (str, bytes)
    ):
        errors.append("acceptance receipt search_results must be a sequence")
    else:
        for search in search_results:
            if not isinstance(search, Mapping):
                errors.append("acceptance search result must be a mapping")
                continue
            if (
                search.get("status") != "optional_no_go"
                or search.get("result_count") != 0
            ):
                errors.append(
                    f"acceptance search is not a bounded no-go: {search.get('id')}"
                )
        if list(search_results) != list(expected_search_results):
            errors.append(
                "acceptance search results do not match the bounded search owner"
            )
    return tuple(errors)


def readiness_errors(
    project_root: Path,
    *,
    payload: Mapping[str, object] | None = None,
    formal_resources: Iterable[str] | None = None,
) -> tuple[str, ...]:
    """Return every static contract error for the H2.0 readiness matrix."""

    root = project_root.resolve()
    errors: list[str] = []
    if payload is None:
        matrix_path = _safe_project_file(root, _MATRIX_RELATIVE.as_posix())
        if matrix_path is None:
            return ("readiness matrix is missing or unsafe",)
        try:
            payload = _load_mapping(matrix_path)
        except (OSError, UnicodeDecodeError, TypeError, yaml.YAMLError) as error:
            return (f"readiness matrix is unreadable: {error}",)

    if payload.get("schema_version") != 1:
        errors.append("matrix schema_version must be 1")
    if payload.get("horizon") != "H2.0":
        errors.append("matrix horizon must be H2.0")
    if payload.get("status") != _EXPECTED_STATUS:
        errors.append(
            f"matrix status must be {_EXPECTED_STATUS}: {payload.get('status')}"
        )
    if payload.get("no_go_edge_semantics") != _NO_GO_EDGE_SEMANTICS:
        errors.append("matrix no-go edge semantics are noncanonical")

    row_order = payload.get("row_order")
    rows = payload.get("rows")
    if not isinstance(row_order, list) or not all(
        isinstance(row_id, str) for row_id in row_order
    ):
        errors.append("row_order must be a string list")
        row_order = []
    if not isinstance(rows, list) or not all(isinstance(row, Mapping) for row in rows):
        errors.append("rows must be a mapping list")
        rows = []
    row_ids = [row.get("id") for row in rows]
    if row_ids != row_order or len(set(row_ids)) != len(row_ids):
        errors.append("rows must exactly match the unique row_order")
    expected_rows_sha = canonical_rows_sha256(rows)

    errors.extend(
        _pin_evidence_errors(root, rows=rows, toolchain=payload.get("toolchain"))
    )

    probe_order = payload.get("probe_order")
    if not isinstance(probe_order, list) or not all(
        isinstance(probe, str) for probe in probe_order
    ):
        errors.append("probe_order must be a string list")
        probe_order = []
    toolchain = payload.get("toolchain")
    toolchain_sources: list[str] = []
    if isinstance(toolchain, Mapping) and isinstance(toolchain.get("sources"), Mapping):
        toolchain_sources = [
            source
            for source in toolchain["sources"].values()
            if isinstance(source, str)
        ]
    else:
        errors.append("toolchain sources must be a mapping")
    expected_source_paths = frozenset(
        {
            "tests/test_horizon2_readiness.py",
            (_SPEC_RELATIVE / "readiness/validate.py").as_posix(),
            *toolchain_sources,
            *((_SPEC_RELATIVE / probe).as_posix() for probe in probe_order),
        }
    )
    search_owner_path = _safe_project_file(
        root,
        (_SPEC_RELATIVE / "readiness/probes/11_unsupported_api_search.yaml").as_posix(),
    )
    expected_search_results: list[Mapping[str, object]] = []
    if search_owner_path is None:
        errors.append("bounded search owner is missing or unsafe")
    else:
        try:
            search_owner = _load_mapping(search_owner_path)
        except (OSError, UnicodeDecodeError, TypeError, yaml.YAMLError) as error:
            errors.append(f"bounded search owner is unreadable: {error}")
        else:
            searches = search_owner.get("searches")
            if not isinstance(searches, list) or not all(
                isinstance(search, Mapping) for search in searches
            ):
                errors.append("bounded search owner searches must be a mapping list")
            else:
                expected_search_results = [
                    {
                        "id": search.get("id"),
                        "result_count": search.get("result_count"),
                        "status": search.get("status"),
                    }
                    for search in searches
                ]

    evidence = payload.get("acceptance_evidence")
    errors.extend(
        _receipt_errors(
            root,
            evidence,
            expected_rows_sha256=expected_rows_sha,
            expected_source_paths=expected_source_paths,
            expected_search_results=expected_search_results,
        )
    )
    decision_values = payload.get("decision_values")
    if not isinstance(decision_values, list) or not all(
        isinstance(decision, str) for decision in decision_values
    ):
        errors.append("decision_values must be a string list")
        allowed_decisions: set[str] = set()
    else:
        allowed_decisions = set(decision_values)
    for row in rows:
        row_id = row.get("id")
        status = row.get("status")
        criticality = row.get("criticality")
        if status not in allowed_decisions or status not in _SEALED_DECISIONS:
            errors.append(f"row {row_id} status is not sealed: {status}")
        if criticality == "fatal" and status == "optional_no_go":
            errors.append(f"fatal row {row_id} cannot be optional_no_go")
        if criticality in {"optional", "exclusion"} and status in {
            "blocking_no_go",
            "upstream_required",
        }:
            errors.append(f"nonfatal row {row_id} cannot block H2")
        if row.get("evidence") != evidence:
            errors.append(f"row {row_id} does not bind canonical acceptance evidence")

        probe = row.get("probe")
        if not isinstance(probe, Mapping):
            errors.append(f"row {row_id} probe must be a mapping")
        else:
            probe_path = probe.get("path")
            if probe_path is not None:
                spec_relative = (_SPEC_RELATIVE / str(probe_path)).as_posix()
                resolved_probe = _safe_project_file(root, spec_relative)
                if resolved_probe is None:
                    errors.append(f"readiness probe is missing or unsafe: {probe_path}")
                elif probe.get("kind") == "lean":
                    marker_kind = {
                        "go": "ROW",
                        "optional_no_go": "OPTIONAL",
                        "blocking_no_go": "BLOCKING",
                        "upstream_required": "UPSTREAM",
                    }.get(status)
                    marker = f"-- H2-READINESS-{marker_kind}: {row_id}"
                    if marker not in resolved_probe.read_text(encoding="utf-8"):
                        errors.append(
                            f"row {row_id} is missing its {marker_kind} probe marker"
                        )

        used = row.get("used_declarations")
        if not isinstance(used, list):
            errors.append(f"row {row_id} used_declarations must be a list")
        elif status == "go" and not used and row_id != "pin_identity":
            errors.append(f"go row {row_id} must name used declarations")
        if status == "go" and row.get("missing_obligation") is not None:
            errors.append(f"go row {row_id} must have no missing obligation")
        if status != "go" and not row.get("missing_obligation"):
            errors.append(f"no-go row {row_id} must name its missing obligation")
        if status != "go" and not row.get("no_go_action"):
            errors.append(f"no-go row {row_id} must name its action")

    if payload.get("canonical_rows_sha256") != expected_rows_sha:
        errors.append(
            "canonical row digest mismatch: "
            f"expected {payload.get('canonical_rows_sha256')}, got {expected_rows_sha}"
        )

    if payload.get("status") != _EXPECTED_STATUS:
        resources = tuple(
            _default_formal_resources()
            if formal_resources is None
            else formal_resources
        )
        premature = sorted(_H2_FORMAL_RESOURCES.intersection(resources))
        if premature:
            errors.append(
                "maintained H2 formal resources must remain absent during H2.0: "
                + ", ".join(premature)
            )
    return tuple(errors)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate and exit")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[4],
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.check:
        _parser().error("--check is required")
    errors = readiness_errors(args.project_root)
    if errors:
        for error in errors:
            print(f"H2.0 readiness error: {error}")
        return 1
    print("H2.0 readiness matrix: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
