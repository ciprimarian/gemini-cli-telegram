# Security

## Defaults

- deny by default
- explicit allowlist
- admin-only power mode
- path traversal blocked
- archive extraction checked before unpacking
- request rate limiting
- transcript and audit trail written locally

## Workspace root

The bridge only trusts paths under `WORKSPACE_ROOT`.

Anything outside that root is treated as out of bounds.

## Custom domain

If you deploy docs with GitHub Pages and want a proper domain, replace the placeholder in `docs/CNAME.example` with your real domain and publish it as `CNAME`.
