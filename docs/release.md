# Release procedure

A versioned release is a tagged, hosted-CI-green `main` commit with one
consistent version. The gate is short on purpose: it checks what a release
actually ships, and it is fully checked by
[`docs/release_check.py`](release_check.py).

## Release gate

| Requirement | Checked by |
| --- | --- |
| One version across `pyproject.toml`, `compat/fep-lean/pyproject.toml` (including its dependency/extras), `src/fep_formal/__init__.py`, `CITATION.cff`, `manuscript/config.yaml`, `config/settings.yaml`, `.aii/config.yaml`, `uv.lock` and the release-bundle constants | `release_check.py` |
| One release date across `CITATION.cff`, `manuscript/config.yaml`, `.aii/config.yaml` and the release-bundle constants | `release_check.py` |
| A `## X.Y.Z — YYYY-MM-DD — title` section in `CHANGELOG.md` | `release_check.py` |
| Clean working tree; `HEAD` equals `origin/main` | `release_check.py --hosted` |
| The newest hosted `ci.yml` run on that exact commit succeeded, and its `python`, `static`, `lean`, `render-deps`, `render` and every `distribution` matrix job each succeeded (none skipped) | `release_check.py --hosted` |

## Published coordinated 2.1.0 checkpoint

[FEP_Formal 2.1.0](https://github.com/ActiveInferenceInstitute/fep_formal/releases/tag/v2.1.0)
and [GNN 5.0.1](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/releases/tag/v5.0.1)
are published; [GEO-INFER 0.4.0](https://github.com/ActiveInferenceInstitute/GEO_INFER/releases/tag/v0.4.0)
links those exact releases. FEP's accepted source remains
`96bf714d91c088e79b9dea54af0f9151f70de64f`, tree
`15af656a15fc86b6d89804277ea030502a4f9168`, annotated tag object
`6bc61ffa58428190055245781328820c7c86abac`.

A later joint candidate still requires current-source bridge/Q7 refresh,
fresh native qualification for its actual source pair, GNN's final companion
pin and repository gates. Numerical audits, source custody and native proof
retain separate scopes. Do not relabel a published receipt for a later source;
preserve historical DOI, tag and artifact identities.

## What does not block a release

Research and evidence lanes stay in [`TODO.md`](../TODO.md) with their own
acceptance probes. They are reported honestly in release notes, never claimed:

- the frozen H3 study (export, single primary run, outcome reviews);
- full seven-stage publication capture and two-archive parity;
- additional runtime investigations and read-only status controls beyond the
  required installed-wheel matrix;
- Q7 generated-runner execution and GNN bridge work;
- optional provider (Hermes/OpenGauss) runs;
- the nine-criterion closure audit.

A release changes no scientific claim. Unrun lanes stay described as unrun.

## Steps

1. Bump with
   `uv run python docs/release_check.py --bump X.Y.Z --date YYYY-MM-DD`. It
   rewrites the version and date in every file listed above plus the
   InstituteOS sidecar (`.aii/config.yaml`: `meta.updated` and the
   `Release vX.Y.Z (date; ...)` description, which must be reworded by hand if
   the release is not yet tagged). Then add the dated `CHANGELOG.md` section
   and run the printed `uv lock` (the bump never touches `uv.lock` or the
   changelog).
2. `uv run python docs/release_check.py` — fix every reported mismatch.
3. Run the local suite and audits (see [development](development.md)), commit
   and push to `main`.
4. Wait for hosted CI on that commit, then
   `uv run python docs/release_check.py --hosted --notes output/release-notes.md`.
5. Build both distributions from the same commit. The canonical wheel owns
   the implementation, import adapter and both commands; the deprecated
   compatibility wheel owns metadata only. The version gate checks their
   versions and exact dependency/extras pins together.

   ```bash
   uv build
   (cd compat/fep-lean && uv build --out-dir ../../dist)
   ```
6. Tag and publish:

   ```bash
   git tag -a vX.Y.Z -m "FEP_Formal vX.Y.Z" && git push origin vX.Y.Z
   gh release create vX.Y.Z dist/* --title "FEP_Formal vX.Y.Z — title" \
     --notes-file output/release-notes.md
   ```

7. Verify that the GitHub release was archived under the
   [software concept DOI](https://doi.org/10.5281/zenodo.23196891). The v1.5.0
   software version is [23196892](https://doi.org/10.5281/zenodo.23196892).
   The GitHub integration archives the tagged repository ZIP; it does not
   automatically include the PDF, wheel, sdist or release assets. Add the
   immutable software version DOI to the release notes only after checking
   the published record and its tagged source identity.
8. Publish a new version of the separate
   [scholarly concept](https://doi.org/10.5281/zenodo.19699233) from its latest
   manuscript record in the owner's Zenodo account. At the v1.6.0 preparation
   date, that latest record is [22072956](https://zenodo.org/records/22072956),
   version 1.1.0. Preserve this concept's existing version history. Upload the
   accepted PDF, offline companion, wheel, sdist, exact tagged source archive
   and SHA-256 checksums. The offline companion must preserve the PDF's
   relative explorer link: `pdf/fep_lean_combined.pdf` beside
   `manuscript/assets/mathematical-map.html` and its referenced assets.
   Keep current workstation paths, account information and private execution
   logs out of new generated public artifacts. An exact tagged source archive
   retains already-public historical custody records unchanged; compare those
   bytes with the prior public release rather than silently scrubbing history.
   Link the scholarly and software records, then verify
   the published version, author, ORCID, license, file bytes and DOI resolution.

`CITATION.cff` distinguishes software citation from its preferred scholarly
citation. The manuscript DOI identifies its exact scholarly version under the
scholarly concept. For v1.6.0 the published version is
`10.5281/zenodo.23220027`. Keep the scholarly concept, scholarly version and
software concept distinct; do not describe the two histories as one version chain.
The [2.1.0 scholarly record](https://doi.org/10.5281/zenodo.23607007)
was published and independently checked on 2026-10-26. All nine public files
(57,016,395 bytes) match the accepted source `96bf714` payload; DOI resolution,
version metadata, the checksum inventory and metadata bookends also passed.
The accepted 390-page PDF has SHA-256
`ba7594ee91f1bc9adf3830ae32e915da9f956436965758381615129d90378953`.
The [public archive verification](fep_2_1_0_manuscript_archive.json)
records all filenames, sizes and SHA-256 hashes.
This completes the separate scholarly deposit; it does not add a new proof,
provider run or execution claim. Its software source archive remains
[10.5281/zenodo.23631895](https://doi.org/10.5281/zenodo.23631895).
Preserve the earlier 1.6.0 scholarly record and its original PDF bytes.

## Deferred

Publication is a maintainer action: there is intentionally no publishing
workflow. Automating tag, GitHub release and Zenodo upload is deferred until a
maintainer decides to delegate that authority.
