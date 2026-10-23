# Split Python and live Chrome acceptance

This slice validates the union of two once-only pytest components. CI first
runs the complete non-serial suite except the two canonical live Chrome cases
with parallel `loadgroup` workers and the existing 89% coverage floor. After
those workers finish, it runs exactly those two cases once with `-n 0`, appends
coverage, and applies the same 89% floor again. No startup deadline, retry,
skip, or production browser policy changes. This explicit isolation policy
does not establish why earlier hosted startups failed.

The checker uses actual current pytest collection to approve membership:

```bash
uv run python specs/publication-browser-acceptance/validate_acceptance.py \
  --project-root . --collect output/python-collection.json
uv run python specs/publication-browser-acceptance/validate_acceptance.py \
  --project-root . --collection output/python-collection.json \
  --parallel-junit output/python-parallel.xml \
  --chrome-junit output/python-live-chrome.xml \
  --coverage coverage.xml --output output/python-acceptance-summary.json
uv run pytest specs/publication-browser-acceptance/test_validate_acceptance.py -q --no-cov
```

Collection runs `tests/ --collect-only -q -n 0 --no-cov -p no:cacheprovider -m
"not serial_lean"` in a separate Python 3.14 process. It imports tests for
collection but executes no test bodies. The approved record hashes source and
test leaves. Validation recollects current membership, refuses a stale or
coherently edited record, and compares the exact two JUnit components against
that membership. Class methods and parameter strings containing `::` or `@`
retain their exact identities. The serial Chrome names must be unsuffixed;
there is no generic group-suffix removal.

All eight named issue #46 cases must occur exactly once and pass without a
skip: both real Chrome cases, two failure-diagnostic controls, both
absent/present xdist collection controls, and both actual-worker ordering
controls. Every other failure or error also fails acceptance. Other optional
skips are disclosed with their exact reasons. Empty, duplicated, omitted,
unknown, or incorrectly routed cases are refused. Coverage requires positive
valid lines, `0 <= covered <= valid`, consistency with the declared decimal
rate, and the exact integer 89% bound. Outputs stay under `output/`; input and
output symlink paths are refused. Output path/inode aliases to acceptance inputs
are refused on both success and failure paths. Atomic output replacement avoids
writing through an existing hardlink to a source file; validation leaves input
bytes and mtimes unchanged.

The summary records XML/source hashes and structural acceptance. It does not
authenticate that arbitrary supplied XML or coverage came from particular
commands. Hosted acceptance additionally requires the reviewed workflow,
actual same-run command/exit logs, fresh coverage reset then append, exact
checkout identity, artifact digests and independent shared-infrastructure
review. PR acceptance and exact-main release acceptance remain separate.
Passing these startup cases does not close the production DOM/capture lane,
create a browser receipt, prove earlier startup causality, or establish
provider, native Lean, or scientific acceptance.

## Same-run render dependency readiness

`wait_render_dependencies.py` is slice-local CI publication-readiness tooling.
Before a PDF consumer downloads figure assets, it checks the current workflow
run, attempt, source identity, successful `render-deps` producer and exact artifact
name. It is an orchestration barrier, separate from browser capture policy and
from scientific or native acceptance. Its bounded API polling cannot approve a
failed producer, substitute an older attempt, or establish artifact content
acceptance; the download and independent publication validators still apply.

The helper uses only the standard library and performs no environment inspection
or network access on import. CI invokes it with its actual GitHub environment.
The canonical required checks in `AGENTS.md` cover this slice with Ruff and
format checks and explicitly include the helper in strict mypy coverage. Tests
mock the API boundary; a later actual hosted run remains required before rollout.
