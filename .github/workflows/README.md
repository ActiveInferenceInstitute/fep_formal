# GitHub workflows

Executable CI for `ActiveInferenceInstitute/fep_formal`. The
[GitHub repository contract](../AGENTS.md) owns workflow policy; the
[root required-check inventory](../../AGENTS.md#required-checks) owns the
commands these workflows execute.

## Workflows

| File | Trigger | Role |
| --- | --- | --- |
| [ci.yml](ci.yml) | Push and pull request to `main`; manual dispatch | The gate. Runs the required-check inventory through its `changes`, `documentation`, `distribution`, `python`, `static`, `render-deps`, `render` and `lean` jobs. |
| [lean-latest.yml](lean-latest.yml) | Weekly schedule and manual dispatch | `pin-audit` against the newest stable Lean toolchain. |
| [lean-latest-compile.yml](lean-latest-compile.yml) | Weekly schedule and manual dispatch | `compile-latest`, a non-gating compile against the newest stable Lean toolchain. |
| [source-pair-qualification.yml](source-pair-qualification.yml) | Manual dispatch only | `qualify-source-pair` for explicit FEP and GNN source SHAs; produces scoped bridge and Q7 evidence. |

## Editing rules

- Add or remove a gate in [ci.yml](ci.yml) and in the root required-check block in the same change. `tests/test_check_inventory.py` fails when the two drift.
- Keep workflow pins and action permissions under explicit review. [`.github/dependabot.yml`](../dependabot.yml) owns automated dependency updates.
- A skipped alternative lane never counts as an executed check. See [the GitHub repository contract](../AGENTS.md) for dispatch and acceptance boundaries.
- The dispatch-only source-pair workflow neither publishes commits nor establishes full-mode, publication or release acceptance.
