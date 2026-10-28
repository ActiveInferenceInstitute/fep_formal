# Branch coverage

The declared coverage configuration is maintained in
[`pyproject.toml`](../pyproject.toml). The required test gate measures line
coverage and requires at least 89%; branch coverage is a separate diagnostic.
Use Python 3.14, selected by [`.python-version`](../.python-version), for
repository validation. The packaging floor does not change that requirement.

## Measured package line floors

The [policy](coverage-floors.json) additionally gates each of the 15 nonempty
direct packages in coverage.py's XML. A subpackage has its own floor; its lines
are not counted again under its parent package. CI checks the XML after the
parallel Python component and isolated Chrome component have both contributed,
retaining the result beside their acceptance evidence. The exact command lives
in the [required-check inventory](../AGENTS.md#required-checks).

The baseline is the actual PR181 run
[38834310995](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/38834310995),
head `2893bed22d084183e81b02ab2ce68a71aab8df75`, tested merge
`f739e4bfcf32fe58ed8a701dbead0d9f8f0fe0df`. Its tree
`26447d4324a1ada590c20496c6e552e7f78de165` also identifies main checkpoint
`4208d589a00c5eeaed5a36d8760153bad8805ef1`. Authenticated coverage artifact
`12019210437` contains 17,197 covered lines out of 18,765 executable lines.
The policy retains the ZIP/XML SHA-256 digests, exact package denominators,
and the selection rule: `floor(100 * covered / valid)` for each nonempty
package. No threshold is inferred from the rounded XML display rate. The
pre-existing aggregate requirement stays at 89%.

`fep_formal.data` has zero executable lines at this checkpoint. It is explicitly
listed as empty rather than credited with a perfect coverage percentage; adding
executable lines there requires a measured floor. Missing or unexpected packages,
duplicate file/line records, malformed rates/counts, path mismatches, and aggregate
count disagreement fail closed. Threshold comparisons use exact integer ratios.
Changes to package membership or floors require review and a new measured
baseline, rather than deleting the failing package or lowering its threshold.

The regression control copies the actual custody model into an isolated tree,
inserts a marked conditional arm in `Census.status_of`, and traces the copy with
coverage.py. The one-arm control leaves those added lines uncovered: the global
89% line gate still passes, while the measured custody line floor fails. The
positive control also exercises the inserted arm. CI retains the original and
instrumented source, command, XML and evaluated counts for each control.
This demonstrates uncovered branch-body line detection in an instrumented
production-source copy. It changes no live custody source, measures no branch
arcs, and does not show that every possible decision edge was exercised.
Fresh hosted checks must qualify the new checker and controls before acceptance
of their source epoch. The retained baseline alone does not do that.

## Measuring branch coverage

An optional branch measurement can use the existing diagnostic command:

```bash
uv run pytest tests/ -q --cov=src --cov-branch --cov-report=term-missing \
  --ignore=tests/test_figure_generation.py
```

This excludes one test module, not the figure source from the coverage
denominator. Inspect the reported source set and subprocess coverage before
interpreting the result. Record the exact command, interpreter, source identity,
reported line and branch denominators, and observed result with each run.
The configured `concurrency = ["multiprocessing"]` setting alone does not
establish that every child contributed coverage data.

## Acceptance boundary

This guide claims no fresh branch-coverage measurement. Branch coverage is not
independently gated, and the 89% line-coverage requirement does not establish
branch coverage. A run with branch measurement enabled does not replace the
declared line-coverage gate or native/formal acceptance.

See [Testing](testing.md) and the [required checks](../AGENTS.md#required-checks)
for the maintained validation contract. Dated failure ledgers and prior
measurements remain historical evidence in repository history; they are not
current operating instructions.

The identity migration maps the historical `fep_lean` package selectors to
`fep_formal` without changing their recorded baseline counts or floor values.
Those baseline measurements remain historical; the migrated package and its
compatibility adapter require a fresh coverage run. The adapter is additional
code under the same aggregate floor.

The adapter has a separate October 27, 2026 local baseline: all 32 executable
lines were covered by the 11 identity migration tests. Its measured floor is
100%. The policy records the source and XML digests separately from the
historical canonical-package baseline. The adapter-only measurement used an
explicit zero aggregate threshold solely to collect that isolated baseline;
the required full-suite aggregate threshold remains 89%. Missing adapter
coverage fails the same complete-package inventory check. Legacy subpackages
contain typing aliases only and are not accepted as executable coverage owners.
