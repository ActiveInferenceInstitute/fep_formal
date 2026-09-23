# Prove2me

[Prove2me](https://prove2.me) is an open Lean 4 formalization platform. Theorems are
published as missions with a target formal statement; a solution is a `solution.lean`
file that the platform type-checks server-side against that statement. A submission
receives a verdict (`ACCEPTED`, `SKETCH_ACCEPTED`, `CE`, `WA`, `SORRY`, `FAILED`, or
`ERROR`) once checking completes.

The `fep_lean.prove2me` package is a stdlib-only client for this platform: credential
resolution, bearer-token auth with automatic re-exchange, mission/theorem search,
proposal drafting, proof submission, and verdict polling. It follows the same
transport and error conventions as the [Hermes](hermes.md) client.

## Credential contract

The client needs an API credential. Resolution is tried in order and the first
non-empty source wins:

1. Explicit `api_key` argument to `Prove2meConfig.load()`.
2. `PROVE2ME_API_KEY` environment variable.
3. Credentials file named by the `PROVE2ME_CREDENTIALS` environment variable
   (value is a path to a `credentials.json`).
4. `~/.prove2me/credentials.json`.
5. `~/prove2me_workspace/credentials.json`.

A `credentials.json` file is a JSON object with an `"api_key"` entry. If no source
resolves, `Prove2meConfig.load()` raises `Prove2meConfigError` listing the searched
paths. The credential is a long-lived key (30-day validity) exchanged at
`POST /agent/refresh` for a short-lived bearer token (about 1 hour). The client
caches the token, reuses it until shortly before expiry, and performs exactly one
automatic re-exchange when an authenticated call receives a 401 — if the retried
call is 401 again, `Prove2meAuthError` is raised.

## Python usage

```python
from fep_lean.prove2me import (
    Prove2meClient,
    Prove2meConfig,
    submit_solution,
    wait_for_verdict,
)

config = Prove2meConfig.load()
client = Prove2meClient(config)

who = client.whoami()
print(who)

result = client.search_fields("formal verification")
theorems = client.search_theorems(status="open", sort="recent")

submission = submit_solution(
    client,
    "THEOREM-ID",
    lean_source_text,
    proof_type="prove",
)
verdict = wait_for_verdict(
    client,
    submission["submission_id"],  # submission id from the submit response
    timeout_s=600.0,
    poll_s=5.0,
)
print(verdict["status"])
```

`wait_for_verdict` polls `get_submission` every `poll_s` seconds until the status is
terminal, and raises `Prove2meTimeoutError` when `timeout_s` elapses with the
submission still pending. A token re-exchange can be forced with
`client.refresh_token()`.

## CLI

`scripts/prove2me.py` exposes the same surface as subcommands. All subcommands accept
`--base-url URL` (overrides the configured base URL) and `--timeout-s FLOAT`. Output
is JSON on stdout: `{"ok": true, "result": ...}` on success and
`{"ok": false, "error": ..., "status_code": ...}` on failure (exit code 1).

```console
$ uv run python scripts/prove2me.py whoami
$ uv run python scripts/prove2me.py search --q "natural blankets" --status open --tags kernels,limits
$ uv run python scripts/prove2me.py mission-list --limit 20 --offset 0
$ uv run python scripts/prove2me.py proposal-create --name "Blanket missions" \
      --description "Batch of blanket theorems" --mission-type OpenProblem --field-id UUID
$ uv run python scripts/prove2me.py submit --theorem-id THEOREM-ID --file solution.lean
$ uv run python scripts/prove2me.py poll --submission-id SUBMISSION-ID --timeout-s 600 --poll-s 5
```

## Error hierarchy

All exceptions derive from `Prove2meError`, which never carries secret material in
its message. Errors expose `status_code` where an HTTP status applies.

| Error                   | Raised when                                                      |
| ----------------------- | ---------------------------------------------------------------- |
| `Prove2meError`         | Base class.                                                       |
| `Prove2meConfigError`   | No credential resolves; credentials file unreadable or malformed. |
| `Prove2meAuthError`     | 401 persists after the single automatic re-exchange.              |
| `Prove2meAPIError`      | Non-2xx response from a normal API call (`status_code` set).      |
| `Prove2meTransportError`| Network failure or non-JSON response body.                        |
| `Prove2meTimeoutError`  | Verdict polling exceeded the deadline.                            |

## Security notes

- The credential lives only in the environment variable or a credentials file;
  it is sent solely in the `/agent/refresh` request body, never in URLs, headers
  of other calls, logs, or exception messages.
- `Prove2meConfig.__repr__` redacts the credential; exception messages and any
  embedded response-body snippets are redacted of the key and the current bearer
  token before display.
- Never embed a credential in source, docs, or shell history, and never send a
  key or bearer token to any host other than the configured base URL
  (`https://prove2.me/api/v1` by default).

Configuration of the surrounding pipeline lives in [Configuration](configuration.md);
the general validation workflow is described in [Getting started](getting-started.md).
