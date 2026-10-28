"""Versioned native-only supplement; importing this module performs no I/O.

A source reference may be captured while automatic CI is active. It is never
release acceptance: join_release requires the exact terminal accepted automatic
profile and independently reviewed original supplement artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import io
import json
import os
import platform
import stat
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, cast

PROFILE = "native-api-cli-supplement-v1"
REPOSITORY = "ActiveInferenceInstitute/fep_formal"
REPOSITORY_ID = 1210503162
WORKFLOW_ID = 316419466
WORKFLOW_PATH = ".github/workflows/ci.yml"
PRODUCER = ("tests.test_catalogue_bodies_compile", "test_all_catalogue_bodies_compile")
ROLE_NAMES = {
    "changes",
    "static",
    "python",
    "render-deps",
    "lean",
    "render",
    "documentation",
} | {
    f"distribution ({system}, {version})"
    for system in ("ubuntu-latest", "macos-latest", "windows-latest")
    for version in ("3.10", "3.11", "3.12", "3.13", "3.14")
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def decode(raw: bytes) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    return json.loads(raw, object_pairs_hook=pairs)


def positive(value: Any) -> int:
    require(type(value) is int and value > 0, "positive integer identity required")
    return cast(int, value)


def commit(value: Any) -> str:
    require(
        isinstance(value, str)
        and len(value) == 40
        and all(c in "0123456789abcdef" for c in value),
        "exact commit required",
    )
    return cast(str, value)


def automatic_identity(
    run: dict[str, Any],
    *,
    run_id: int,
    attempt: int,
    pr_number: int,
    candidate: str,
    base: str,
    terminal: bool = False,
) -> None:
    require(
        run["repository"]["full_name"] == REPOSITORY
        and run["repository"]["id"] == REPOSITORY_ID,
        "wrong repository",
    )
    require(
        run["workflow_id"] == WORKFLOW_ID
        and run["path"].split("@", 1)[0] == WORKFLOW_PATH,
        "wrong workflow",
    )
    require(
        run["id"] == positive(run_id) and run["run_attempt"] == positive(attempt),
        "wrong run or attempt",
    )
    require(
        run["event"] == "pull_request" and run["head_sha"] == commit(candidate),
        "wrong automatic event/head",
    )
    require(len(run["pull_requests"]) == 1, "one exact PR association required")
    pr = run["pull_requests"][0]
    require(
        pr["number"] == positive(pr_number)
        and pr["head"]["sha"] == candidate
        and pr["base"]["sha"] == commit(base),
        "wrong PR/base/head",
    )
    require(
        pr["head"]["repo"]["id"] == pr["base"]["repo"]["id"] == REPOSITORY_ID,
        "foreign PR repository",
    )
    if terminal:
        require(
            run["status"] == "completed" and run["conclusion"] == "success",
            "automatic run not terminal successful",
        )
    else:
        require(
            run["status"]
            in {
                "queued",
                "in_progress",
                "requested",
                "waiting",
                "pending",
                "completed",
            },
            "unknown automatic state",
        )
        require(
            run["conclusion"] is None
            or (run["status"] == "completed" and run["conclusion"] == "success"),
            "failed prior automatic reference",
        )


def merge_identity(
    merge: dict[str, Any], *, candidate: str, base: str, checkout: str, tree: str
) -> None:
    require(merge["sha"] == commit(checkout), "wrong synthetic checkout")
    require(
        [p["sha"] for p in merge["parents"]] == [commit(base), commit(candidate)],
        "wrong ordered synthetic parents",
    )
    require(merge["tree"]["sha"] == commit(tree), "synthetic/candidate trees differ")
    require(checkout not in {candidate, base}, "synthetic execution must stay distinct")


def producer_case(raw: bytes) -> None:
    import xml.etree.ElementTree as ET

    cases = list(ET.fromstring(raw).iter("testcase"))
    require(
        len(cases) == 1,
        "supplement is exactly one producer node, not a full serial suite",
    )
    node = cases[0]
    require(
        (node.get("classname"), node.get("name")) == PRODUCER, "wrong producer node"
    )
    require(
        all(node.find(tag) is None for tag in ("skipped", "failure", "error")),
        "producer must actually pass once",
    )


def nonduration(payload: dict[str, Any]) -> dict[str, Any]:
    # This is exactly the existing shadow comparison exclusion: only measured
    # top-level/row duration_s. Unknown fields, paths, status and retry data stay.
    return {
        key: (
            [{k: v for k, v in row.items() if k != "duration_s"} for row in value]
            if key == "results"
            else value
        )
        for key, value in payload.items()
        if key != "duration_s"
    }


def original_zip(
    raw: bytes,
    artifact: dict[str, Any],
    *,
    run_id: int,
    attempt: int,
    candidate: str,
    reference: dict[str, Any],
) -> dict[str, bytes]:
    positive(artifact["id"])
    require(
        artifact["name"] == f"{PROFILE}-{positive(run_id)}-{positive(attempt)}",
        "wrong artifact name/attempt",
    )
    require(
        artifact["expired"] is False and artifact["size_in_bytes"] == len(raw) > 0,
        "artifact unavailable/size changed",
    )
    require(
        artifact["digest"] == "sha256:" + sha(raw),
        "original ZIP digest mismatch or repack",
    )
    workflow = artifact["workflow_run"]
    require(
        workflow["id"] == run_id and workflow["head_sha"] == commit(candidate),
        "wrong artifact source/run",
    )
    require(
        workflow["repository_id"] == workflow["head_repository_id"] == REPOSITORY_ID,
        "wrong artifact repository",
    )
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        rows = archive.infolist()
        names = [r.filename for r in rows]
        require(len(names) == len(set(names)), "duplicate ZIP member")
        require(
            sum(r.file_size for r in rows) <= 64_000_000, "oversized supplement archive"
        )
        for row in rows:
            require(
                not row.is_dir()
                and Path(row.filename).name == row.filename
                and "\\" not in row.filename
                and row.filename not in {".", ".."},
                "flat regular artifact members required",
            )
            require(
                stat.S_IFMT(row.external_attr >> 16) in {0, stat.S_IFREG},
                "nonregular artifact member refused",
            )
        files = {r.filename: archive.read(r) for r in rows}
    receipt = decode(files["receipt.json"])
    require(
        receipt["profile"] == PROFILE
        and receipt["schema_version"] == 1
        and receipt["passed"] is True
        and receipt["complete"] is True,
        "unfinished native supplement",
    )
    require(
        receipt["head"] == candidate
        and receipt["run_id"] == run_id
        and receipt["run_attempt"] == attempt,
        "receipt/artifact epoch mismatch",
    )
    require(
        receipt["release_qualified"] is False
        and receipt["producer_cases"] == 1
        and receipt["api_topics"] == receipt["cli_topics"] == 168,
        "wrong supplement scope",
    )
    require(
        set(files) == set(receipt["files_sha256"]) | {"receipt.json"},
        "artifact roster differs from receipt",
    )
    require(
        all(
            sha(files[name]) == digest
            for name, digest in receipt["files_sha256"].items()
        ),
        "artifact member changed",
    )
    required = {
        "reference.json",
        "api-native.json",
        "cli-native.json",
        "producer.intent.json",
        "producer.json",
        "producer.xml",
        "api.stdout.log",
        "api.stderr.log",
        "cli.stdout.log",
        "cli.stderr.log",
        "api.exitcode",
        "cli.exitcode",
        "source-before.json",
        "source-after.json",
        "runtime-before.json",
        "runtime-after.json",
        "native-outcomes.json",
    }
    require(required <= set(files), "mandatory raw supplement evidence missing")
    require(
        receipt["reference"] == decode(files["reference.json"]) == reference,
        "artifact reference differs from approved join",
    )
    require(
        (reference["supplement_run_id"], reference["supplement_run_attempt"])
        == (run_id, attempt),
        "supplement identity differs from reference",
    )
    producer_case(files["producer.xml"])
    require(
        files["api.exitcode"] == files["cli.exitcode"] == b"0\n",
        "native command failed",
    )
    require(
        nonduration(decode(files["api-native.json"]))
        == nonduration(decode(files["cli-native.json"])),
        "API/CLI nonduration mismatch",
    )
    require(
        files["source-before.json"] == files["source-after.json"]
        and files["runtime-before.json"] == files["runtime-after.json"],
        "source/runtime changed",
    )
    return files


def join_release(
    reference: dict[str, Any],
    terminal: dict[str, Any],
    automatic_validation_raw: bytes,
    automatic_acceptance_raw: bytes,
    automatic_review_raw: bytes,
    supplement_validation_raw: bytes,
    supplement_review_raw: bytes,
) -> dict[str, Any]:
    """Join already independently validated full and native-only executions.

    The caller must authenticate the closed full-profile validator, all five
    original automatic ZIPs and PDF review, and the independent native bundle
    replay (both production validators at candidate bytes). No merely successful
    Actions conclusion, declared count or label substitutes for those reviews.
    """
    require(
        reference["schema_version"] == 1 and reference["profile"] == PROFILE,
        "unsupported reference profile",
    )
    automatic_identity(
        terminal,
        run_id=reference["automatic_run_id"],
        attempt=reference["automatic_run_attempt"],
        pr_number=reference["pr_number"],
        candidate=reference["candidate"],
        base=reference["base"],
        terminal=True,
    )
    a = decode(automatic_acceptance_raw)
    r = decode(automatic_review_raw)
    v = decode(automatic_validation_raw)
    s = decode(supplement_validation_raw)
    sr = decode(supplement_review_raw)
    require(
        a["passed"] is True
        and a["complete"] is True
        and a["head"] == reference["candidate"],
        "automatic acceptance missing",
    )
    require(
        (a["run_id"], a["run_attempt"])
        == (reference["automatic_run_id"], reference["automatic_run_attempt"]),
        "accepted automatic run differs from dispatch reference",
    )
    require(
        a["validation_sha256"] == sha(automatic_validation_raw)
        and a["PDF_scoped_acceptance"] is True,
        "automatic full validation/PDF not accepted",
    )
    require(
        r["passed"] is True
        and r["complete"] is True
        and r["head"] == a["head"]
        and r["acceptance_sha256"] == sha(automatic_acceptance_raw),
        "automatic independent review missing",
    )
    require(
        v["supplement_join_schema"] == "full-automatic-source-projection-v1",
        "versioned full-profile source projection required",
    )
    require(
        v["profile"] == "pull_request"
        and v["run_id"] == a["run_id"]
        and v["run_attempt"] == a["run_attempt"],
        "wrong full automatic profile",
    )
    require(
        v["state"]
        == "FULL_PROFILE_AND_ACTUAL_CAPTURED_CONSUMER_VALIDATED_PDF_ACCEPTANCE_PENDING",
        "full automatic validator did not pass",
    )
    require(
        v["head"] == reference["candidate"]
        and v["artifact_commit"]
        == v["captured_checkout_commit"]
        == reference["automatic_checkout"],
        "actual automatic checkout differs from frozen reference",
    )
    require(
        v["synthetic_parents"] == [reference["base"], reference["candidate"]]
        and v["source_tree"] == reference["tree"],
        "automatic parent/tree association missing",
    )
    require(
        v["workflow_sha256"] == reference["workflow_sha256"]
        and v["artifact_roster"]["total_count"]
        == len(v["artifact_roster"]["artifacts"])
        == 5,
        "workflow/artifact policy differs",
    )
    require(
        len(v["jobs"]) == 22 and {j["name"] for j in v["jobs"]} == ROLE_NAMES,
        "full22/15 required",
    )
    require(
        all(
            j["status"] == "completed"
            and j["conclusion"]
            == ("skipped" if j["name"] == "documentation" else "success")
            for j in v["jobs"]
        ),
        "automatic required job failed/skipped",
    )
    require(
        not v["audit_defects"]
        and not v["render_defects"]
        and v["native_validation"]["native_claim_ready"] is True
        and v["native_validation"]["verified_topics"] == 168,
        "automatic native/render gate failed",
    )
    require(
        s["passed"] is True
        and s["complete"] is True
        and s["profile"] == PROFILE
        and s["head"] == reference["candidate"],
        "native supplement not independently replayed",
    )
    require(
        (s["run_id"], s["run_attempt"])
        == (reference["supplement_run_id"], reference["supplement_run_attempt"]),
        "wrong supplement execution",
    )
    require(
        s["reference"] == reference
        and s["producer_cases"] == 1
        and s["api_topics"] == s["cli_topics"] == 168
        and s["nonduration_equal"] is True,
        "supplement source/reference/producer mismatch",
    )
    require(
        s["original_zip_verified"] is True
        and s["production_api_source_bound"] is True
        and s["production_cli_source_bound"] is True
        and s["runtime_unchanged"] is True,
        "supplement custody/source/runtime incomplete",
    )
    require(
        sr["passed"] is True
        and sr["complete"] is True
        and sr["head"] == s["head"]
        and sr["qualification_sha256"] == sha(supplement_validation_raw),
        "supplement independent review missing",
    )
    return {
        "passed": True,
        "profile": "full-automatic-pr-plus-native-supplement-v1",
        "head": reference["candidate"],
        "automatic_checkout": reference["automatic_checkout"],
        "automatic_run_id": a["run_id"],
        "automatic_run_attempt": a["run_attempt"],
        "supplement_run_id": s["run_id"],
        "supplement_run_attempt": s["run_attempt"],
        "automatic_acceptance_sha256": sha(automatic_acceptance_raw),
        "supplement_validation_sha256": sha(supplement_validation_raw),
        "boundary": "Full automatic PR and independently replayed native-only supplement joined. Supplement is one producer plus ordinary CLI, never a full serial/Python/wheel/render run. Fresh merged-main full profile/PDF remains mandatory.",
    }


def git(root: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        GIT_OPTIONAL_LOCKS="0",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_SYSTEM=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_NO_REPLACE_OBJECTS="1",
        GIT_CONFIG_COUNT="2",
        GIT_CONFIG_KEY_0="maintenance.auto",
        GIT_CONFIG_VALUE_0="false",
        GIT_CONFIG_KEY_1="gc.auto",
        GIT_CONFIG_VALUE_1="0",
    )
    return subprocess.check_output(
        ["git", *args],
        cwd=root,
        env=env,
        stdin=subprocess.DEVNULL,
        text=True,
        timeout=30,
    ).strip()


def source_snapshot(root: Path) -> dict[str, Any]:
    require(
        not git(root, "status", "--porcelain", "--untracked-files=all"),
        "tracked/untracked source dirty",
    )
    rows: dict[str, Any] = {}
    for record in git(root, "ls-files", "--stage", "-z").split("\0"):
        if not record:
            continue
        entry, name = record.split("\t", 1)
        mode, blob, stage = entry.split()
        require(
            stage == "0" and mode in {"100644", "100755", "120000"},
            "unmerged/gitlink source refused",
        )
        path = root / name
        raw = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
        rows[name] = {"mode": mode, "blob": blob, "sha256": sha(raw)}
    return rows


def runtime_snapshot(root: Path) -> dict[str, Any]:
    import fep_formal

    require(
        Path(fep_formal.__file__).resolve().is_relative_to(root / "src"),
        "foreign FEP import",
    )
    metadata = []
    for d in importlib.metadata.distributions():
        path = Path(
            str(cast(Any, d)._path)
        )  # Actual dist-info and source egg-info remain distinct.
        metadata.append(
            {
                "name": d.metadata["Name"],
                "version": d.version,
                "path": str(path),
                "files": {
                    str(p.relative_to(path)): sha(p.read_bytes())
                    for p in path.rglob("*")
                    if p.is_file()
                },
            }
        )
    prefix = Path(sys.prefix)
    files = {
        str(p): sha(p.read_bytes())
        for folder in (prefix / "bin",)
        for p in folder.iterdir()
        if p.is_file()
    }
    for folder in prefix.glob("lib/python*/site-packages"):
        files.update(
            {str(p): sha(p.read_bytes()) for p in folder.glob("*.pth") if p.is_file()}
        )
    packages = decode((root / "lean/lake-manifest.json").read_bytes())["packages"]
    require(len(packages) == 9, "physical package roster changed")
    pins = {
        r["name"]: git(root / "lean/.lake/packages" / r["name"], "rev-parse", "HEAD")
        for r in packages
    }
    require(
        all(pins[r["name"]] == r["rev"] for r in packages),
        "physical package pin differs",
    )
    tools = {}
    for name in ("lean", "lake"):
        path = Path(
            subprocess.check_output(
                ["elan", "which", name],
                cwd=root / "lean",
                stdin=subprocess.DEVNULL,
                text=True,
                timeout=30,
            ).strip()
        ).resolve(strict=True)
        tools[name] = {"path": str(path), "sha256": sha(path.read_bytes())}
    return {
        "python": sys.version,
        "executable": str(Path(sys.executable).resolve()),
        "executable_sha256": sha(Path(sys.executable).read_bytes()),
        "prefix": sys.prefix,
        "platform": platform.platform(),
        "fep_origin": str(Path(fep_formal.__file__).resolve()),
        "distributions": sorted(metadata, key=lambda d: (d["name"], d["path"])),
        "runtime_files": files,
        "toolchain": (root / "lean/lean-toolchain").read_text(),
        "tools": tools,
        "physical_packages": pins,
    }


def write(path: Path, value: Any) -> None:
    with path.open("x") as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2) + "\n")


def api(path: str, dest: Path) -> dict[str, Any]:
    require(
        os.environ["GITHUB_REPOSITORY"] == REPOSITORY
        and os.environ["GITHUB_API_URL"] == "https://api.github.com",
        "wrong Actions API host/repository",
    )
    request = urllib.request.Request(
        "https://api.github.com/repos/" + REPOSITORY + path,
        headers={
            "Authorization": "Bearer " + os.environ["GH_TOKEN"],
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read(8_000_001)
    require(len(raw) <= 8_000_000, "oversized Actions metadata")
    with dest.open("xb") as stream:
        stream.write(raw)
    payload = decode(raw)
    require(isinstance(payload, dict), "Actions metadata object required")
    return cast(dict[str, Any], payload)


def capture(
    root: Path, output: Path, run_id: int, attempt: int, pr_number: int
) -> None:
    require(
        os.environ["GITHUB_EVENT_NAME"] == "workflow_dispatch",
        "explicit dispatch profile required",
    )
    event = decode(Path(os.environ["GITHUB_EVENT_PATH"]).read_bytes())
    require(
        event["inputs"]["native_supplement_profile"] == PROFILE,
        "supplement profile required",
    )
    require(
        event["inputs"]["run_lean"] in (True, "true")
        and event["inputs"].get("native_producer_shadow", "false") in (False, "false"),
        "supplement must enable native; debug shadow disabled",
    )
    candidate = commit(git(root, "rev-parse", "HEAD"))
    tree = commit(git(root, "rev-parse", "HEAD^{tree}"))
    require(
        candidate == os.environ["GITHUB_SHA"] == os.environ["GITHUB_WORKFLOW_SHA"],
        "dispatch source/workflow checkout mismatch",
    )
    require(not output.exists(), "fresh supplement output required")
    output.mkdir(parents=True, mode=0o700)
    own = api(
        "/actions/runs/" + os.environ["GITHUB_RUN_ID"],
        output / "supplement-run.original.json",
    )
    require(
        own["event"] == "workflow_dispatch"
        and own["head_sha"] == candidate
        and own["workflow_id"] == WORKFLOW_ID
        and own["run_attempt"] == int(os.environ["GITHUB_RUN_ATTEMPT"]),
        "wrong supplement run",
    )
    run = api(f"/actions/runs/{run_id}", output / "automatic-run.original.json")
    require(run_id != own["id"], "automatic reference cannot be this dispatch")
    require(len(run["pull_requests"]) == 1, "one exact automatic PR required")
    base = commit(run["pull_requests"][0]["base"]["sha"])
    automatic_identity(
        run,
        run_id=run_id,
        attempt=attempt,
        pr_number=pr_number,
        candidate=candidate,
        base=base,
    )
    pr = api(f"/pulls/{pr_number}", output / "automatic-pr.original.json")
    require(
        pr["head"]["sha"] == candidate
        and pr["base"]["sha"] == base
        and pr["state"] == "open",
        "PR changed since referenced run",
    )
    checkout = commit(pr["merge_commit_sha"])
    merge = api("/git/commits/" + checkout, output / "automatic-merge.original.json")
    merge_identity(merge, candidate=candidate, base=base, checkout=checkout, tree=tree)
    workflow = api(
        f"/actions/workflows/{WORKFLOW_ID}", output / "workflow.original.json"
    )
    require(
        workflow["path"] == WORKFLOW_PATH and workflow["state"] == "active",
        "wrong workflow definition",
    )
    reference = {
        "schema_version": 1,
        "profile": PROFILE,
        "repository": REPOSITORY,
        "repository_id": REPOSITORY_ID,
        "workflow_id": WORKFLOW_ID,
        "workflow_path": WORKFLOW_PATH,
        "workflow_sha256": sha((root / WORKFLOW_PATH).read_bytes()),
        "candidate": candidate,
        "base": base,
        "tree": tree,
        "automatic_checkout": checkout,
        "automatic_run_id": run_id,
        "automatic_run_attempt": attempt,
        "pr_number": pr_number,
        "supplement_run_id": positive(own["id"]),
        "supplement_run_attempt": positive(own["run_attempt"]),
        "reference_is_acceptance": False,
    }
    write(output / "reference.json", reference)


def start(root: Path, output: Path) -> None:
    reference = decode((output / "reference.json").read_bytes())
    require(
        git(root, "rev-parse", "HEAD") == reference["candidate"],
        "source changed before native work",
    )
    write(output / "source-before.json", source_snapshot(root))
    write(output / "runtime-before.json", runtime_snapshot(root))


def native_validators(root: Path, source_before: dict[str, Any]) -> tuple[Any, Any]:
    """Import checkout-local validators from the explicitly bound repository root."""
    require(
        root == Path(__file__).resolve(strict=True).parents[2],
        "helper/repository root differs",
    )
    modules = (
        "tests",
        "tests._support",
        "tests._support.native_catalogue_gate",
        "tests._support.native_catalogue_shadow",
    )
    expected = {}
    for name in modules:
        relative = name.replace(".", "/") + (
            "/__init__.py" if name in modules[:2] else ".py"
        )
        path = root / relative
        require(
            path.is_file()
            and not path.is_symlink()
            and path.resolve(strict=True) == path,
            "validator regular checkout source required",
        )
        require(
            source_before[relative]["sha256"] == sha(path.read_bytes()),
            "validator source changed before import",
        )
        expected[name] = path
        if name in sys.modules:
            module_file = sys.modules[name].__file__
            require(isinstance(module_file, str), "validator module file missing")
            require(
                Path(cast(str, module_file)).resolve(strict=True) == path,
                "foreign preloaded validator module",
            )
    sys.path.insert(0, str(root))
    importlib.invalidate_caches()
    loaded = {name: importlib.import_module(name) for name in modules}
    require(
        all(
            isinstance(module_file := loaded[name].__file__, str)
            and Path(module_file).resolve(strict=True) == path
            for name, path in expected.items()
        ),
        "foreign validator import origin",
    )
    return loaded[modules[2]].validate_native_catalogue_producer, loaded[
        modules[3]
    ].compare_native_catalogue_receipts


def finalize(root: Path, output: Path) -> None:
    validate_native_catalogue_producer, compare_native_catalogue_receipts = (
        native_validators(root, decode((output / "source-before.json").read_bytes()))
    )
    reference = decode((output / "reference.json").read_bytes())
    require(
        git(root, "rev-parse", "HEAD") == reference["candidate"],
        "native source epoch changed",
    )
    require(
        (output / "api.exitcode").read_bytes()
        == (output / "cli.exitcode").read_bytes()
        == b"0\n",
        "native command failed",
    )
    producer_case((root / "output/native-supplement-producer.xml").read_bytes())
    producer = validate_native_catalogue_producer(
        root, junit=root / "output/native-supplement-producer.xml"
    )
    comparison = compare_native_catalogue_receipts(
        root,
        root / "output/native-verification.json",
        root / "output/native-supplement-cli.json",
        run_id=str(reference["supplement_run_id"]),
        attempt=str(reference["supplement_run_attempt"]),
        commit=reference["candidate"],
    )
    require(
        producer["producer_node_passed_exactly_once"] is True
        and len(comparison["topic_ids"]) == 168,
        "producer scope differs",
    )
    write(output / "source-after.json", source_snapshot(root))
    write(output / "runtime-after.json", runtime_snapshot(root))
    require(
        (output / "source-before.json").read_bytes()
        == (output / "source-after.json").read_bytes()
        and (output / "runtime-before.json").read_bytes()
        == (output / "runtime-after.json").read_bytes(),
        "source/runtime changed across executions",
    )
    post = api(
        f"/actions/runs/{reference['automatic_run_id']}",
        output / "automatic-run-final.original.json",
    )
    # A failed/cancelled concurrent full run is retained as a fact; it can never
    # qualify release. Do not turn native work into a wait for terminal full CI.
    require(
        post["id"] == reference["automatic_run_id"]
        and post["run_attempt"] == reference["automatic_run_attempt"]
        and post["head_sha"] == reference["candidate"]
        and post["workflow_id"] == WORKFLOW_ID,
        "automatic reference changed/reran",
    )
    for name, source in {
        "api-native.json": "output/native-verification.json",
        "cli-native.json": "output/native-supplement-cli.json",
        "producer.intent.json": "output/native-catalogue-producer.intent.json",
        "producer.json": "output/native-catalogue-producer.json",
        "producer.xml": "output/native-supplement-producer.xml",
    }.items():
        p = root / source
        require(
            p.is_file() and not p.is_symlink(), "regular original evidence required"
        )
        (output / name).write_bytes(p.read_bytes())
    write(
        output / "native-outcomes.json",
        {"producer": producer, "comparison": comparison},
    )
    files = {
        p.name: sha(p.read_bytes())
        for p in output.iterdir()
        if p.is_file() and not p.is_symlink()
    }
    require(
        len(files) == len(list(output.iterdir())), "unexpected evidence directory/link"
    )
    write(
        output / "receipt.json",
        {
            "schema_version": 1,
            "profile": PROFILE,
            "head": reference["candidate"],
            "run_id": reference["supplement_run_id"],
            "run_attempt": reference["supplement_run_attempt"],
            "passed": True,
            "complete": True,
            "release_qualified": False,
            "producer_cases": 1,
            "api_topics": 168,
            "cli_topics": 168,
            "reference": reference,
            "files_sha256": files,
            "boundary": "Native-only actual API+ordinary CLI. Reference may still be in progress or may fail; exact independently accepted terminal full automatic22/15/PDF is separately mandatory. No640/wholePython/wheel/render execution claim.",
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("capture", "start", "finalize"))
    parser.add_argument("--automatic-run-id", type=int)
    parser.add_argument("--automatic-run-attempt", type=int)
    parser.add_argument("--pr-number", type=int)
    parser.add_argument("--repository-root", type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    root = Path.cwd().resolve(strict=True)
    output = root / "output/native-supplement-v1"
    if args.mode == "capture":
        capture(
            root,
            output,
            positive(args.automatic_run_id),
            positive(args.automatic_run_attempt),
            positive(args.pr_number),
        )
    elif args.mode == "start":
        start(root, output)
    else:
        require(
            args.repository_root is not None
            and args.repository_root.resolve(strict=True) == root,
            "explicit repository root must equal working directory",
        )
        finalize(root, output)


if __name__ == "__main__":
    main()
