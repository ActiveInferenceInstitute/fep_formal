# Canonical identity cutover tooling

The [migration guide](../../docs/identity-migration.md) owns interface,
deprecation, evidence and release policy. The
[status record](../../docs/identity-migration-status.md) records validation.

`generate_legacy_stubs.py` projects canonical exports into legacy typing
aliases. Its `--check` gate rejects missing, changed or extra stubs without
repairing them. The canonical distribution owns the runtime adapter and all
typing aliases; the separate compatibility distribution owns metadata only.

`baseline/q5-gnn-artifact-proof.py.txt` preserves the byte-exact extractor
from the recorded pre-cutover source. The retained Q5 static check explicitly
hashes it against the unchanged manifest and labels its historical scope.
Current-source and native validators retain their canonical live-source
binding and reject historical receipts when sources have changed. Do not
import the snapshot or present it as current implementation.
