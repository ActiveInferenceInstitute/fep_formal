"""Check measured package line floors without changing coverage collection mode.

This documentation-local checker reads coverage.py XML; it never imports the
package, executes tests, or treats line coverage as branch-arc coverage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_PACKAGE = re.compile(r"fep_lean(?:\.[A-Za-z_][A-Za-z_0-9]*)*\Z")
_INTEGER = re.compile(r"(?:0|[1-9][0-9]{0,9})\Z")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _read_regular(path: Path, limit: int) -> bytes:
    before = path.lstat()
    _require(stat.S_ISREG(before.st_mode), f"not a regular input: {path}")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as handle:
        opened = os.fstat(handle.fileno())
        _require(
            (before.st_dev, before.st_ino) == (opened.st_dev, opened.st_ino),
            f"input replaced while opening: {path}",
        )
        data = handle.read(limit + 1)
        after = os.fstat(handle.fileno())
    _require(len(data) <= limit, f"oversized input: {path}")
    _require(
        (opened.st_size, opened.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
        and len(data) == after.st_size,
        f"input changed while reading: {path}",
    )
    return data


def _unique_pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        _require(key not in result, f"duplicate policy key: {key}")
        result[key] = value
    return result


def _reject_constant(token: str) -> None:
    raise ValueError(f"nonfinite policy number: {token}")


def _reject_float(token: str) -> None:
    raise ValueError(f"policy numbers must use integer notation: {token}")


def load_policy(data: bytes) -> dict[str, Any]:
    policy: dict[str, Any] = json.loads(
        data,
        object_pairs_hook=_unique_pairs,
        parse_constant=_reject_constant,
        parse_float=_reject_float,
    )
    _require(isinstance(policy, dict), "policy must be an object")
    _require(
        set(policy)
        == {
            "schema_version",
            "kind",
            "metric",
            "aggregate_line_floor",
            "baseline",
            "packages",
            "empty_packages",
        },
        "unknown or missing policy fields",
    )
    _require(
        type(policy["schema_version"]) is int and policy["schema_version"] == 1,
        "unsupported policy schema",
    )
    _require(
        policy["kind"] == "package-line-coverage-floors" and policy["metric"] == "line",
        "policy must select line coverage",
    )
    floor = policy["aggregate_line_floor"]
    _require(type(floor) is int and 0 <= floor <= 100, "invalid aggregate line floor")
    _require(isinstance(policy["baseline"], dict), "missing baseline provenance")
    packages = policy["packages"]
    _require(isinstance(packages, dict) and bool(packages), "missing package floors")
    for name, entry in packages.items():
        _require(bool(_PACKAGE.fullmatch(name)), f"invalid policy package: {name}")
        _require(
            isinstance(entry, dict)
            and set(entry)
            == {
                "line_floor",
                "baseline_lines_covered",
                "baseline_lines_valid",
            },
            f"invalid package policy: {name}",
        )
        covered, valid, minimum = (
            entry["baseline_lines_covered"],
            entry["baseline_lines_valid"],
            entry["line_floor"],
        )
        _require(
            all(type(n) is int for n in (covered, valid, minimum))
            and 0 <= covered <= valid
            and valid > 0,
            f"invalid baseline counts: {name}",
        )
        _require(
            minimum == covered * 100 // valid,
            f"floor does not match measured whole-percent policy: {name}",
        )
    empty = policy["empty_packages"]
    _require(
        isinstance(empty, list) and all(isinstance(n, str) for n in empty),
        "invalid empty-package inventory",
    )
    _require(
        len(empty) == len(set(empty))
        and not set(empty) & set(packages)
        and all(_PACKAGE.fullmatch(n) for n in empty),
        "invalid empty-package inventory",
    )
    return policy


def _count(raw: str | None, label: str) -> int:
    _require(raw is not None and bool(_INTEGER.fullmatch(raw)), f"invalid {label}")
    return int(raw)  # type: ignore[arg-type]


def _rate(raw: str | None, covered: int, valid: int, label: str) -> None:
    _require(raw is not None and len(raw) <= 20, f"invalid {label} line-rate")
    try:
        rate = Decimal(raw)  # type: ignore[arg-type]
        exponent = rate.as_tuple().exponent
        if not rate.is_finite() or not isinstance(exponent, int):
            raise ValueError(f"invalid {label} line-rate")
        _require(0 <= rate <= 1 and -12 <= exponent <= 0, f"invalid {label} line-rate")
        expected = (Decimal(covered) / valid if valid else Decimal(1)).quantize(
            Decimal(1).scaleb(exponent)
        )
    except InvalidOperation as exc:
        raise ValueError(f"invalid {label} line-rate") from exc
    _require(rate == expected, f"{label} line-rate disagrees with counts")


def coverage_counts(data: bytes) -> dict[str, tuple[int, int]]:
    text = data.decode("utf-8")
    _require(
        "<!DOCTYPE" not in text and "<!ENTITY" not in text, "XML declarations forbidden"
    )
    root = ET.fromstring(text)
    _require(
        root.tag == "coverage" and len(root.findall("packages")) == 1,
        "unknown or missing coverage root/packages",
    )
    groups: dict[str, tuple[int, int]] = {}
    filenames: set[str] = set()
    for package in root.findall("./packages/package"):
        name = package.get("name", "")
        _require(
            bool(_PACKAGE.fullmatch(name)) and name not in groups,
            f"invalid or duplicate coverage package: {name}",
        )
        _require(len(package.findall("classes")) == 1, f"missing classes: {name}")
        covered = valid = 0
        classes = package.findall("./classes/class")
        _require(bool(classes), f"missing class inventory: {name}")
        for cls in classes:
            filename = cls.get("filename", "")
            path = PurePosixPath(filename)
            _require(
                bool(filename)
                and "\\" not in filename
                and not path.is_absolute()
                and ".." not in path.parts
                and str(path) == filename
                and path.parent.as_posix() == name.replace(".", "/")
                and path.suffix == ".py"
                and filename not in filenames,
                f"invalid or duplicate coverage filename: {filename}",
            )
            filenames.add(filename)
            _require(len(cls.findall("lines")) == 1, f"missing lines: {filename}")
            numbers: set[int] = set()
            file_covered = 0
            for line in cls.findall("./lines/line"):
                number = _count(line.get("number"), "line number")
                hits = _count(line.get("hits"), "line hit count")
                _require(
                    number > 0 and number not in numbers,
                    f"invalid or duplicate line number: {filename}:{number}",
                )
                numbers.add(number)
                file_covered += hits > 0
            _rate(cls.get("line-rate"), file_covered, len(numbers), filename)
            covered += file_covered
            valid += len(numbers)
        _rate(package.get("line-rate"), covered, valid, name)
        groups[name] = (covered, valid)
    total_covered = sum(c for c, _ in groups.values())
    total_valid = sum(v for _, v in groups.values())
    _require(total_valid > 0, "coverage contains no executable lines")
    _require(
        _count(root.get("lines-covered"), "covered lines") == total_covered
        and _count(root.get("lines-valid"), "valid lines") == total_valid,
        "aggregate line counts disagree with unique file records",
    )
    _rate(root.get("line-rate"), total_covered, total_valid, "aggregate")
    return groups


def evaluate(data: bytes, policy_data: bytes) -> dict[str, Any]:
    policy = load_policy(policy_data)
    counts = coverage_counts(data)
    expected = set(policy["packages"]) | set(policy["empty_packages"])
    _require(
        set(counts) == expected,
        f"package inventory differs: missing={sorted(expected - set(counts))}; "
        f"unexpected={sorted(set(counts) - expected)}",
    )
    violations: list[str] = []
    packages = []
    for name, (covered, valid) in sorted(counts.items()):
        if name in policy["empty_packages"]:
            _require(
                valid == 0, f"formerly empty package needs a measured floor: {name}"
            )
            packages.append(
                {
                    "package": name,
                    "covered": 0,
                    "valid": 0,
                    "floor": None,
                    "status": "empty-no-executable-lines",
                }
            )
            continue
        _require(valid > 0, f"configured package has no executable lines: {name}")
        floor = policy["packages"][name]["line_floor"]
        passed = covered * 100 >= valid * floor
        packages.append(
            {
                "package": name,
                "covered": covered,
                "valid": valid,
                "floor": floor,
                "status": "passed" if passed else "failed",
            }
        )
        if not passed:
            violations.append(f"{name}: {covered}/{valid} lines below {floor}%")
    covered, valid = (
        sum(c for c, _ in counts.values()),
        sum(v for _, v in counts.values()),
    )
    floor = policy["aggregate_line_floor"]
    passed = covered * 100 >= valid * floor
    if not passed:
        violations.append(f"aggregate: {covered}/{valid} lines below {floor}%")
    return {
        "schema_version": 1,
        "kind": "package-line-coverage-result",
        "metric": "line",
        "status": "failed" if violations else "passed",
        "aggregate": {
            "covered": covered,
            "valid": valid,
            "floor": floor,
            "passed": passed,
        },
        "packages": packages,
        "violations": violations,
        "coverage_sha256": hashlib.sha256(data).hexdigest(),
        "policy_sha256": hashlib.sha256(policy_data).hexdigest(),
        "scope": "Line coverage only; no branch-arc, native, production or scientific acceptance.",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage", type=Path, default=Path("coverage.xml"))
    parser.add_argument(
        "--policy", type=Path, default=PROJECT_ROOT / "docs/coverage-floors.json"
    )
    args = parser.parse_args(argv)
    try:
        result = evaluate(
            _read_regular(args.coverage, 8 * 1024 * 1024),
            _read_regular(args.policy, 64 * 1024),
        )
    except (OSError, ValueError, ET.ParseError, RecursionError) as exc:
        print(
            json.dumps({"status": "error", "failure_reason": str(exc)}, sort_keys=True)
        )
        return 1
    print(json.dumps(result, sort_keys=True))
    return int(result["status"] != "passed")


if __name__ == "__main__":
    raise SystemExit(main())
