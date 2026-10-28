# Bridge ownership

`custody.py` owns ordered Signature-only drift classification, contained owner
hashes, and atomic output. `operations.py` owns source pins, both emitters,
read-only status, and comparison receipts. `certificates.py` is pure numerical
evaluation. `cli.py` adapts the existing `fep-formal` command.

Never turn a passing comparison into native proof or execution provenance.
Never silently re-pin sources, ignore deleted owners, or rewrite content under
a digest-refresh flag. No import-time filesystem writes or provider calls.
Tests live in the package's
ordinary pytest suite. Follow the parent package and repository contracts.
