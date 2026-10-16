# FEP_Formal agent interface

The project exposes the `fep-lean` command through the `fep_lean` Python package.
Discover commands with `uv run fep-lean --help`; common entry points are:

```bash
uv run fep-lean catalogue
uv run fep-lean atlas --check
uv run fep-lean dashboard --check
uv run fep-lean verify --fail-on-warnings --receipt output/native-verification.json
uv run python scripts/audit_formalisms.py --receipt output/formalism-audit.json
uv run fep-lean preflight
uv run fep-lean run
```

The generated catalogue in `config/topics.yaml` joins maintained metadata,
semantic review, and canonical Lean bodies. Agents use `fep-lean catalogue` for
offline artifacts, `fep-lean atlas` to inspect or drift-check authored
formalism relations, `fep-lean dashboard --check` to validate the deterministic
maintained witness projection, and `fep-lean preflight` before full
execution. Dashboard acceptance is the conjunction of typed equality,
inequality, and predicate checks with per-check tolerances; it is numerical
diagnostic evidence, not a Lean proof or an empirical result. A native
compilation claim requires independent validation of a current exact-roster
receipt. A
full result is publication-eligible only when report validation returns
`claim_ready: true`; stored mode, completion, and count fields are necessary
but are never trusted without digest, roster, provenance, and artifact
reconciliation.

The [repository contract](AGENTS.md) owns setup and required checks. Use the
[CLI reference](docs/cli-reference.md) for command boundaries and the
[active campaign](specs/comprehensive-next-steps/README.md) for remaining
acceptance work; a command succeeding does not close an unrelated gate.
