"""Execute exactly the frozen H3 synthetic study, after native/export review gates."""

from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import math
import os
import platform
import re
import stat
import sys
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction
from itertools import pairwise
from pathlib import Path, PurePosixPath
from typing import Any, Protocol, cast

import numpy as np
import yaml

from fep_formal.output.provenance import config_owner_paths, source_owner_paths
from fep_formal.verification._jsonutil import load_strict_json
from fep_formal.verification._toolchain import (
    lean_version_matches_pin,
    read_toolchain_pin,
    resolved_mathlib_revision,
)
from fep_formal.verification.formalism_audit import validate_formalism_audit_receipt

PROTOCOL_SHA256 = "50b3575316fb272dc7bf209f50a21330fc5ea0764da9399e20aedeb0b2302c93"
FREEZE_SHA256 = "dadbbf4a5f06d5b143dd87c6fb9f7eaca6f9db69b1351e32cad842ab1c8556d5"
BASE = "specs/h3-reference-study/"
STUDY_SOURCE_FILES = (BASE + "run_synthetic.py", BASE + "export_native.py")
NATIVE_EXPORT_FOUNDATION = "src/fep_formal/formal/h3_reference_model.lean"
NATIVE_EXPORT_STAGE_NAMES = (
    "compiler-version",
    "mathlib-head",
    "native-build",
    "native-export",
    "mathlib-head-final",
    "compiler-version-final",
)
NATIVE_EXPORT_ARTIFACT_FILES = frozenset(
    {"H3NativeExport.lean"}
    | {
        name + "." + stream
        for name in NATIVE_EXPORT_STAGE_NAMES
        for stream in ("stdout", "stderr")
    }
)
AXES = ("external", "sensory", "active", "internal")
PARAMETER_WITNESSES = frozenset(
    "FEP.H3ReferenceModel." + name
    for name in (
        "precisionRat_eq_native",
        "covarianceRat_eq_native",
        "scaleRat_eq_native",
        "offsetRat_eq_native",
        "scalarRateRat_eq_native",
        "diffusionVarianceRateRat_eq_native",
        "recognitionRat_eq_precision",
        "settingRat_eq_native",
        "modeRat_eq_native",
        "modeRateRat_eigenpair",
        "modeVector_nonzero",
        "modeVector_gram",
    )
)
PROOF_ROLES = frozenset(
    {
        "arbitrary_state_projection",
        "native_posterior",
        "vfe_optimum",
        "blanket",
        "recognition",
        "clamp_normalization",
        "clamp_conditional_covariance",
        "finite_likelihood_conjugacy",
        "consistency_mse",
        "consistency_tail",
        "consistency_limit",
        "scalar_mean_identifiability",
        "hidden_mode_nonidentifiability",
        "policy_attainment",
        "policy_containment",
        "efe_native_information",
        "efe_risk_alignment",
        "preference_counterexample",
        "controlled_moment_bound",
        "restricted_class_counterexample",
        "nonstationary_native_grid",
        "finite_grid_kl",
        "singular_grid_infinite_kl",
        "constitutive_nonidentification",
    }
)


class StudyRejection(ValueError):
    """A positively identified study input or acceptance failure."""


class AttemptFiles:
    """Non-following descriptor ownership of an exclusive attempt directory."""

    def __init__(self, directory: Path, *, create: bool = False):
        require(
            directory.is_absolute() and bool(directory.name),
            "absolute non-root attempt directory required",
        )
        self.directory = directory
        self.fd = os.open(directory.anchor, os.O_RDONLY | os.O_DIRECTORY)
        try:
            for part in directory.parts[1:-1]:
                child = os.open(
                    part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=self.fd
                )
                os.close(self.fd)
                self.fd = child
            if create:
                os.mkdir(directory.name, mode=0o700, dir_fd=self.fd)
            child = os.open(
                directory.name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=self.fd,
            )
            os.close(self.fd)
            self.fd = child
            self.identity = os.fstat(self.fd)
        except BaseException:
            os.close(self.fd)
            raise

    def close(self) -> None:
        os.close(self.fd)

    def write_new(self, name: str, data: bytes) -> None:
        require(
            Path(name).name == name and name not in ("", ".", ".."),
            "unsafe output filename",
        )
        fd = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=self.fd,
        )
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())

    def receipt(self, data: bytes) -> None:
        self.write_new(".acceptance.pending", data)
        os.rename(
            ".acceptance.pending",
            "acceptance.json",
            src_dir_fd=self.fd,
            dst_dir_fd=self.fd,
        )
        os.fsync(self.fd)

    def inventory(
        self, *, strict: bool = True
    ) -> tuple[dict[str, str], list[dict[str, str]]]:
        hashes: dict[str, str] = {}
        issues: list[dict[str, str]] = []
        try:
            lexical = self.directory.lstat()
            if not stat.S_ISDIR(lexical.st_mode) or (
                lexical.st_dev,
                lexical.st_ino,
            ) != (self.identity.st_dev, self.identity.st_ino):
                issues.append({"path": ".", "reason": "attempt directory redirected"})
        except OSError:
            issues.append({"path": ".", "reason": "attempt directory path unavailable"})
        members = sorted(os.listdir(self.fd))
        for name in members:
            try:
                value = os.stat(name, dir_fd=self.fd, follow_symlinks=False)
                if not stat.S_ISREG(value.st_mode):
                    issues.append(
                        {
                            "path": name,
                            "reason": "nonregular artifact; target never read",
                        }
                    )
                    continue
                if strict and not name.endswith(".npy"):
                    issues.append(
                        {"path": name, "reason": "undeclared output extension"}
                    )
                require(value.st_size <= 128 * 1024 * 1024, "oversized output artifact")
                fd = os.open(
                    name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self.fd
                )
                with os.fdopen(fd, "rb") as stream:
                    before = os.fstat(stream.fileno())
                    require(stat.S_ISREG(before.st_mode), "opened output is nonregular")
                    data = stream.read(128 * 1024 * 1024 + 1)
                    after = os.fstat(stream.fileno())
                require(
                    (
                        value.st_dev,
                        value.st_ino,
                        value.st_size,
                        value.st_mtime_ns,
                        value.st_ctime_ns,
                    )
                    == (
                        before.st_dev,
                        before.st_ino,
                        before.st_size,
                        before.st_mtime_ns,
                        before.st_ctime_ns,
                    )
                    == (
                        after.st_dev,
                        after.st_ino,
                        after.st_size,
                        after.st_mtime_ns,
                        after.st_ctime_ns,
                    )
                    and len(data) == before.st_size,
                    "output changed while hashing",
                )
                hashes[name] = hashlib.sha256(data).hexdigest()
            except (OSError, StudyRejection) as exc:
                issues.append({"path": name, "reason": str(exc)})
        if members != sorted(os.listdir(self.fd)):
            issues.append(
                {"path": ".", "reason": "output membership changed while hashing"}
            )
        return hashes, issues


def require(condition: bool, message: str) -> None:
    if not condition:
        raise StudyRejection(message)


def finite(values: Any, label: str) -> np.ndarray:
    try:
        array = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise StudyRejection(f"invalid numeric array: {label}") from exc
    require(bool(np.all(np.isfinite(array))), f"nonfinite {label}")
    return array


def json_primitives(value: Any) -> Any:
    """Retain exact NumPy scalar values using ordinary JSON primitive types."""
    if isinstance(value, np.generic):
        return json_primitives(value.item())
    if type(value) is dict:
        return {key: json_primitives(child) for key, child in value.items()}
    if type(value) is list:
        return [json_primitives(child) for child in value]
    return value


def fraction(value: Any) -> float:
    if type(value) is dict:
        require(set(value) == {"numerator", "denominator"}, "rational object fields")
        require(
            type(value["numerator"]) is int
            and type(value["denominator"]) is int
            and value["denominator"] > 0,
            "invalid rational numerator/denominator",
        )
        return float(Fraction(value["numerator"], value["denominator"]))
    require(type(value) in (str, int), "rational parameter must be a string or int")
    return float(Fraction(value))


@dataclass(frozen=True)
class InputState:
    bytes: bytes
    mtime_ns: int
    sha256: str
    identity: tuple[int, int, int, int]


class Inputs:
    """Containment-safe retained buffers and exact source-race checks."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.states: dict[str, InputState] = {}

    def read(self, name: str, *, expected: str | None = None) -> bytes:
        path = PurePosixPath(name)
        require(
            bool(name)
            and "\\" not in name
            and not path.is_absolute()
            and not any(p in (".", "..") for p in path.parts),
            "unsafe input path",
        )
        lexical = self.root / name
        require(
            not lexical.is_symlink()
            and not any(
                p.is_symlink()
                for p in lexical.parents
                if p != self.root and p.is_relative_to(self.root)
            ),
            "symlink input",
        )
        require(lexical.resolve().is_relative_to(self.root), "input escapes project")
        require(lexical.is_file(), f"missing input: {name}")
        require(lexical.stat().st_size <= 128 * 1024 * 1024, "oversized input")
        # Resolve each directory using descriptors, so a concurrent symlink swap
        # cannot redirect scientific input reads outside the declared project.
        directory_fd = os.open(self.root.anchor, os.O_RDONLY | os.O_DIRECTORY)
        file_fd = None
        try:
            for part in self.root.parts[1:]:
                child_fd = os.open(
                    part,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory_fd,
                )
                os.close(directory_fd)
                directory_fd = child_fd
            for part in path.parts[:-1]:
                child_fd = os.open(
                    part,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory_fd,
                )
                os.close(directory_fd)
                directory_fd = child_fd
            file_fd = os.open(
                path.name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=directory_fd,
            )
            before = os.fstat(file_fd)
            require(
                stat.S_ISREG(before.st_mode) and before.st_size <= 128 * 1024 * 1024,
                "nonregular/oversized input",
            )
            with os.fdopen(file_fd, "rb") as stream:
                file_fd = None
                data = stream.read(128 * 1024 * 1024 + 1)
                after = os.fstat(stream.fileno())

            def identity(value: os.stat_result) -> tuple[int, ...]:
                return (
                    value.st_dev,
                    value.st_ino,
                    value.st_mode,
                    value.st_size,
                    value.st_mtime_ns,
                    value.st_ctime_ns,
                )

            require(
                identity(before) == identity(after) and len(data) == before.st_size,
                "input changed while reading",
            )
        finally:
            if file_fd is not None:
                os.close(file_fd)
            os.close(directory_fd)
        state = InputState(
            data,
            before.st_mtime_ns,
            hashlib.sha256(data).hexdigest(),
            (before.st_dev, before.st_ino, before.st_size, before.st_ctime_ns),
        )
        require(
            name not in self.states or self.states[name] == state,
            "input changed during read",
        )
        require(expected is None or state.sha256 == expected, f"stale input: {name}")
        self.states[name] = state
        return state.bytes

    def json(self, name: str, *, expected: str | None = None) -> dict[str, Any]:
        raw = load_strict_json(self.read(name, expected=expected).decode())
        require(type(raw) is dict, "input must be a JSON object")
        return cast(dict[str, Any], raw)

    def stable(self) -> None:
        for name, before in tuple(self.states.items()):
            self.read(name, expected=before.sha256)

    def hashes(self) -> dict[str, str]:
        return {name: state.sha256 for name, state in sorted(self.states.items())}


def frozen_protocol(inputs: Inputs) -> dict[str, Any]:
    raw = inputs.read(BASE + "preregistration.yaml", expected=PROTOCOL_SHA256)
    protocol = yaml.safe_load(raw)
    require(type(protocol) is dict, "protocol mapping required")
    freeze = inputs.json(BASE + "freeze.json", expected=FREEZE_SHA256)
    require(freeze.get("decision") == "accepted_pre_outcome_protocol", "freeze absent")
    require(freeze.get("new_outcomes_accessed") is False, "freeze was not pre-outcome")
    require(
        freeze.get("new_model_implementation_started") is False,
        "freeze followed implementation",
    )
    require(
        freeze.get("protocol")
        == {"path": BASE + "preregistration.yaml", "sha256": PROTOCOL_SHA256},
        "freeze protocol mismatch",
    )
    require(
        protocol["branch"] == "continuous"
        and protocol["finite_branch_selected"] is False,
        "exactly one continuous branch required",
    )
    require(protocol["execution_authorized"] is True, "execution not authorized")
    identities = set()
    for ref in freeze["reviews"].values():
        review = inputs.json(ref["path"], expected=ref["sha256"])
        require(
            review.get("decision") == "approve"
            and review.get("protocol_sha256") == PROTOCOL_SHA256,
            "protocol review mismatch",
        )
        identities.add(review["reviewer_id"])
    require(len(identities) == 2, "two independent protocol reviewers required")
    g0 = inputs.json(freeze["g0"]["path"], expected=freeze["g0"]["sha256"])
    require(
        g0["terminal_acceptance_sha256"] == freeze["h2_terminal_at_freeze_sha256"],
        "H2/G0 epoch mismatch",
    )
    for name, digest in freeze["carrier_sources"].items():
        inputs.read(name, expected=digest)
    epoch = protocol["source_epoch_at_freeze"]
    old_map = inputs.json(
        epoch["h2_review_source_map_path"],
        expected=epoch["h2_review_source_map_sha256"],
    )
    require(g0["source_sha256"] == old_map, "G0 historical source epoch mismatch")
    require(
        protocol["empirical_gate"]["status"] == "no_go_no_licensed_named_dataset",
        "empirical scope changed",
    )
    return cast(dict[str, Any], protocol)


def native_probe(source: str) -> str:
    """The sole permitted export probe is canonical text plus exact commands."""
    return (
        source
        + '\n#eval IO.println ("H3_PARAMETERS=" ++ FEP.H3ReferenceModel.parameterExport.compress)\n'
        + "\n".join(f"#print axioms {name}" for name in sorted(PARAMETER_WITNESSES))
        + "\n"
    )


def parse_native_output(stdout: str, stderr: str, returncode: int) -> dict[str, Any]:
    """Read one native value and exactly its requested equality axiom records."""
    require(type(returncode) is int and returncode == 0, "native compiler failed")
    require(
        not re.search(
            r"\b(?:warning|error):|\bsorryAx\b", stdout + "\n" + stderr, re.IGNORECASE
        ),
        "native compiler warned or reported an error/placeholder",
    )
    values = [
        line.removeprefix("H3_PARAMETERS=")
        for line in stdout.splitlines()
        if line.startswith("H3_PARAMETERS=")
    ]
    require(len(values) == 1, "exactly one native parameter value required")
    value = load_strict_json(values[0])
    require(type(value) is dict, "native value must be an object")
    require(
        type(value.get("witnesses")) is list
        and len(value["witnesses"]) == len(PARAMETER_WITNESSES)
        and set(value["witnesses"]) == PARAMETER_WITNESSES,
        "native equality witness roster changed",
    )
    records: dict[str, set[str]] = {}
    for name, axioms in re.findall(
        r"'([^']+)' depends on axioms: \[([^\]]*)\]", stdout
    ):
        require(name not in records, "duplicate native axiom record")
        records[name] = {part.strip() for part in axioms.split(",") if part.strip()}
    for name in re.findall(r"'([^']+)' does not depend on any axioms", stdout):
        require(name not in records, "duplicate native axiom record")
        records[name] = set()
    require(
        set(records) == PARAMETER_WITNESSES, "incomplete native equality axiom evidence"
    )
    require(
        all(
            axioms <= {"propext", "Classical.choice", "Quot.sound"}
            for axioms in records.values()
        ),
        "unsupported native equality axiom",
    )
    return cast(dict[str, Any], value)


def replay_native_attempt(
    inputs: Inputs, export_name: str, export: dict[str, Any], acceptance: dict[str, Any]
) -> None:
    """Validate retained execution content; artifact hashes alone do not do this."""
    parent = PurePosixPath(export_name).parent

    captured_root = export.get("captured_project_root")
    require(
        type(captured_root) is str
        and captured_root.startswith("/")
        and "\\" not in captured_root
        and "\x00" not in captured_root
        and all(part not in ("", ".", "..") for part in captured_root.split("/")[1:])
        and acceptance.get("captured_project_root") == captured_root,
        "native captured project root is absent, unsafe or changed",
    )
    recorded_root = Path(cast(str, captured_root))

    def text(name: str) -> str:
        return inputs.states[(parent / name).as_posix()].bytes.decode()

    require(
        text("H3NativeExport.lean")
        == native_probe(inputs.states[NATIVE_EXPORT_FOUNDATION].bytes.decode()),
        "retained native probe differs from canonical source/commands",
    )
    stages = acceptance.get("stages")
    require(
        type(stages) is list and len(stages) == len(NATIVE_EXPORT_STAGE_NAMES),
        "native stage roster",
    )
    stages = cast(list[dict[str, Any]], stages)
    require(all(type(item) is dict for item in stages), "native stage must be object")
    command = stages[0].get("command")
    require(
        type(command) is list
        and len(command) == 4
        and type(command[0]) is str
        and bool(command[0]),
        "compiler executable record",
    )
    command = cast(list[str], command)
    lake = command[0]
    mathlib = [
        "git",
        "-C",
        str(recorded_root / "lean/.lake/packages/mathlib"),
        "rev-parse",
        "HEAD",
    ]
    expected_commands = (
        [lake, "env", "lean", "--version"],
        mathlib,
        [
            lake,
            "build",
            "FepSketches.h3_reference_model",
            "FepSketches.compositions.h3_case_study",
        ],
        [
            lake,
            "env",
            "lean",
            "--threads=1",
            "-R",
            str(recorded_root / parent),
            str(recorded_root / parent / "H3NativeExport.lean"),
        ],
        mathlib,
        [lake, "env", "lean", "--version"],
    )
    budgets = []
    for item, name, expected in zip(
        stages, NATIVE_EXPORT_STAGE_NAMES, expected_commands, strict=True
    ):
        require(
            item.get("name") == name and item.get("command") == expected,
            "native stage command/order changed",
        )
        require(
            type(item.get("returncode")) is int
            and item["returncode"] == 0
            and item.get("timed_out", False) is False,
            "native stage failed or timed out",
        )
        budget: Any = item.get("budget_seconds")
        duration: Any = item.get("duration_seconds")
        require(
            type(budget) in (int, float)
            and math.isfinite(budget)
            and budget > 0
            and type(duration) in (int, float)
            and math.isfinite(duration)
            and 0 <= duration < budget,
            "native stage budget/duration invalid",
        )
        budgets.append(budget)
        require(
            not re.search(
                r"\b(?:warning|error):|\bsorryAx\b",
                text(name + ".stdout") + text(name + ".stderr"),
                re.IGNORECASE,
            ),
            "native stage transcript warned or failed",
        )
    require(
        all(right < left for left, right in pairwise(budgets)),
        "native stage budgets were renewed",
    )
    budget = acceptance.get("capture_budget_seconds")
    duration = acceptance.get("duration_seconds")
    require(
        type(budget) in (int, float)
        and math.isfinite(budget)
        and budget > 0
        and type(duration) in (int, float)
        and math.isfinite(duration)
        and 0 <= duration < budget
        and budgets[0] <= budget,
        "native total capture deadline invalid",
    )
    version = text("compiler-version.stdout").strip()
    pin = read_toolchain_pin(inputs.root / "lean")
    require(
        pin is not None
        and lean_version_matches_pin(version, pin)
        and text("compiler-version-final.stdout").strip() == version
        and export.get("lean_version") == version,
        "native compiler identity mismatch",
    )
    revision = resolved_mathlib_revision(inputs.root / "lean")
    require(
        bool(revision)
        and text("mathlib-head.stdout").strip() == revision
        and text("mathlib-head-final.stdout").strip() == revision
        and export.get("mathlib_revision") == revision,
        "native Mathlib identity mismatch",
    )
    require(
        parse_native_output(
            text("native-export.stdout"),
            text("native-export.stderr"),
            stages[3]["returncode"],
        )
        == export.get("parameters"),
        "native parameter value differs from retained compiler output",
    )
    inputs.stable()


def load_export(
    inputs: Inputs, export_name: str, audit_name: str, review_name: str
) -> dict[str, Any]:
    """Require actual native equality exports and independently reviewed proof roles."""
    export = inputs.json(export_name)
    require(
        type(export.get("schema_version")) is int
        and export.get("schema_version") == 1
        and export.get("kind") == "h3-native-rational-export",
        "native export schema",
    )
    require(
        export.get("protocol_sha256") == PROTOCOL_SHA256,
        "native export protocol mismatch",
    )
    require(
        type(export.get("returncode")) is int
        and export.get("returncode") == 0
        and export.get("warnings") == [],
        "export compiler failed or warned",
    )
    require(
        export.get("source_before") == export.get("source_after"), "export source race"
    )
    require(
        type(export.get("source_after")) is dict and bool(export["source_after"]),
        "empty export source binding",
    )
    for name, digest in export["source_after"].items():
        require(
            type(digest) is str
            and len(digest) == 64
            and all(c in "0123456789abcdef" for c in digest),
            "native source digest must be SHA-256",
        )
        inputs.read(name, expected=digest)
    owner_names = {
        p.relative_to(inputs.root).as_posix()
        for p in (*source_owner_paths(inputs.root), *config_owner_paths(inputs.root))
    } | set(STUDY_SOURCE_FILES)
    require(
        set(export["source_after"]) == owner_names,
        "export source owner roster is incomplete or expanded",
    )
    acceptance_ref = export.get("native_acceptance")
    export_path = PurePosixPath(export_name)
    require(
        export_path.name == "export.json"
        and acceptance_ref == (export_path.parent / "acceptance.json").as_posix(),
        "native export acceptance reference required",
    )
    acceptance = inputs.json(cast(str, acceptance_ref))
    require(
        type(acceptance.get("schema_version")) is int
        and acceptance.get("schema_version") == 1
        and acceptance.get("kind") == "h3-native-export-attempt"
        and acceptance.get("accepted") is True
        and acceptance.get("source_before") == export["source_before"]
        and acceptance.get("source_after") == export["source_after"]
        and acceptance.get("protocol_sha256") == PROTOCOL_SHA256,
        "native export attempt rejected or changed",
    )
    artifacts = export.get("native_artifacts")
    require(type(artifacts) is dict and bool(artifacts), "native artifact roster")
    artifacts = cast(dict[str, str], artifacts)
    require(
        set(artifacts)
        == {
            (export_path.parent / name).as_posix()
            for name in NATIVE_EXPORT_ARTIFACT_FILES
        },
        "native transcript/probe roster is incomplete or expanded",
    )
    expected_retained = dict(artifacts)
    expected_retained[export_name] = inputs.states[export_name].sha256
    require(
        acceptance.get("artifact_sha256") == expected_retained
        and acceptance.get("retained_output_issues") == [],
        "native attempt artifact roster changed",
    )
    for name, digest in artifacts.items():
        require(
            type(digest) is str
            and len(digest) == 64
            and all(c in "0123456789abcdef" for c in digest),
            "native artifact digest must be SHA-256",
        )
        inputs.read(name, expected=digest)
    replay_native_attempt(inputs, export_name, export, acceptance)
    audit = inputs.json(audit_name)
    errors = validate_formalism_audit_receipt(inputs.root / audit_name, inputs.root)
    require(not errors, "current axiom audit rejected: " + "; ".join(errors))
    proof = inputs.json(review_name)
    require(
        type(proof.get("schema_version")) is int
        and proof.get("schema_version") == 1
        and proof.get("protocol_sha256") == PROTOCOL_SHA256,
        "proof review schema/protocol",
    )
    require(
        proof.get("export_sha256") == inputs.states[export_name].sha256,
        "proof review export mismatch",
    )
    roles = proof.get("native_witnesses")
    require(
        type(roles) is dict and set(roles) == PROOF_ROLES,
        "complete native proof-role map required",
    )
    roles = cast(dict[str, str], roles)
    records = {
        record["declaration"]: record for record in audit["declaration_evidence"]
    }
    raw = export.get("parameters")
    require(type(raw) is dict, "missing native parameters")
    raw = cast(dict[str, Any], raw)
    require(
        type(raw.get("witnesses")) is list
        and len(raw["witnesses"]) == len(PARAMETER_WITNESSES)
        and set(raw["witnesses"]) == PARAMETER_WITNESSES,
        "parameter equality witness roster",
    )
    for witness in PARAMETER_WITNESSES:
        require(
            witness in records
            and records[witness]["resolved"] is True
            and records[witness]["uses_sorry_ax"] is False,
            "unresolved parameter bridge: " + witness,
        )
    for role, witness in roles.items():
        require(
            type(witness) is str
            and witness.startswith(
                ("FEP.H3ReferenceModel.", "FEPComposed.H3CaseStudy.")
            ),
            f"unowned witness: {role}",
        )
        require(
            witness in records
            and records[witness]["resolved"] is True
            and records[witness]["uses_sorry_ax"] is False,
            f"unresolved native witness: {role}",
        )
    reviews = proof.get("reviews")
    require(
        type(reviews) is list and len(reviews) == 3,
        "three final independent proof reviews required",
    )
    reviews = cast(list[dict[str, Any]], reviews)
    reviewer_ids, reviewer_roles = set(), set()
    for ref in reviews:
        review = inputs.json(ref["path"], expected=ref["sha256"])
        require(
            type(review.get("schema_version")) is int
            and review.get("schema_version") == 1
            and review.get("decision") == "approve"
            and review.get("native_witnesses") == roles,
            "final proof review not approved/bound",
        )
        require(
            review.get("export_sha256") == inputs.states[export_name].sha256,
            "final review export changed",
        )
        require(
            review.get("source_sha256") == export["source_after"],
            "final review source roster mismatch",
        )
        for name, digest in export["source_after"].items():
            require(
                review.get("source_sha256", {}).get(name) == digest,
                "final review omitted source",
            )
        reviewer_ids.add(review["reviewer_id"])
        reviewer_roles.add(review["role"])
    require(
        len(reviewer_ids) == 3 and reviewer_roles == {"lean", "domain", "statistical"},
        "independent final review identities/roles",
    )
    return raw


def parameters(raw: dict[str, Any], protocol: dict[str, Any]) -> dict[str, np.ndarray]:
    require(
        set(raw)
        == {
            "schema_version",
            "protocol_sha256",
            "axes",
            "axis_fin_order",
            "raw_units",
            "settings",
            "precision",
            "covariance",
            "mode_columns",
            "rates",
            "mode_squared_norms",
            "scales",
            "offsets",
            "rate",
            "diffusion_variance_rate",
            "recognition_coefficients",
            "recognition_variance",
            "recognition_boundary",
            "witnesses",
        },
        "parameter field roster",
    )
    require(
        type(raw["schema_version"]) is int and raw["schema_version"] == 1,
        "parameter schema version",
    )
    require(tuple(raw.get("axes", ())) == AXES, "sealed axis mismatch")
    require(
        raw.get("protocol_sha256") == PROTOCOL_SHA256, "parameter protocol mismatch"
    )
    require(
        raw["axis_fin_order"] == [0, 1, 2, 3]
        and all(type(v) is int for v in raw["axis_fin_order"]),
        "sealed Fin axis order",
    )
    require(
        raw["raw_units"] == protocol["carrier"]["raw_unit_bridge"]["units"],
        "raw unit tags mismatch",
    )
    require(
        type(raw["settings"]) is list and len(raw["settings"]) == 2,
        "native setting roster",
    )
    for actual, expected in zip(
        raw["settings"], protocol["synthetic_acceptance"]["settings"], strict=True
    ):
        require(
            type(actual) is dict
            and set(actual) == {"id", "center", "observation_noise_variance", "delta"}
            and actual["id"] == expected["id"],
            "setting identity mismatch",
        )
        for name in ("center", "observation_noise_variance", "delta"):
            require(
                fraction(actual[name]) == fraction(expected[name]),
                "native setting parameter mismatch",
            )
    require(
        [fraction(v) for v in raw["recognition_coefficients"]] == [0.25, 0.25]
        and fraction(raw["recognition_variance"]) == 0.25,
        "recognition parameter mismatch",
    )
    require(
        raw["recognition_boundary"]
        == "precision_block_algebra_only_native_conditioning_owned_by_composition",
        "recognition proof boundary mismatch",
    )
    k = finite([[fraction(x) for x in row] for row in raw["precision"]], "precision")
    sigma = finite(
        [[fraction(x) for x in row] for row in raw["covariance"]], "covariance"
    )
    require(k.shape == sigma.shape == (4, 4), "four-axis matrix shape required")
    require(
        np.array_equal(k, protocol["carrier"]["precision"]),
        "exported K differs from protocol",
    )
    tol = protocol["synthetic_acceptance"]["exact_fixture_tolerance"]
    require(
        np.max(np.abs(k @ sigma - np.eye(4))) <= tol,
        "derived covariance inverse mismatch",
    )
    rates = finite([fraction(x) for x in raw["rates"]], "rates")
    require(np.array_equal(rates, [2, 4, 4, 6]), "named mode rates mismatch")
    modes = finite(
        [[fraction(x) for x in row] for row in raw["mode_columns"]], "mode columns"
    )
    require(modes.shape == (4, 4), "mode shape")
    squared_norms = finite(
        [fraction(v) for v in raw["mode_squared_norms"]], "native mode squared norms"
    )
    require(
        squared_norms.shape == (4,)
        and np.array_equal(squared_norms, [4, 2, 2, 4])
        and np.array_equal((modes * modes).sum(axis=0), squared_norms),
        "native mode Gram mismatch",
    )
    require(
        np.array_equal(
            modes, [[1, 1, 0, 1], [1, 0, 1, -1], [1, 0, -1, -1], [1, -1, 0, 1]]
        ),
        "sealed named mode orientation mismatch",
    )
    norms = np.sqrt(squared_norms)
    u = modes / norms
    require(np.max(np.abs(u.T @ u - np.eye(4))) <= tol, "mode orthogonality")
    require(np.max(np.abs(k @ u - u * rates)) <= tol, "named eigenmode pairing")
    scales = finite([fraction(x) for x in raw["scales"]], "scales")
    offsets = finite([fraction(x) for x in raw["offsets"]], "offsets")
    require(
        scales.shape == offsets.shape == (4,) and bool(np.all(scales > 0)),
        "positive four-axis calibration required",
    )
    bridge = protocol["carrier"]["raw_unit_bridge"]
    require(
        np.array_equal(scales, bridge["scales"])
        and np.array_equal(offsets, bridge["offsets"]),
        "sealed calibration mismatch",
    )
    require(fraction(raw["diffusion_variance_rate"]) == 2, "diffusion mismatch")
    require(fraction(raw["rate"]) == 2, "projected rate mismatch")
    return {
        "k": k,
        "sigma": sigma,
        "rates": rates,
        "u": u,
        "scales": scales,
        "offsets": offsets,
    }


def posterior(
    y: np.ndarray, mean: float, variance: float, noise: float
) -> tuple[np.ndarray, float]:
    require(
        math.isfinite(mean) and math.isfinite(variance) and math.isfinite(noise),
        "nonfinite posterior parameter",
    )
    require(variance > 0 and noise > 0, "positive prior/noise variance required")
    y = finite(y, "observations")
    gain = variance / (variance + noise)
    return mean + gain * (y - mean), variance * noise / (variance + noise)


def estimates(
    x0: np.ndarray, xt: np.ndarray, delta: float, p: dict[str, np.ndarray]
) -> dict[str, Any]:
    x0, xt = finite(x0, "initial states"), finite(xt, "terminal states")
    require(
        x0.shape == xt.shape and x0.ndim == 2 and x0.shape[1] == 4 and len(x0) >= 5,
        "paired four-axis samples required",
    )
    require(math.isfinite(delta) and delta > 0, "positive delta required")
    n = len(x0)
    z0, zt = x0 - x0.mean(axis=0), xt - xt.mean(axis=0)
    c00 = z0.T @ z0 / n
    require(
        bool(np.all(np.linalg.eigvalsh(c00) > 0)),
        "singular/nonpositive empirical covariance",
    )
    precision = np.linalg.inv(c00)
    transition = (zt.T @ z0 / n) @ precision
    y0, yt = z0 @ p["u"], zt @ p["u"]
    variance = (y0 * y0).mean(axis=0)
    require(bool(np.all(variance > 0)), "zero mode variance")
    rho = (y0 * yt).mean(axis=0) / variance
    require(bool(np.all((rho > 0) & (rho < 1))), "mode slope outside (0,1)")
    rates = -np.log(rho) / delta
    q = ((yt - rho * y0) ** 2).mean(axis=0)
    diffusion = 2 * rates * q / (1 - rho**2)
    design = np.column_stack((np.ones(n), x0[:, 1], x0[:, 2]))
    require(np.linalg.matrix_rank(design) == 3, "recognition design rank failure")
    beta = np.linalg.lstsq(design, x0[:, 0], rcond=None)[0]
    residual = x0[:, 0] - design @ beta
    result = {
        "precision": precision,
        "transition": transition,
        "rates": rates,
        "diffusions": diffusion,
        "recognition": beta,
        "recognition_residual_variance": float((residual**2).mean()),
    }
    for name, value in result.items():
        finite(value, name)
    return {
        name: value.tolist() if isinstance(value, np.ndarray) else value
        for name, value in result.items()
    }


def vector_estimates(result: dict[str, Any]) -> np.ndarray:
    return finite(
        [
            *np.ravel(result["precision"]),
            *np.ravel(result["transition"]),
            *result["rates"],
            *result["diffusions"],
            *result["recognition"],
            result["recognition_residual_variance"],
        ],
        "estimator vector",
    )


def jackknife(
    x0: np.ndarray,
    xt: np.ndarray,
    delta: float,
    p: dict[str, np.ndarray],
    full: dict[str, Any],
) -> dict[str, Any]:
    require(len(x0) == 200000, "frozen jackknife count mismatch")
    replicates, failures = [], []
    indices = np.arange(len(x0))
    for group in range(64):
        keep = (indices < group * 3125) | (indices >= (group + 1) * 3125)
        try:
            replicates.append(vector_estimates(estimates(x0[keep], xt[keep], delta, p)))
        except (StudyRejection, np.linalg.LinAlgError) as exc:
            failures.append({"group": group, "reason": str(exc)})
    if failures:
        return {
            "available": False,
            "failures": failures,
            "boundary": "Failed groups retained; no interval fabricated.",
        }
    values = np.asarray(replicates)
    se = np.sqrt(63 / 64 * ((values - values.mean(axis=0)) ** 2).sum(axis=0))
    point = vector_estimates(full)
    return {
        "available": True,
        "standard_errors": se.tolist(),
        "interval_lower": (point - 1.96 * se).tolist(),
        "interval_upper": (point + 1.96 * se).tolist(),
        "boundary": "Descriptive asymptotic intervals; no finite-sample coverage or acceptance gate.",
    }


def draw_pair(
    rng: np.random.Generator,
    n: int,
    delta: float,
    center: float,
    noise: float,
    p: dict[str, np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    initial = rng.standard_normal((n, 4), dtype=np.float64)
    innovation = rng.standard_normal((n, 4), dtype=np.float64)
    eta = rng.standard_normal(n, dtype=np.float64)
    rho = np.exp(-delta * p["rates"])
    modes0 = initial / np.sqrt(p["rates"])
    modest = modes0 * rho + innovation * np.sqrt((1 - rho**2) / p["rates"])
    mean = center * p["u"][:, 0]
    x0, xt = modes0 @ p["u"].T + mean, modest @ p["u"].T + mean
    y = xt @ p["u"][:, 0] + math.sqrt(noise) * eta
    return x0, xt, y


def sbc_metrics(
    z: np.ndarray,
    y: np.ndarray,
    mean: float,
    noise: float,
    eta: np.ndarray,
    ties: np.ndarray,
) -> tuple[dict[str, Any], np.ndarray]:
    z, y, eta, ties = (
        finite(v, name)
        for v, name in (
            (z, "latent"),
            (y, "observations"),
            (eta, "posterior draws"),
            (ties, "tie uniforms"),
        )
    )
    require(
        z.ndim == 1
        and len(z) > 0
        and y.shape == ties.shape == z.shape
        and eta.shape == (len(z), 31),
        "frozen SBC array shapes",
    )
    require(bool(np.all((ties >= 0) & (ties < 1))), "tie uniforms outside [0,1)")
    m, variance = posterior(y, mean, 0.5, noise)
    draws = m[:, None] + math.sqrt(variance) * eta
    ranks = (draws < z[:, None]).sum(axis=1) + np.floor(
        ties * (1 + (draws == z[:, None]).sum(axis=1))
    ).astype(np.int64)
    require(bool(np.all((ranks >= 0) & (ranks <= 31))), "rank domain failure")
    histogram = np.bincount(ranks, minlength=32)
    w = (z - m) / math.sqrt(variance)
    metrics = {
        "rank_histogram": histogram.tolist(),
        "rank_frequencies": (histogram / len(z)).tolist(),
        "rank_frequency_error": float(np.max(np.abs(histogram / len(z) - 1 / 32))),
        "normalized_rank_mean": float(ranks.mean() / 31),
        "residual_mean": float(w.mean()),
        "residual_variance": float(w.var(ddof=0)),
        "central_95_coverage": float((np.abs(w) <= 1.959963984540054).mean()),
    }
    return metrics, m


class ArrayWriter(Protocol):
    """Array publication or pure retained-byte comparison boundary."""

    def write_new(self, name: str, data: bytes) -> None: ...


def save_array(
    directory: Path | ArrayWriter, name: str, values: np.ndarray
) -> dict[str, str]:
    buffer = io.BytesIO()
    np.save(buffer, finite(values, name).astype("<f8"), allow_pickle=False)
    data = buffer.getvalue()
    owned = AttemptFiles(directory.resolve()) if isinstance(directory, Path) else None
    files = owned if owned is not None else cast(ArrayWriter, directory)
    try:
        files.write_new(name + ".npy", data)
    finally:
        if owned is not None:
            owned.close()
    return {"path": name + ".npy", "sha256": hashlib.sha256(data).hexdigest()}


def recover(
    setting: dict[str, Any],
    protocol: dict[str, Any],
    p: dict[str, np.ndarray],
    directory: Path | AttemptFiles,
) -> dict[str, Any]:
    spec = protocol["synthetic_acceptance"]
    delta, center, noise = (
        fraction(setting["delta"]),
        fraction(setting["center"]),
        fraction(setting["observation_noise_variance"]),
    )
    rng = np.random.Generator(np.random.PCG64(setting["seed"]))
    x0, xt, y = draw_pair(rng, spec["pairs_per_setting"], delta, center, noise, p)
    return analyze_recovery(setting, protocol, p, x0, xt, y, directory)


def analyze_recovery(
    setting: dict[str, Any],
    protocol: dict[str, Any],
    p: dict[str, np.ndarray],
    x0: np.ndarray,
    xt: np.ndarray,
    y: np.ndarray,
    directory: Path | ArrayWriter,
) -> dict[str, Any]:
    """Analyze retained paired states without opening a random stream."""
    spec = protocol["synthetic_acceptance"]
    delta, center, noise = (
        fraction(setting["delta"]),
        fraction(setting["center"]),
        fraction(setting["observation_noise_variance"]),
    )
    n = spec["pairs_per_setting"]
    require(
        x0.shape == xt.shape == (n, 4) and y.shape == (n,),
        "recovery retained array shapes",
    )
    observed = estimates(x0, xt, delta, p)
    exact_transition = (p["u"] * np.exp(-delta * p["rates"])) @ p["u"].T
    metrics = {
        "precision_max_entry_absolute_error": float(
            np.max(np.abs(np.asarray(observed["precision"]) - p["k"]))
        ),
        "transition_eigen_rate_relative_error": float(
            np.max(np.abs(np.asarray(observed["rates"]) - p["rates"]) / p["rates"])
        ),
        "diffusion_variance_rate_absolute_error": float(
            np.max(np.abs(np.asarray(observed["diffusions"]) - 2))
        ),
        "recognition_coefficient_absolute_error": float(
            np.max(np.abs(np.asarray(observed["recognition"])[1:] - 0.25))
        ),
        "recognition_intercept_absolute_error": abs(
            observed["recognition"][0] - center / 4
        ),
        "recognition_residual_variance_absolute_error": abs(
            observed["recognition_residual_variance"] - 0.25
        ),
    }
    gates = {
        name: value <= spec["primary_metrics"][name] for name, value in metrics.items()
    }
    m, variance = posterior(y, center, 0.5, noise)
    wrong_prior_m, _ = posterior(y, center + 1, 0.5, noise)
    z = xt @ p["u"][:, 0]
    wrong_prior_w = (z - wrong_prior_m) / math.sqrt(variance)
    shift = math.exp(-2 * delta)
    shifted_m, _ = posterior(y + shift, center, 0.5, noise)
    shifted_correct_m, shifted_correct_variance = posterior(
        y + shift, center + shift, 0.5, noise
    )
    shifted_wrong_w = (z + shift - shifted_m) / math.sqrt(variance)
    gates["wrong_prior_rejects_nominal_mean"] = abs(float(wrong_prior_w.mean())) > 0.4
    gates["nonstationary_mean_rejects_stationary_substitute"] = (
        abs(float(shifted_wrong_w.mean())) > 0.2
    )
    raw0 = p["offsets"] + p["scales"] * x0
    raw_delta = p["offsets"] + p["scales"] * xt
    roundtrip_error = max(
        float(np.max(np.abs((raw0 - p["offsets"]) / p["scales"] - x0))),
        float(np.max(np.abs((raw_delta - p["offsets"]) / p["scales"] - xt))),
    )
    gates["positive_affine_roundtrip"] = (
        roundtrip_error <= spec["exact_fixture_tolerance"]
    )
    prefix = "recovery_" + setting["id"]
    arrays = {
        name: save_array(directory, prefix + "_" + name, array)
        for name, array in {
            "states0": x0,
            "states_delta": xt,
            "raw_states0": raw0,
            "raw_states_delta": raw_delta,
            "observations": y,
            "posterior_means": m,
            "wrong_prior_means": wrong_prior_m,
            "shifted_wrong_means": shifted_m,
            "shifted_correct_means": shifted_correct_m,
        }.items()
    }
    halves = {
        name: estimates(x0[index::2], xt[index::2], delta, p)
        for index, name in enumerate(("even", "odd"))
    }
    return {
        "setting": setting,
        "estimates": observed,
        "metrics": metrics,
        "transition_baseline_max_entry_error_diagnostic": float(
            np.max(np.abs(np.asarray(observed["transition"]) - exact_transition))
        ),
        "gates": gates,
        "accepted": all(gates.values()),
        "jackknife": jackknife(x0, xt, delta, p, observed),
        "sensitivity_halves": halves,
        "half_differences": (
            vector_estimates(halves["even"]) - vector_estimates(halves["odd"])
        ).tolist(),
        "wrong_prior_residual_mean": float(wrong_prior_w.mean()),
        "shifted_wrong_residual_mean": float(shifted_wrong_w.mean()),
        "shifted_correct_predictive_mean": center + shift,
        "shifted_correct_posterior_variance": shifted_correct_variance,
        "roundtrip_max_error": roundtrip_error,
        "zero_coefficient_baseline_residual_variance": float(
            ((x0[:, 0] - center / 2) ** 2).mean()
        ),
        "arrays": arrays,
    }


def calibrate(
    setting: dict[str, Any],
    sbc_setting: dict[str, Any],
    protocol: dict[str, Any],
    p: dict[str, np.ndarray],
    directory: Path | AttemptFiles,
) -> dict[str, Any]:
    spec = protocol["synthetic_acceptance"]["simulation_based_calibration"]
    n = spec["replications_per_setting"]
    delta, center, noise = (
        fraction(setting["delta"]),
        fraction(setting["center"]),
        fraction(setting["observation_noise_variance"]),
    )
    rng = np.random.Generator(np.random.PCG64(sbc_setting["seed"]))
    x0, xt, y = draw_pair(rng, n, delta, center, noise, p)
    eta = rng.standard_normal(
        (n, spec["posterior_draws_per_replication"]), dtype=np.float64
    )
    ties = rng.random(n)
    return analyze_calibration(
        setting, sbc_setting, protocol, p, x0, xt, y, eta, ties, directory
    )


def calibration_nominal_gates(
    metrics: dict[str, Any], thresholds: dict[str, Any]
) -> dict[str, bool]:
    """Apply the same five frozen nominal thresholds to either noise model."""
    return {
        "rank_frequency": metrics["rank_frequency_error"]
        <= thresholds["maximum_32_bin_rank_frequency_absolute_error_from_one_over_32"],
        "rank_mean": abs(metrics["normalized_rank_mean"] - 0.5)
        <= thresholds["normalized_rank_mean_absolute_error_from_one_half"],
        "residual_mean": abs(metrics["residual_mean"])
        <= thresholds["standardized_residual_mean_absolute_value"],
        "residual_variance": abs(metrics["residual_variance"] - 1)
        <= thresholds["standardized_residual_variance_absolute_error_from_one"],
        "coverage": abs(metrics["central_95_coverage"] - 0.95)
        <= thresholds["central_95_percent_coverage_absolute_error_from_0_95"],
    }


def analyze_calibration(
    setting: dict[str, Any],
    sbc_setting: dict[str, Any],
    protocol: dict[str, Any],
    p: dict[str, np.ndarray],
    x0: np.ndarray,
    xt: np.ndarray,
    y: np.ndarray,
    eta: np.ndarray,
    ties: np.ndarray,
    directory: Path | ArrayWriter,
) -> dict[str, Any]:
    """Analyze retained SBC states, posterior normals and ties with no draws."""
    spec = protocol["synthetic_acceptance"]["simulation_based_calibration"]
    n = spec["replications_per_setting"]
    center, noise = (
        fraction(setting["center"]),
        fraction(setting["observation_noise_variance"]),
    )
    require(
        x0.shape == xt.shape == (n, 4)
        and y.shape == ties.shape == (n,)
        and eta.shape == (n, spec["posterior_draws_per_replication"]),
        "calibration retained array shapes",
    )
    z = xt @ p["u"][:, 0]
    observed, m = sbc_metrics(z, y, center, noise, eta, ties)
    wrong, wrong_m = sbc_metrics(z, y, center, 2 * noise, eta, ties)
    thresholds = spec["conjunctive_thresholds_each_setting"]
    gates = calibration_nominal_gates(observed, thresholds)
    wrong_nominal_gates = calibration_nominal_gates(wrong, thresholds)

    target = fraction(
        spec["wrong_noise_control"]["standardized_residual_variance_targets"][
            setting["id"]
        ]
    )
    gates.update(
        {
            "wrong_noise_target": abs(wrong["residual_variance"] - target) <= 0.04,
            "wrong_noise_variance_rejects_nominal": abs(wrong["residual_variance"] - 1)
            > 0.10,
            "wrong_noise_coverage_rejects_nominal": abs(
                wrong["central_95_coverage"] - 0.95
            )
            > 0.015,
        }
    )
    arrays = {
        name: save_array(directory, "sbc_" + setting["id"] + "_" + name, array)
        for name, array in {
            "latent": z,
            "observations": y,
            "posterior_means": m,
            "wrong_noise_means": wrong_m,
            "states0": x0,
            "states_delta": xt,
            "posterior_standard_normals": eta,
            "tie_uniforms": ties,
        }.items()
    }
    return {
        "setting_id": setting["id"],
        "seed": sbc_setting["seed"],
        "nominal": observed,
        "wrong_noise": wrong,
        "wrong_noise_nominal_gates": wrong_nominal_gates,
        "wrong_noise_nominal_accepted": all(wrong_nominal_gates.values()),
        "gates": gates,
        "accepted": all(gates.values()),
        "arrays": arrays,
    }


def exact_controls(
    protocol: dict[str, Any], p: dict[str, np.ndarray]
) -> dict[str, Any]:
    """Deterministic diagnostics; native proof roles remain separately required."""
    tol = protocol["synthetic_acceptance"]["exact_fixture_tolerance"]
    sigma = p["sigma"]
    clamp_cov = sigma[0, 3] - sigma[0, 1] * sigma[1, 3] / sigma[1, 1]
    clamp_var = sigma[0, 0] - sigma[0, 1] ** 2 / sigma[1, 1]
    times = np.asarray([0.0, 0.25, 0.5])
    covariance = 0.5 * np.exp(-2 * np.abs(times[:, None] - times))
    mean = np.exp(-2 * times)
    difference = mean - mean[::-1]
    grid_kl = float(0.5 * difference @ np.linalg.solve(covariance, difference))
    r = math.exp(-0.5)
    q = (1 - r**2) / 2
    bound = 1 + q / (1 - r)
    consistency = {}
    calibration_fixtures = {}
    consistency_spec = protocol["synthetic_acceptance"][
        "fixed_latent_posterior_consistency"
    ]
    ys = consistency_spec["deterministic_fixtures"]["observation_list"]
    for setting in protocol["synthetic_acceptance"]["settings"]:
        noise, center = (
            Fraction(str(setting["observation_noise_variance"])),
            Fraction(str(setting["center"])),
        )
        rows = []
        for n in consistency_spec["deterministic_fixtures"]["counts"]:
            variance = noise / (2 * noise + n)
            posterior_mean = (2 * noise * center + sum(ys[:n])) / (2 * noise + n)
            sequential_mean, sequential_variance = float(center), 0.5
            for observation in ys[:n]:
                updated_mean, sequential_variance = posterior(
                    np.asarray([observation]),
                    sequential_mean,
                    sequential_variance,
                    float(noise),
                )
                sequential_mean = float(updated_mean[0])
            # Independent affine-error expansion under the declared Gaussian
            # joint: prior-error variance plus n independent noise variances.
            joint_mse = ((2 * float(noise)) ** 2 * 0.5 + n * float(noise)) / (
                2 * float(noise) + n
            ) ** 2
            tail = (
                joint_mse
                / fraction(consistency_spec["deterministic_fixtures"]["epsilon"]) ** 2
            )
            rows.append(
                {
                    "n": n,
                    "variance": str(variance),
                    "mean": str(posterior_mean),
                    "native_joint_mse": str(variance),
                    "markov_tail_bound_epsilon_half": str(4 * variance),
                    "sequential_mean": sequential_mean,
                    "sequential_variance": sequential_variance,
                    "affine_joint_mse": joint_mse,
                    "independent_tail_bound": tail,
                    "matches": abs(sequential_mean - float(posterior_mean)) <= tol
                    and abs(sequential_variance - float(variance)) <= tol
                    and abs(joint_mse - float(variance)) <= tol
                    and abs(tail - float(4 * variance)) <= tol,
                }
            )
        consistency[setting["id"]] = rows
        _, actual_variance = posterior(
            np.asarray([0.0, 1.0]), float(center), 0.5, float(noise)
        )
        _, wrong_variance = posterior(
            np.asarray([0.0, 1.0]), float(center), 0.5, 2 * float(noise)
        )
        expected_variance = noise / (2 * noise + 1)
        expected_wrong = 2 * noise / (4 * noise + 1)
        wrong_prior_mean, _ = posterior(
            np.asarray([float(center)]), float(center) + 1, 0.5, float(noise)
        )
        actual_bias = (float(center) - float(wrong_prior_mean[0])) / math.sqrt(
            actual_variance
        )
        expected_bias = {"A": -math.sqrt(2 / 5), "B": -math.sqrt(2 / 3)}[setting["id"]]
        shift = math.exp(-2 * fraction(setting["delta"]))
        correct_mean, correct_variance = posterior(
            np.asarray([float(center) + shift]),
            float(center) + shift,
            0.5,
            float(noise),
        )
        stationary_substitute, _ = posterior(
            np.asarray([float(center) + shift]), float(center), 0.5, float(noise)
        )
        substitute_bias = (
            float(center) + shift - float(stationary_substitute[0])
        ) / math.sqrt(actual_variance)
        expected_shift_bias = (
            float(2 * noise / (2 * noise + 1))
            * shift
            / math.sqrt(float(expected_variance))
        )
        calibration_fixtures[setting["id"]] = {
            "variance": actual_variance,
            "expected_variance": str(expected_variance),
            "misspecified_variance": wrong_variance,
            "expected_misspecified_variance": str(expected_wrong),
            "misspecification_error": abs(actual_variance - wrong_variance),
            "matches": abs(actual_variance - float(expected_variance)) <= tol
            and abs(wrong_variance - float(expected_wrong)) <= tol,
            "wrong_prior_standardized_bias": actual_bias,
            "wrong_prior_expected_bias": expected_bias,
            "shifted_correct_mean": float(correct_mean[0]),
            "shifted_correct_variance": correct_variance,
            "shifted_stationary_substitute_bias": substitute_bias,
            "prior_bias_matches": abs(actual_bias - expected_bias) <= tol,
            "shift_matches": abs(float(correct_mean[0]) - float(center) - shift) <= tol
            and abs(correct_variance - float(expected_variance)) <= tol
            and abs(substitute_bias - expected_shift_bias) <= tol,
        }
    permutation = np.eye(4)[[1, 0, 2, 3]]
    wrong_rates = np.asarray([6, 4, 4, 2])
    gates = {
        "clamp_covariance": abs(clamp_cov - 1 / 56) <= tol,
        "clamp_variance": abs(clamp_var - 15 / 56) <= tol,
        "positive_grid_covariance": bool(np.all(np.linalg.eigvalsh(covariance) > 0)),
        "grid_kl": abs(grid_kl - 2 * (1 - math.exp(-1))) <= tol,
        "controlled_bound": abs(bound - (1.5 + 0.5 * r)) <= tol,
        "preference_counterexample": (2 * r - 1) ** 2 < 1 and (2 * r - 2) ** 2 > 0,
        "restricted_class_counterexample": 0.5 + (1 - r**2) ** 2 > 0.5 + (1 - r) ** 4,
        "law_changing_axis_permutation": not np.array_equal(
            permutation @ p["k"] @ permutation.T, p["k"]
        ),
        "law_changing_rate_pairing": np.max(
            np.abs((p["u"] * wrong_rates) @ p["u"].T - p["k"])
        )
        > tol,
        "hidden_mode_projection_zero": abs(float(p["u"][:, 0] @ p["u"][:, 1])) <= tol,
        "distinct_constitutive_heat_assignments": grid_kl > 0
        and grid_kl != 2 * grid_kl,
        "calibration_fixtures": all(
            row["matches"]
            and row["misspecification_error"]
            > protocol["synthetic_acceptance"][
                "misspecified_noise_min_absolute_variance_error"
            ]
            for row in calibration_fixtures.values()
        ),
        "fixed_latent_consistency": all(
            row["matches"] for rows in consistency.values() for row in rows
        ),
        "positive_decreasing_consistency_variance": all(
            all(
                fraction(rows[index]["variance"])
                > fraction(rows[index + 1]["variance"])
                > 0
                for index in range(len(rows) - 1)
            )
            for rows in consistency.values()
        ),
        "wrong_prior_exact_bias": all(
            row["prior_bias_matches"] for row in calibration_fixtures.values()
        ),
        "shifted_correct_mean_and_variance": all(
            row["shift_matches"] for row in calibration_fixtures.values()
        ),
    }
    return {
        "gates": gates,
        "accepted": all(gates.values()),
        "clamp_covariance": clamp_cov,
        "clamp_variance": clamp_var,
        "grid_kl": grid_kl,
        "marginal_kl": np.exp(-4 * times).tolist(),
        "controlled_bound": bound,
        "fixed_latent_consistency": consistency,
        "calibration_fixtures": calibration_fixtures,
        "singular_grid": {
            "kl": "infinity",
            "status": "requires separately reviewed native support witness",
        },
        "boundary": "Deterministic non-proof computations; equality, support and probability claims require the native witness map.",
    }


def control_simulation(
    protocol: dict[str, Any], p: dict[str, np.ndarray], directory: Path | AttemptFiles
) -> dict[str, Any]:
    spec = protocol["synthetic_acceptance"]
    n = (
        spec["control_evaluation"]
        if type(spec["control_evaluation"]) is int
        else 200000
    )
    require(n == 200000, "frozen control count")
    rng = np.random.Generator(np.random.PCG64(spec["controls_seed"]))
    initial = rng.standard_normal((n, 4), dtype=np.float64)
    innovation1 = rng.standard_normal((n, 4), dtype=np.float64)
    observation = rng.standard_normal(n, dtype=np.float64)
    innovation2 = rng.standard_normal((n, 4), dtype=np.float64)
    rates, u = p["rates"], p["u"]
    x0 = (initial / np.sqrt(rates)) @ u.T
    return analyze_control(
        protocol, p, x0, innovation1, observation, innovation2, directory
    )


def analyze_control(
    protocol: dict[str, Any],
    p: dict[str, np.ndarray],
    x0: np.ndarray,
    innovation1: np.ndarray,
    observation: np.ndarray,
    innovation2: np.ndarray,
    directory: Path | ArrayWriter,
) -> dict[str, Any]:
    """Reuse the retained shared control arrays without generating any noise."""
    spec = protocol["synthetic_acceptance"]
    n = (
        spec["control_evaluation"]
        if type(spec["control_evaluation"]) is int
        else 200000
    )
    require(
        x0.shape == innovation1.shape == innovation2.shape == (n, 4)
        and observation.shape == (n,),
        "control retained array shapes",
    )
    rates, u = p["rates"], p["u"]
    rho = np.exp(-0.25 * rates)
    innovation_scale = np.sqrt((1 - rho**2) / rates)
    arrays = {
        name: save_array(directory, "control_shared_" + name, values)
        for name, values in {
            "initial_states": x0,
            "first_mode_innovations": innovation1,
            "observation_standard_noise": observation,
            "second_mode_innovations": innovation2,
        }.items()
    }
    r, q = float(rho[0]), float(innovation_scale[0] ** 2)
    results: dict[str, dict[str, Any]] = {}
    for setting in spec["settings"]:
        noise = fraction(setting["observation_noise_variance"])
        plans, contingent, moments, posterior_arrays = {}, {}, {}, {}
        for a0 in (-1, 1):
            center0 = a0 * u[:, 0]
            x1 = (
                (x0 - center0) @ u * rho @ u.T
                + center0
                + (innovation1 * innovation_scale) @ u.T
            )
            z1 = x1 @ u[:, 0]
            y = z1 + math.sqrt(noise) * observation
            m, posterior_variance = posterior(y, (1 - r) * a0, 0.5, noise)
            choices = np.where(m >= 0, -1, 1)
            for label, a1 in (("false", -1), ("true", 1), ("contingent", choices)):
                center1 = np.asarray(a1)[..., None] * u[:, 0]
                x2 = (
                    (x1 - center1) @ u * rho @ u.T
                    + center1
                    + (innovation2 * innovation_scale) @ u.T
                )
                objective = float(((x2 @ u[:, 0]) ** 2).mean())
                if label == "contingent":
                    contingent[str(a0)] = objective
                else:
                    plans[f"{a0},{a1}"] = objective
                moments[f"{a0},{label}"] = float((x2**2).sum(axis=1).mean())
            posterior_arrays[str(a0)] = save_array(
                directory, f"control_{setting['id']}_{a0}_posterior_means", m
            )
        # The exact symmetry gives equal attained first-action objectives;
        # false is selected before true independently of Monte Carlo values.
        chosen = contingent["-1"]
        advantage = chosen - min(plans.values())
        v = r * r * posterior_variance + q
        information = 0.5 * math.log1p(v / noise)
        results[setting["id"]] = {
            "open_loop_objectives": plans,
            "contingent_objectives": contingent,
            "selected_first_action": False,
            "selected_contingent_minus_best_sample_open_loop": advantage,
            "gates": {
                "contained_policy_advantage": advantage
                <= spec["primary_metrics"][
                    "contingent_minus_best_open_loop_objective_upper_tolerance"
                ],
            },
            "full_second_moments": moments,
            "posterior_mean_arrays": posterior_arrays,
            "theorem_full_second_moment_upper_bound": 1.5 + 0.5 * r + 2 / 3,
            "moment_reporting_boundary": "Unthresholded sample diagnostic; the native expectation bound is separately proved. No Monte Carlo tolerance was preregistered.",
            "action_common_information": information,
            "efe_minus_risk": 0.5 * math.log(math.pi) - information,
        }
    return {
        "seed": spec["controls_seed"],
        "results": results,
        "shared_arrays": arrays,
        "accepted": all(all(row["gates"].values()) for row in results.values()),
        "boundary": "Same random arrays reused across both settings and all policies; action choice uses exact tie convention, not fitted sample risk.",
    }


def run_study(
    root: Path,
    output: Path,
    export: str,
    audit: str,
    proof_review: str,
    *,
    check_inputs: bool = False,
) -> dict[str, Any]:
    inputs = Inputs(root)
    protocol = frozen_protocol(inputs)
    raw = load_export(inputs, export, audit, proof_review)
    p = parameters(raw, protocol)
    inputs.read(BASE + "run_synthetic.py")
    inputs.stable()
    if check_inputs:
        return {
            "status": "inputs_valid",
            "scientific_draws_executed": False,
            "source_sha256": inputs.hashes(),
        }
    env = protocol["synthetic_acceptance"]["execution_environment"]
    require(
        platform.python_version() == env["python"] and np.__version__ == env["numpy"],
        "frozen execution runtime mismatch",
    )
    output = new_output(inputs.root, output)
    negative_controls = parameter_negative_controls(raw, protocol)
    files = AttemptFiles(output, create=True)
    record: dict[str, Any] = {
        "schema_version": 1,
        "gate": "H3.6S",
        "study_id": protocol["study_id"],
        "protocol_sha256": PROTOCOL_SHA256,
        "accepted": False,
        "source_before": inputs.hashes(),
        "execution_environment": env,
        "empirical_gate": "governed_no_go",
        "input_negative_controls": negative_controls,
    }
    try:
        exact = exact_controls(protocol, p)
        record["exact_controls"] = exact
        require(exact["accepted"], "exact fixture/control failure")
        spec = protocol["synthetic_acceptance"]
        calibrations: list[dict[str, Any]] = []
        record["calibration"] = calibrations
        for setting, sbc_setting in zip(
            spec["settings"],
            spec["simulation_based_calibration"]["settings"],
            strict=True,
        ):
            calibrations.append(calibrate(setting, sbc_setting, protocol, p, files))
        recoveries: list[dict[str, Any]] = []
        record["recovery"] = recoveries
        for setting in spec["settings"]:
            recoveries.append(recover(setting, protocol, p, files))
        control = control_simulation(protocol, p, files)
        record["control"] = control
        declared_artifacts = array_references(record)
        actual_artifacts, artifact_issues = files.inventory()
        require(
            not artifact_issues,
            "invalid output entries: " + json.dumps(artifact_issues),
        )
        require(
            declared_artifacts == actual_artifacts,
            "generated output/hash roster mismatch",
        )
        record["artifact_sha256"] = actual_artifacts
        inputs.stable()
        require(
            not validate_formalism_audit_receipt(inputs.root / audit, inputs.root),
            "axiom audit changed during execution",
        )
        record["source_after"] = inputs.hashes()
        record["accepted"] = (
            all(row["accepted"] for row in calibrations + recoveries)
            and control["accepted"]
        )
        record["decision"] = "accepted" if record["accepted"] else "rejected"
    except (StudyRejection, OSError, ValueError, np.linalg.LinAlgError) as exc:
        record["decision"] = "rejected"
        record["failure"] = {"type": type(exc).__name__, "reason": str(exc)}
        raise
    except Exception as exc:
        record["decision"] = "failed"
        record["failure"] = {"type": type(exc).__name__, "reason": str(exc)}
        raise
    finally:
        retained, issues = files.inventory(strict=False)
        record["retained_artifact_sha256"] = retained
        record["retained_output_issues"] = issues
        if record["accepted"] and (issues or retained != record.get("artifact_sha256")):
            record["accepted"] = False
            record["decision"] = "rejected"
            record["failure"] = {
                "type": "StudyRejection",
                "reason": "output changed during final source check",
            }
        data = (
            json.dumps(
                json_primitives(record), indent=2, sort_keys=True, allow_nan=False
            )
            + "\n"
        ).encode()
        try:
            files.receipt(data)
        finally:
            files.close()
    return record


class RetainedArrayReplay:
    """Pure array loader/comparator; scientific files and generators are untouched."""

    def __init__(self, artifacts: dict[str, str], loader: Callable[[str], bytes]):
        self.artifacts = artifacts
        self.loader = loader
        self.buffers: dict[str, bytes] = {}
        self.compared: set[str] = set()

    def _bytes(self, name: str) -> bytes:
        require(name in self.artifacts, "missing retained array: " + name)
        if name not in self.buffers:
            try:
                data = self.loader(name)
            except (OSError, KeyError) as exc:
                raise StudyRejection("cannot load retained array: " + name) from exc
            require(type(data) is bytes, "retained array loader must return bytes")
            require(len(data) <= 128 * 1024 * 1024, "oversized retained array")
            require(
                hashlib.sha256(data).hexdigest() == self.artifacts[name],
                "retained array hash mismatch: " + name,
            )
            self.buffers[name] = data
        return self.buffers[name]

    def read(self, name: str, shape: tuple[int, ...]) -> np.ndarray:
        data = self._bytes(name)
        stream = io.BytesIO(data)
        try:
            version = np.lib.format.read_magic(stream)
            require(version in ((1, 0), (2, 0)), "unsupported retained NPY version")
            reader = (
                np.lib.format.read_array_header_1_0
                if version == (1, 0)
                else np.lib.format.read_array_header_2_0
            )
            declared_shape, fortran, dtype = reader(stream)
            require(
                declared_shape == shape
                and all(type(n) is int and n >= 0 for n in declared_shape)
                and fortran is False
                and dtype.str == "<f8"
                and stream.tell() + math.prod(shape) * dtype.itemsize == len(data),
                "retained array shape/dtype/EOF mismatch: " + name,
            )
            stream.seek(0)
            values = np.load(stream, allow_pickle=False)
        except (ValueError, OSError, EOFError) as exc:
            raise StudyRejection("invalid retained array: " + name) from exc
        require(
            type(values) is np.ndarray
            and values.dtype.str == "<f8"
            and values.shape == shape
            and stream.tell() == len(data),
            "retained array shape/dtype/EOF mismatch: " + name,
        )
        finite(values, name)
        return cast(np.ndarray, values)

    def write_new(self, name: str, data: bytes) -> None:
        require(
            name not in self.compared and name in self.artifacts,
            "unknown or duplicate replay array: " + name,
        )
        require(
            self._bytes(name) == data
            and hashlib.sha256(data).hexdigest() == self.artifacts[name],
            "retained array differs from deterministic replay: " + name,
        )
        self.compared.add(name)


def replay_synthetic_attempt(
    protocol: dict[str, Any],
    native_parameters_raw: dict[str, Any],
    record: dict[str, Any],
    array_loader: Callable[[str], bytes],
) -> dict[str, Any]:
    """Reconstruct a complete primary result from retained arrays, with no draws.

    The caller validates frozen protocol/export/source metadata and supplies a
    containment-safe bytes loader. This function checks every analysis field,
    array byte stream, setting and decision; it is not seed-generation evidence.
    """
    require(type(record) is dict and record.get("failure") is None, "partial attempt")
    artifacts = record.get("artifact_sha256")
    require(
        type(artifacts) is dict
        and bool(artifacts)
        and all(
            type(name) is str
            and Path(name).name == name
            and name.endswith(".npy")
            and type(digest) is str
            and re.fullmatch(r"[0-9a-f]{64}", digest) is not None
            for name, digest in artifacts.items()
        ),
        "complete typed retained array roster required",
    )
    artifacts = cast(dict[str, str], artifacts)
    require(
        record.get("retained_artifact_sha256") == artifacts
        and record.get("retained_output_issues") == []
        and array_references(record) == artifacts,
        "retained array roster incomplete or altered",
    )
    p = parameters(native_parameters_raw, protocol)
    sink = RetainedArrayReplay(artifacts, array_loader)
    spec = protocol["synthetic_acceptance"]
    sbc = spec["simulation_based_calibration"]
    reconstructed: dict[str, Any] = {
        "input_negative_controls": parameter_negative_controls(
            native_parameters_raw, protocol
        ),
        "exact_controls": exact_controls(protocol, p),
        "calibration": [],
        "recovery": [],
    }
    require(
        reconstructed["exact_controls"]["accepted"], "exact fixture/control failure"
    )
    for setting, sbc_setting in zip(spec["settings"], sbc["settings"], strict=True):
        n = sbc["replications_per_setting"]
        prefix = "sbc_" + setting["id"] + "_"
        reconstructed["calibration"].append(
            analyze_calibration(
                setting,
                sbc_setting,
                protocol,
                p,
                sink.read(prefix + "states0.npy", (n, 4)),
                sink.read(prefix + "states_delta.npy", (n, 4)),
                sink.read(prefix + "observations.npy", (n,)),
                sink.read(
                    prefix + "posterior_standard_normals.npy",
                    (n, sbc["posterior_draws_per_replication"]),
                ),
                sink.read(prefix + "tie_uniforms.npy", (n,)),
                sink,
            )
        )
    for setting in spec["settings"]:
        n = spec["pairs_per_setting"]
        prefix = "recovery_" + setting["id"] + "_"
        reconstructed["recovery"].append(
            analyze_recovery(
                setting,
                protocol,
                p,
                sink.read(prefix + "states0.npy", (n, 4)),
                sink.read(prefix + "states_delta.npy", (n, 4)),
                sink.read(prefix + "observations.npy", (n,)),
                sink,
            )
        )
    n = (
        spec["control_evaluation"]
        if type(spec["control_evaluation"]) is int
        else 200000
    )
    reconstructed["control"] = analyze_control(
        protocol,
        p,
        sink.read("control_shared_initial_states.npy", (n, 4)),
        sink.read("control_shared_first_mode_innovations.npy", (n, 4)),
        sink.read("control_shared_observation_standard_noise.npy", (n,)),
        sink.read("control_shared_second_mode_innovations.npy", (n, 4)),
        sink,
    )
    require(sink.compared == set(artifacts), "unexpected retained array roster")
    reconstructed["accepted"] = (
        all(
            row["accepted"]
            for row in reconstructed["calibration"] + reconstructed["recovery"]
        )
        and reconstructed["control"]["accepted"]
    )
    reconstructed["decision"] = "accepted" if reconstructed["accepted"] else "rejected"
    metadata_keys = {
        "schema_version",
        "gate",
        "study_id",
        "protocol_sha256",
        "source_before",
        "source_after",
        "execution_environment",
        "empirical_gate",
        "artifact_sha256",
        "retained_artifact_sha256",
        "retained_output_issues",
    }
    require(
        set(record) - {"failure"} == metadata_keys | set(reconstructed),
        "synthetic result field roster incomplete or unknown",
    )
    for name, expected in reconstructed.items():
        try:
            actual_bytes = json.dumps(
                json_primitives(record[name]),
                sort_keys=True,
                allow_nan=False,
                separators=(",", ":"),
            )
            expected_bytes = json.dumps(
                json_primitives(expected),
                sort_keys=True,
                allow_nan=False,
                separators=(",", ":"),
            )
        except (TypeError, ValueError) as exc:
            raise StudyRejection("invalid synthetic result field: " + name) from exc
        require(actual_bytes == expected_bytes, "synthetic replay mismatch: " + name)
    return cast(dict[str, Any], json_primitives(reconstructed))


def array_references(value: Any) -> dict[str, str]:
    references: dict[str, str] = {}

    def walk(item: Any) -> None:
        if type(item) is dict:
            if set(item) == {"path", "sha256"}:
                require(
                    type(item["path"]) is str
                    and Path(item["path"]).name == item["path"]
                    and item["path"].endswith(".npy"),
                    "unsafe array reference",
                )
                require(item["path"] not in references, "duplicate array reference")
                references[item["path"]] = item["sha256"]
            else:
                for child in item.values():
                    walk(child)
        elif type(item) is list:
            for child in item:
                walk(child)

    walk(value)
    return dict(sorted(references.items()))


def output_artifacts(directory: Path, *, strict: bool = True) -> dict[str, str]:
    files = AttemptFiles(directory)
    try:
        result, issues = files.inventory(strict=strict)
        require(not issues, "unexpected output artifact: " + json.dumps(issues))
        return result
    finally:
        files.close()


def new_output(root: Path, output: Path) -> Path:
    require(output.is_absolute(), "absolute attempt output required")
    require(
        not any(p.is_symlink() for p in (output, *output.parents)),
        "output traverses a symlink",
    )
    require(
        output.parent.is_dir() and not output.exists(),
        "new attempt with existing parent required",
    )
    canonical = output.resolve()
    if canonical.is_relative_to(root):
        require(
            canonical.parent == root / (BASE + "output"),
            "repository attempt must use the H3 output directory",
        )
    return canonical


def evidence_mass(values: Any, weights: Any) -> float:
    density, mass = finite(values, "density"), finite(weights, "reference mass")
    require(
        density.shape == mass.shape
        and bool(np.all(density >= 0))
        and bool(np.all(mass >= 0)),
        "nonnegative matching density/reference required",
    )
    normalizer = float(np.sum(density * mass))
    require(
        math.isfinite(normalizer) and normalizer > 0,
        "zero/nonpositive evidence normalizer",
    )
    return normalizer


def parameter_negative_controls(
    raw: dict[str, Any], protocol: dict[str, Any]
) -> dict[str, Any]:
    """Locked malformed-input controls, with no new scientific random stream."""
    rejected = {}
    for label in (
        "axis_labels",
        "axis_indices",
        "missing_scale",
        "nonpositive_scale",
        "double_active_scale",
        "stale_protocol",
        "wrong_rate_pairing",
    ):
        bad = copy.deepcopy(raw)
        if label == "axis_labels":
            bad["axes"][0], bad["axes"][1] = bad["axes"][1], bad["axes"][0]
        elif label == "axis_indices":
            bad["axis_fin_order"][0], bad["axis_fin_order"][1] = 1, 0
        elif label == "missing_scale":
            bad["scales"].pop()
        elif label == "nonpositive_scale":
            bad["scales"][2] = {"numerator": 0, "denominator": 1}
        elif label == "double_active_scale":
            bad["scales"][2] = {"numerator": 6, "denominator": 1}
        elif label == "stale_protocol":
            bad["protocol_sha256"] = "0" * 64
        else:
            bad["rates"][0], bad["rates"][3] = bad["rates"][3], bad["rates"][0]
        try:
            parameters(bad, protocol)
        except StudyRejection as exc:
            rejected[label] = str(exc)
        else:
            raise StudyRejection("negative control silently accepted: " + label)
    for label, call in (
        ("zero_observation_variance", lambda: posterior(np.asarray([0.0]), 0, 0.5, 0)),
        ("zero_evidence_normalizer", lambda: evidence_mass([0, 0], [0.5, 0.5])),
    ):
        try:
            call()
        except StudyRejection as exc:
            rejected[label] = str(exc)
        else:
            raise StudyRejection("density negative control silently accepted")
    require(
        evidence_mass([0, 1], [0, 1]) == 1, "null-point density must remain accepted"
    )
    return {
        "rejected": rejected,
        "null_point_density_accepted": True,
        "boundary": "Input/deterministic implementation controls; native probability/support and stale source/export controls are independently required.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--export", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--proof-review", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--check-inputs", action="store_true")
    args = parser.parse_args()
    try:
        result = run_study(
            args.project_root,
            args.output,
            args.export,
            args.audit,
            args.proof_review,
            check_inputs=args.check_inputs,
        )
        print(
            json.dumps(
                {
                    "status": result.get("decision", result.get("status")),
                    "accepted": result.get("accepted", False),
                    "scientific_draws_executed": not args.check_inputs,
                },
                sort_keys=True,
            )
        )
        return 0 if args.check_inputs or result["accepted"] else 1
    except (StudyRejection, OSError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "status": "rejected",
                    "error_type": type(exc).__name__,
                    "reason": str(exc),
                },
                sort_keys=True,
            )
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
