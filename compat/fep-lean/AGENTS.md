# Deprecated `fep-lean` distribution contract

Metadata-only compatibility distribution. It owns no modules and no commands.

## Rules

- Do not add code, resources or console entry points here. The canonical
  `fep-formal` distribution owns both commands.
- Keep the dependency on the matching `fep-formal` version. A version change
  follows the release ordering in
  [the cutover guide](../../docs/identity-migration.md).
- Never publish this distribution ahead of the matching canonical release. It
  cannot replace already published wheels.
- Preserve the package name and metadata so an uninstall cannot delete shared
  code.

See the [distribution guide](README.md) and the
[root repository contract](../../AGENTS.md).
