# `fep_lean.prove2me`

A standard-library client in FEP_Formal for the [Prove2me](https://prove2.me) Lean 4
formalization platform. It is explicit and authenticated: nothing here runs as
part of catalogue mode or the pipeline, and every call needs an API key you
supply.

`Prove2meConfig.load()` resolves the key from an explicit argument, then the
`PROVE2ME_API_KEY` environment variable, then a `credentials.json` named by
`PROVE2ME_CREDENTIALS`, then `~/.prove2me/credentials.json`, then
`~/prove2me_workspace/credentials.json`. The key is masked in `repr` and in
error messages. The default base URL is `https://prove2.me/api/v1`.

`Prove2meClient` exchanges the key for a bearer token at `POST /agent/refresh`,
caches it until shortly before expiry, and re-exchanges once on a 401 (a second
401 raises `Prove2meAuthError`). It covers `whoami`, field and theorem search,
mission listing, mission-proposal create/read/update, multipart proof
submission, and submission lookup. The transport is injectable
(`Prove2meTransport`), so ordinary tests use fake responses. Real-transport
tests use a loopback HTTP server rather than the remote platform.

`missions.py` adds small helpers: `draft_proposal`, `add_theorem_item`,
`submit_solution`, and `wait_for_verdict`, which polls until a status other than
`PENDING` or raises `Prove2meTimeoutError` at the deadline.

```python
from fep_lean.prove2me import (
    Prove2meClient,
    Prove2meConfig,
    submit_solution,
    wait_for_verdict,
)

client = Prove2meClient(Prove2meConfig.load())
submission = submit_solution(client, theorem_id, lean_source)
verdict = wait_for_verdict(client, submission["submission_id"])
```

The response field name follows
[Prove2me operations](../../../docs/prove2me.md). A command-line wrapper lives in [`scripts/prove2me.py`](../../../scripts/prove2me.py)
(`whoami`, `search`, `theorem-show`, `mission-list`, `proposal-create`,
`proposal-show`, `submit`, `poll`); it prints one JSON object on stdout.

## Failure policy

- Errors derive from `Prove2meError`: config, auth, API (non-2xx, with
  `status_code`), transport (network, timeout, oversized or non-JSON body), and
  poll timeout are distinct classes.
- The default transport bounds total wall time and response size.
- A verdict returned by the platform is remote evidence. It is not a local Lean
  check and is not recorded by the Gauss or verification layers.

See [AGENTS.md](AGENTS.md), [Prove2me operations](../../../docs/prove2me.md),
and [../llm/README.md](../llm/README.md) for the sibling provider client.
