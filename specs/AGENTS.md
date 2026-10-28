# `specs/` contract

Slice-local specifications, acceptance artifacts, and research modules. See
[README.md](README.md) for the acceptance-artifact conventions.

- `done/**` is a closed, historical record. Do not rewrite its prose, values, or any
  bytes a receipt may hash. The only permitted edit is repairing a broken link, and
  only when no receipt hashes the file.
- `**/evidence/**` (journals, command results, captured logs) is retained evidence on
  the same terms as `done/`.
- `**/gnn_output*/`, `**/gnn-input/`, and `**/fixtures/` hold tool outputs and pinned
  inputs; regenerate them with their owning tool, never by hand.
- The link and hygiene gates (`docs/check_links.py`, `docs/md_hygiene.py`) skip these
  historical trees by design (`--include-root`); active spec documents are scanned.
- Slice-local tooling lives here (see `openai-math-methods/generate_package_methods.py`)
  instead of adding new files under `src/fep_formal/` or `scripts/`.
