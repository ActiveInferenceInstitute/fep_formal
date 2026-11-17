# Q7 canonical scaffold serialization, schema 1

This protocol was frozen before changing `scaffold_digest` or its expected
digest. It replaces the representation-dependent `ast.dump` bytes of the
reviewed scalar OU runner, whose previous pin is
`793e6f58b3a79cbf7547e2869aefa4ca501e49d968cdd15fe2703f7c293241c2`.
It supplies static syntax identity, never runner execution or native proof.

## Encoding and scope

Parse source with `type_comments=True`, without importing or executing the
runner. Replace only the six
top-level `TABLE_SHAPES` assignment values with the existing
`Q7_LITERAL:<name>` sentinel strings. Preserve every other node, field, list
order, operator, name, literal value, and optional-field value. Source locations,
ordinary comments and whitespace stay outside the scaffold; type comments are
retained. The separate source digest
continues to bind exact runner bytes and the existing extractor binds the six
decimal lexemes and binary64 values.

The outer JSON list is `["fep-q7-scaffold-ast", 1, <tree>]`. An AST node is
`["node", <class-name>, [[<field-name>, <value>], ...]]`, in the explicitly
reviewed field order. A list is `["list", [<value>, ...]]`. Scalars use
`["none"]`, `["bool", <JSON boolean>]`, `["int", <decimal string>]`,
`["float", <binary64 hex string>]`, or `["str", <string>]`. Integer and Boolean
identity remain distinct; floating-point hex retains the exact finite binary64
value. Other scalar types and nonfinite floats fail closed. Encode ASCII JSON
with `ensure_ascii=True`, `allow_nan=False`, compact comma/colon separators,
and exactly one final LF.

## Reviewed AST schema

The owner contains an explicit node/field roster frozen from the actual runner
on CPython 3.10.20, 3.11.15, 3.12.13, 3.13.15 and 3.14.4. New node classes,
unlisted fields, missing required fields, unlisted instance attributes, and
field-order changes fail closed. Only the four source-location attributes
`lineno`, `col_offset`, `end_lineno`, and `end_col_offset` may be excluded.
Future grammar/schema additions require review rather than silent projection.

The only approved field normalization is `FunctionDef.type_params`: absent on
3.10/3.11 and present as an empty list on 3.12--3.14 becomes the same explicit
empty list. A nonempty value fails closed. No other empty, optional or default
field is dropped or synthesized. In particular function arguments, annotations,
decorators, return annotations, type comments, formatted-string fields, keyword
order, comparison order and statement order are retained.

## Interpreter and evidence boundaries

`canonical_scaffold_bytes` is a candidate-serialization surface restricted to
CPython 3.11--3.14. Unsupported interpreters fail before parsing. Actual runtime
parity records its returned bytes, the source and implementation digests,
interpreter identity, and rejection/mutation controls. Matching hashes alone
do not establish preservation: the schema rejection and semantic mutation
tests are required alongside the four supported runtime observations.

`scaffold_digest`, extraction and receipt validation remain accepted only on
CPython 3.14, with the existing refusal-before-parse contract. The new digest is
frozen only after reviewing the serialization and passing its controls. The
expected contract uses schema 2 and explicitly names the serialization format
and schema version, so an older contract cannot silently accept the new scheme.
Regenerating the manifest is static bookkeeping; older native receipts become
stale and require a separate new capture. Do not rehash a native receipt to
claim that the changed extractor was accepted.

The 2026-11-16 portability refresh drops EOL CPython 3.10 from the active
candidate surface and requires fresh 3.11–3.14 observations. The original
schema review above remains historical; native receipts require independent
renewal after source-owner changes.
