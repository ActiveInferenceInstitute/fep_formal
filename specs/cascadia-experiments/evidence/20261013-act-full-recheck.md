# ACT full recheck, 2026-10-13

The final owned ACT selection passed at GEO commit
`0c54908e40323f65e433400e7c917bff1ac0f591`. No source changed between the
independent publication review and this run.

```bash
uv run --no-sync python GEO-INFER-TEST/run_unified_tests.py \
  --module ACT --timeout 1800
```

The selected external Python was 3.12.11. The 1800-second total budget
matches the earlier full attempt; no test deadline, threshold, process
inspection limit or proof pin was changed. The intervening default-budget
run timed out after 300 seconds and remains failed.

| Field | Observed |
| --- | --- |
| Run | `d2f4fa69fb3c48ae975dbf2909a2fb3e` |
| Attempt | `3d72ebc583cf497eb279def46c789d48` |
| Runner | PASS, exit 0, 771 executed testcases, 340.15 seconds |
| JUnit | 771 tests, zero failures, zero errors, zero skips |
| Workspace custody | `custody_complete: false` |

The full selection is numerical/software execution evidence, not a native
proof or complete-workspace custody claim. Other retained broad failures
remain failures. The qualified candidate source was independently reviewed;
unrelated working files and environments were preserved.

The GEO checkout retains the run beneath `.geo-infer-test-results/runs/`
using the identifiers above. Task command logs are on GitVault under
`Local/task-tmp/cascadia-real-gnn-20261013`.

| Retained artifact | SHA-256 |
| --- | --- |
| Run `summary.json` | `005a3bcbbcaa433d187223433b0c827b6831c20b2f2ecae50a20c50e3dc62ff5` |
| Attempt `receipt.json` | `035644f06ea0ec824aa015b2ac0eb3d6eeac8c3eecdfb663f2b9c4c9f36ec2a1` |
| Attempt `junit.xml` | `c3be759bcbd5afe85c7e5d3ac0dbd4a768070d44e9be0e735d72254e52224539` |
| `act-main-final-explicit-budget.log` | `2efe4768b1df6283b1d538f07b98a786ed15109768fb65072bc553d104c59d6e` |
