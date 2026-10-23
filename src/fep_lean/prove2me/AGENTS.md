# Prove2me client contract

This folder owns the stdlib-only client for the remote Prove2me
Lean-formalization platform: credential resolution, token exchange, request
construction, typed errors, and thin mission/submission helpers. It does not
compile Lean locally, write SQLite sessions, or decide claim readiness.

- `config.py` owns `Prove2meConfig`, the five-step credential-resolution chain,
  the `Prove2meError` hierarchy, and `redact_secret`.
- `client.py` owns `Prove2meClient`, the `Prove2meTransport` injection seam, the
  default urllib transport, token caching, and the single 401 retry.
- `missions.py` owns the thin workflows over the client: `draft_proposal`,
  `add_theorem_item`, `submit_solution`, `wait_for_verdict`.
- `scripts/prove2me.py` is the only CLI; it is a thin wrapper over this package.

## Invariants

- No module in `src/fep_lean` outside this package imports it (`output/provenance.py` only lists its file paths). Every operation is
  an explicit caller action; do not wire it into pipeline, catalog, or
  full-run stages. Importing the package performs no request and reads no
  credential.
- Credentials are referenced by name only: `PROVE2ME_API_KEY` and
  `PROVE2ME_CREDENTIALS` (a path to a `credentials.json`). Never write a key or
  token into source, tests, docs, fixtures, or logs; tests use obviously fake
  keys.
- Resolution order is explicit argument, `PROVE2ME_API_KEY`,
  `PROVE2ME_CREDENTIALS` file, `~/.prove2me/credentials.json`,
  `~/prove2me_workspace/credentials.json`. An existing but unreadable,
  malformed, non-object, or key-less credentials file raises
  `Prove2meConfigError` naming the path, never its contents.
- `Prove2meConfig.__repr__` renders the key only through `redact_secret`. Keep
  every error message free of secret material.
- The API key is sent only in the body of the unauthenticated
  `POST /agent/refresh`; all other calls carry the cached bearer token.
- The token is reused until 60 s before `expires_at`. An authenticated 401
  triggers exactly one re-exchange and one retry; a second 401 raises
  `Prove2meAuthError`. Do not add retry loops.
- Error text is redacted of the API key and current access token before it
  leaves the client, and request headers are never embedded in messages.
- Callers see only `Prove2meError` subclasses: HTTP non-2xx is
  `Prove2meAPIError` (with `status_code`); network failure, wall-clock timeout,
  oversized (over 8 MiB) or non-JSON bodies are `Prove2meTransportError`;
  `wait_for_verdict` deadline expiry is `Prove2meTimeoutError`.
- The default transport enforces a wall-clock deadline in a daemon worker thread
  and reads in bounded chunks. Keep these bounds when touching it.
- `wait_for_verdict` treats only `PENDING` as non-terminal; any other status is
  returned to the caller. A returned document is the platform's verdict, not
  local Lean verification.
- Payload helpers omit `None` fields and URL-quote path identifiers.
- Mutating calls (`create_field`, `create_proposal`, `add_proposal_item`,
  `update_proposal`, `submit_proof`) change remote state. Do not invoke them
  from tests against the real platform or from automation without explicit
  authorization.

```python
from fep_lean.prove2me import (
    Prove2meAPIError,
    Prove2meAuthError,
    Prove2meClient,
    Prove2meConfig,
    Prove2meConfigError,
    Prove2meError,
    Prove2meTimeoutError,
    Prove2meTransport,
    Prove2meTransportError,
    TransportResult,
    add_theorem_item,
    draft_proposal,
    redact_secret,
    submit_solution,
    wait_for_verdict,
)
```

## Testing

Inject a fake `Prove2meTransport` and fake `now`/`sleep` clocks; pass
`Prove2meConfig(...)` directly or call `load(env=..., home=tmp_path)` so no real
environment or home directory is read. Real-transport tests use a loopback
`pytest_httpserver` only.

Focused contracts live in `tests/test_prove2me_client.py` and
`tests/test_prove2me_config.py`. Use the
[root required-check inventory](../../../AGENTS.md#required-checks) for project
acceptance; a remote platform operation needs its own explicit authorization.

See [README.md](README.md), [../llm/AGENTS.md](../llm/AGENTS.md),
[../AGENTS.md](../AGENTS.md), and [Prove2me operations](../../../docs/prove2me.md).
