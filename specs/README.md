# Spec directories

`specs/done/` holds closed spec work. Each subdirectory is a historical
record: its README, acceptance artifacts, and captured assets describe what
was verified at acceptance time and stay as they were accepted. Editing a
closed spec's evidence values is prohibited; historical receipts are
annotated, never rewritten.

## Acceptance-artifact conventions

Future spec acceptance artifacts MUST use bundle-backed durable copies and/or
the `local_gitignored_path` field naming. Pointing a curated spec asset at a
mutable gitignored `output/` path as if its current content were the accepted
evidence is prohibited. Three styles have been observed in existing specs;
follow them or the sibling conventions when writing new ones:

- [`formalism-catalogue-120`](done/formalism-catalogue-120/) — path-style
  raw-XML pointers. Its [acceptance receipt](done/formalism-catalogue-120/assets/acceptance.json)
  pins `pytest.xml`/`coverage.xml` digests alongside committed copies in
  `assets/`, and its native/audit receipt pointers to gitignored `output/`
  content are annotated historical and digest-pinned only.
- [`active-inference-formal-depth`](done/active-inference-formal-depth/) —
  [`acceptance-evidence.json`](done/active-inference-formal-depth/acceptance-evidence.json)
  uses `local_gitignored_path` fields: the gitignored `output/` content is
  gone, and the JSON is a closure snapshot recording schema versions,
  identities, and SHA-256 digests, not the receipts themselves.
- [`formalism-catalogue-155`](done/formalism-catalogue-155/) — no local
  acceptance file. Its README states evidence boundaries and points to the
  validated release bundle, where the durable published copies of the
  gitignored generation outputs live.

Raw runner XML (`pytest.xml`, `coverage.xml`) belongs in the validated release
bundle, not curated spec assets. The `formalism-catalogue-120` copies are
historical and stay as-is; new specs should not add more of them.

## When pointed content is gitignored or gone

A receipt path under `output/` is a historical pointer, not a live file
reference. When the pointed content is no longer present, keep the SHA-256
digests and record the artifact's digest-only identity (run id, digests,
schema versions) — as `active-inference-formal-depth` does — and annotate the
pointer as historical rather than deleting it or claiming the content is
current.
