# Packaged data contract

This directory contains generated package resources. Follow the canonical owner
mapping in [README.md](README.md): catalogue projection and portable methods
inputs have different generators. Regenerate through the appropriate owner and
check its drift mode after changing maintained inputs.

Checkout and packaged projections must remain byte-identical to their owners.
Do not add runtime secrets, local paths, receipts or hand-maintained overrides.
A packaged resource is source data, not native or scientific acceptance.
