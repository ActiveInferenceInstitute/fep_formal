# Release bundle

Deterministic, fail-closed assembly and validation of publication evidence.
The archive is a transport for already validated evidence, never a new proof
plane.

## Modules

| Module | Responsibility |
| --- | --- |
| `_assemble` | Assemble archive members, construct the manifest and write the archive. |
| `_acceptance` | Run Python acceptance, validate its receipt and project numerical witnesses. |
| `_browser` | Validate the browser-acceptance receipt for the bundle. |
| `_constants` | Own canonical constants, regexes and receipt paths. |
| `_core` | Own shared models, errors and canonical helpers. |
| `_identity` | Check publication identity, licensing and owner classification. |
| `_manuscript` | Render the manuscript deterministically and replace the publication set. |
| `_prerequisites` | Aggregate fail-closed prerequisites for the entry points. |
| `_validate` | Read an archive and validate it against a live checkout. |

The public entry point is [`scripts/build_release_bundle.py`](../../../../scripts/build_release_bundle.py).
`--check` re-renders in temporary directories and binds an existing archive
back to current sources without mutating the checkout.

## Use

```bash
uv run python scripts/build_release_bundle.py --output dist/fep-formal.tar.gz
uv run python scripts/build_release_bundle.py --check --output dist/fep-formal.tar.gz
```

Archive contents are normalized regular files. Provider-plane reports are
excluded. Native, declaration, projection, browser, numerical and manuscript
inputs must independently bind to the live checkout before an archive is
accepted. See the [output package contract](../AGENTS.md), the
[release procedure](../../../../docs/release.md) and the
[release runbook](../../../../scripts/README.md).
