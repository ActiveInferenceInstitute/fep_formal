"""Supplement the frozen distribution matrix with actual portable methods use.

The harness runs in the accepted validator environment. Only the isolated
installed wheel uses FEP_DISTRIBUTION_PYTHON (or that validator by default).
These checks establish Python/package behavior, never native or science proof.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[2]
PRODUCTS = {
    "positioning.json",
    "positioning.md",
    "visual-model.json",
    "mathematical-map.html",
    "panels/family-domains.svg",
    "panels/semantic-layers.svg",
    "panels/support-convergence.svg",
    "panels/fisher-geometry.svg",
    "panels/hidden-projection.svg",
    "panels/risk-preference.svg",
    "panels/authored-relations.svg",
    "panels/authored-relations-formal.svg",
    "panels/authored-relations-formal-pairing.svg",
    "panels/authored-relations-conceptual.svg",
    "panels/cross-corpus-embedding.svg",
    "panels/cross-corpus-features.svg",
    "panels/theorem-contracts.svg",
}


def _snapshot(root: Path) -> dict[str, tuple[str, int]]:
    return {
        path.relative_to(root).as_posix(): (
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.stat().st_mtime_ns,
        )
        for path in root.rglob("*")
        if path.is_file()
    }


def test_target_interpreter_installed_methods_api_cli_and_full_visual_export(tmp_path):
    """Install a real wheel outside the checkout and retain exact origin/scope."""
    uv = shutil.which("uv")
    assert uv is not None, "the validator contract requires uv"
    expected_version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"][
        "version"
    ]
    target_python = os.environ.get("FEP_DISTRIBUTION_PYTHON", sys.executable)
    clean_env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"}
        and not key.startswith(("FEP_FORMAL_", "FEP_LEAN_"))
    }
    dist = tmp_path / "dist"
    subprocess.run(
        [uv, "build", "--out-dir", str(dist)],
        cwd=ROOT,
        env=clean_env,
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(dist.glob("fep_formal-*.whl"))
    assert len(wheels) == 1
    environment = tmp_path / "venv"
    subprocess.run(
        [uv, "venv", "--python", target_python, str(environment)],
        cwd=tmp_path,
        env=clean_env,
        check=True,
        capture_output=True,
        text=True,
    )
    scripts = environment / ("Scripts" if os.name == "nt" else "bin")
    python = scripts / ("python.exe" if os.name == "nt" else "python")
    console = scripts / ("fep-formal.exe" if os.name == "nt" else "fep-formal")
    subprocess.run(
        [uv, "pip", "install", "--python", str(python), str(wheels[0])],
        cwd=tmp_path,
        env=clean_env,
        check=True,
        capture_output=True,
        text=True,
    )
    api_output, cli_output = tmp_path / "api-export", tmp_path / "cli-export"
    probe = f"""
import hashlib, importlib.metadata, json, math, pathlib, sys
import fep_formal
from fep_formal.methods import (
    SourceOrigin, analyze_topic, bernoulli_fisher, build_mathematical_positioning,
    cross_corpus_embedding, inspect_theorem,
    evaluate_boundary_probes, export_mathematical_positioning, extended_kl,
    finite_kl_totalized, inspect_family, inspect_topic,
    mathematical_positioning_drift, positioning_neighbors,
)
assert pathlib.Path(fep_formal.__file__).is_relative_to(pathlib.Path({str(environment)!r}))
assert not any(p and pathlib.Path(p).is_relative_to(pathlib.Path({str(ROOT)!r})) for p in sys.path)
assert not any(name == 'src' or name.startswith('src.') for name in sys.modules)
assert fep_formal.__version__ == importlib.metadata.version('fep_formal') == {expected_version!r}
model = build_mathematical_positioning()
data = model.as_dict()
assert model.origin is SourceOrigin.INSTALLED_PACKAGE
assert data['source_origin'] == 'installed_package'
assert data['package_version'] == {expected_version!r}
assert data['counts']['topics'] == len(model.metadata.topic_ids) == 168
assert data['counts']['families'] == 22
assert data['counts']['authored_edges'] == 156
assert data['counts']['capabilities'] == 50
assert inspect_topic(model, 'fep-038')['primary_theorem_qualified'].startswith('fep_fep038.FEP038.')
analysis = analyze_topic(model, 'fep-038')
assert analysis['primary']['conclusion'] == 'fep038_fisherInformation p = 1 / (p * (1 - p))'
assert inspect_theorem(model, analysis['primary']['qualified_name']) == analysis['primary']
assert len(cross_corpus_embedding(model)['rows']) == 34
family = inspect_family(model, 'core-information-geometry')
assert 'fep-038' in family['topic_ids']
assert positioning_neighbors(model, family['family'], 3)
assert len(evaluate_boundary_probes()) == 4
assert bernoulli_fisher(0.5) == 4
assert finite_kl_totalized((1, 0), (0, 1)) == 1
assert extended_kl((1, 0), (0, 1)) == math.inf
assert all(not pathlib.Path(name).is_absolute() for name in data['source_sha256'])
root = pathlib.Path({str(api_output)!r})
paths = export_mathematical_positioning(model, root)
assert {{p.relative_to(root).as_posix() for p in paths}} == {PRODUCTS!r}
before = {{p.relative_to(root).as_posix(): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
          for p in root.rglob('*') if p.is_file()}}
assert mathematical_positioning_drift(model, root) == ()
after = {{p.relative_to(root).as_posix(): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
         for p in root.rglob('*') if p.is_file()}}
assert before == after
mds_json = json.dumps(cross_corpus_embedding(model)['projection'], sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode() + bytes([10])
mds_sha256 = hashlib.sha256(mds_json).hexdigest()
print(json.dumps({{'runtime':sys.version.split()[0], 'version':data['package_version'],
                  'origin':data['source_origin'], 'artifacts':len(paths),
                  'mds_projection_sha256':mds_sha256}}))
"""
    result = subprocess.run(
        [str(python), "-I", "-c", probe],
        cwd=tmp_path,
        env=clean_env,
        check=True,
        capture_output=True,
        text=True,
    )
    evidence = json.loads(result.stdout)
    assert evidence["version"] == expected_version
    assert evidence["origin"] == "installed_package"
    assert evidence["artifacts"] == len(PRODUCTS) == 17
    assert len(evidence["mds_projection_sha256"]) == 64
    print("portable methods installed wheel:", json.dumps(evidence, sort_keys=True))

    def cli(*arguments: str) -> dict:
        completed = subprocess.run(
            [str(console), "methods", *arguments],
            cwd=tmp_path,
            env=clean_env,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        assert payload["status"] == "ok"
        assert payload["package_version"] == expected_version
        assert payload["source_origin"] == "installed_package"
        return payload

    assert cli("inspect", "--topic", "fep-038")["result"]["id"] == "fep-038"
    analysis = cli("analyze", "fep-038")["result"]
    assert (
        analysis["primary"]["qualified_name"]
        == "fep_fep038.FEP038.fep038_fisherInformation_eq"
    )
    assert (
        cli("theorem", analysis["primary"]["qualified_name"])["result"]
        == analysis["primary"]
    )
    assert len(cli("embedding")["result"]["rows"]) == 34
    export = cli("export", "--output-root", str(cli_output))
    assert len(export["result"]["artifacts"]) == len(PRODUCTS)
    api_snapshot, cli_snapshot = _snapshot(api_output), _snapshot(cli_output)
    assert set(api_snapshot) == set(cli_snapshot) == PRODUCTS
    assert {key: value[0] for key, value in api_snapshot.items()} == {
        key: value[0] for key, value in cli_snapshot.items()
    }
    assert cli("check", "--output-root", str(api_output))["result"]["fresh"] is True
    assert cli("check", "--output-root", str(cli_output))["result"]["fresh"] is True
    assert _snapshot(api_output) == api_snapshot
    assert _snapshot(cli_output) == cli_snapshot
