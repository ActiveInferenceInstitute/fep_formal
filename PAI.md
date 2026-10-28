# FEP_Formal agent interface

The project exposes the `fep-formal` command through the `fep_formal` Python package.
Discover commands with `uv run fep-formal --help`; common entry points are:

```bash
uv run fep-formal catalogue
uv run fep-formal atlas --check
uv run fep-formal dashboard --check
uv run fep-formal verify --fail-on-warnings --receipt output/native-verification.json
uv run python scripts/audit_formalisms.py --receipt output/formalism-audit.json
uv run fep-formal preflight
uv run fep-formal run
```

The generated catalog in `config/topics.yaml` joins maintained metadata,
semantic review, and canonical Lean bodies. Agents use `fep-formal catalogue` for
offline artifacts, `fep-formal atlas` to inspect or drift-check authored
formalism relations, `fep-formal dashboard --check` to validate the deterministic
maintained witness projection, and `fep-formal preflight` before full
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
