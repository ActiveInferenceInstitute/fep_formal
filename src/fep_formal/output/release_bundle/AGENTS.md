# Release bundle contract

The archive transports already validated evidence; it does not create a new
proof plane or promote an unaccepted input.

## Invariants

- Payload members are normalized regular files only. Reject symlinks,
  directories, device nodes and mutable provider-plane reports.
- The manifest and checksum table describe the exact payload without a
  recursive self-hash.
- Acceptance joins native, declaration, projection, browser, numerical and
  manuscript inputs, and each must bind to the live checkout.
- `--check` is non-mutating: it re-renders in temporary directories and binds
  an existing archive back to current sources.
- Writes are atomic. A failed build leaves no partial archive that validation
  could mistake for a complete one.

## Change rules

- Keep [`scripts/build_release_bundle.py`](../../../../scripts/build_release_bundle.py)
  a thin wrapper. It must not reconstruct the archive roster, renderer policy,
  manifest, checksum table or evidence boundaries.
- Put a new acceptance predicate in `_validate.py` or `_acceptance.py` and add
  its positive and tamper tests under `tests/test_release_bundle_*.py`.
- Do not add network access or provider credentials to assembly or validation.
- Preserve the distinction between the software archive and the manuscript
  archive. Follow the [release procedure](../../../../docs/release.md) and the
  [output package contract](../AGENTS.md).
