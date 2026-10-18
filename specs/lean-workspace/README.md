# Lean 4.35 workspace coordination

Use FEP_Formal's explicit compiler/dependency pins, source ownership and real
build evidence as the reference practice across independent repositories.
This coordinator is standard-library Python 3.14+. GitVault remains the owner
of repository discovery, acquisition and its shared writer lock.

## One editor workspace, independent packages

```sh
python workspace.py inventory --vault /path/to/gitvault --output inventory.json
python workspace.py workspace --input inventory.json --output /path/to/local/lean-workspace
python workspace.py check --input inventory.json --output alignment.json
python workspace.py build --vault /path/to/gitvault --input inventory.json --output builds.json
python test_workspace.py
```

Open `Lean.code-workspace` in VS Code with the Lean 4 extension. Every owned
Lake package has its own root, including nested opt-in packages. Each retains
its namespace, dependency manifest, default targets and core/Mathlib boundary.
Reference mirrors remain in the inventory but are excluded from editable
workspace roots and build mutations. Generated local inventory/lock files may
contain private repository names and absolute paths: keep them local and out
of public Git history.

Inventory scans every page of the current GitVault manifest. A changing scope,
missing repository, failed inspection or nonmatching account-package pin prevents
a successful account-package check. Reference mirrors report `reference-only`
with their actual alignment and problems; their pins do not gate account-package
success, and they remain excluded from builds. Non-Lake sources are inventoried separately;
they are not silently represented as successfully built projects. A compiler
installation is not a project proof.

Builds acquire GitVault's repository and Git common-store leases with the
migration guard. They wait for a conflicting repository lease, including a sync,
while independent repositories can proceed.
Builds serialize packages, because nested packages can share dependency trees.
The exact compiler is selected through Elan, and `lake --wfail build` rejects
warnings, including open proof obligations and empty default builds. Logs retain
exit status, elapsed time and checksums. Source/configuration/manifest changes
before or during a build fail the captured lock check. A successful default build
does not certify unselected optional targets, Python consumers or scientific
claims; run each repository's declared additional gates too.

## Lockstep update procedure

1. Discover the complete current collection. Keep unavailable repositories
   explicit. Preserve dirty working trees and mirror ownership.
2. Select one stable compiler and matching Mathlib release. This train uses
   `leanprover/lean4:v4.35.0` and Mathlib
   `56a005855ea17e0b0958f73ec801ae140b0a1679` (`v4.35.0`). Keep core-only packages
   core-only. Projects depending on FEP_Formal need its accepted source commit
   pinned independently from the compiler release.
3. Prepare changes in isolated snapshots. Update live toolchain pins, authored
   dependency requirements, runtime constants, tests and active documentation
   together. Leave historical evidence and frozen fixtures unchanged.
4. Regenerate each changed Lake manifest with the selected compiler. Review the
   complete dependency delta. Acquire the official matching Mathlib cache once;
   local package overrides can reuse an exact checked dependency tree during
   development. Portable committed manifests must retain their Git sources.
5. Build all declared targets and run the repository's actual consumer and axiom
   gates. Fix changed APIs without weakening statements or adding proof holes.
   An empty build, disabled warning, admitted theorem or stale receipt is not
   migration acceptance. Keep pre-existing research obligations explicit.
6. Apply only reviewed changes to unchanged working trees under GitVault's
   writer guard, commit each repository and push normally. Record the resulting
   source commits together in a refreshed workspace lock and run the complete
   cross-repository check again.
7. Qualify hosted checks on the final commits. Version the train manifest as a
   cohort; preserve individual projects' semantic release versions. Cross-repo
   Git pushes are not atomic, so interrupted publication must remain explicit
   until every selected remote commit matches the cohort.

Lake's package-overrides format supports sharing a checked local dependency
without rewriting portable source requirements:
<https://lean-lang.org/doc/reference/latest/Build-Tools-and-Distribution/Lake/>

Exact project pins and explicit Elan selection are documented at:
<https://lean-lang.org/doc/reference/latest/Build-Tools-and-Distribution/Managing-Toolchains-with-Elan/>

Workspace builds use GitVault repository leases, one package at a time. Each
lease protects the repository identity and Git common store while the locked
snapshot is checked and built. Other repositories can continue independently.
Reference mirrors are reported without acquiring a write lease or building.
