# GitHub repository contract

The public project is **FEP_Formal**, hosted as `ActiveInferenceInstitute/fep_formal`.
The canonical Python import is `fep_formal`; the CLI is `fep-formal`.

## Repository presentation

[The root README](../README.md) owns the project overview and package long
description. `README.md` in this directory is a generated presentation with local
links rebased for its location. Edit the root overview, then use the regeneration
command in [the documentation maintenance contract](../AGENTS.md#maintaining-documentation).
The strict link gate rejects a missing or stale projection. Keep GitHub-facing
Markdown within the link and hygiene scans, including new contributor templates.

Verify GitHub's `/readme` response and actual repository page after publication;
local filenames alone do not establish which file GitHub displays. A branch
preview is distinct from the default-branch landing page.

## Workflows and dependency updates

[The repository contract](../AGENTS.md#required-checks) owns required checks;
`workflows/ci.yml` executes them. Keep changes to CI in step with that contract
and its inventory tests. Documentation-only shortcuts must retain their declared
source scope and fail-closed publication evidence checks. A skipped alternative
lane never supplies an unexecuted runtime or scientific check.

`dependabot.yml` owns automated dependency update policy. Workflow pins, action
permissions, credentials and hosted resource behavior need explicit source
review. Preserve provider and scientific acceptance boundaries, and obtain fresh
independent review for shared infrastructure or security changes.

## Versioned native supplement dispatch

For the proposed release supplement, dispatch the same immutable candidate ref
as the automatic pull-request run, without waiting for it to finish:

```sh
gh workflow run ci.yml --ref "$CANDIDATE_REF" -f native_supplement_profile=native-api-cli-supplement-v1 -f automatic_run_id="$AUTOMATIC_RUN_ID" -f automatic_run_attempt="$AUTOMATIC_RUN_ATTEMPT" -f supplement_pr_number="$PR_NUMBER" -f run_lean=true -f native_producer_shadow=false
```

Record the new supplement run/attempt before release joining. Dispatch success
is not test acceptance. Reject automatic reruns, changed bases/heads/trees or
unaccepted references rather than substituting an arbitrary prior green run.
This source proposal needs fresh full qualification before activation.
