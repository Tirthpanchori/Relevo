# Security scope

Relevo is a trusted single-cluster portfolio executor. The shared bearer secret
authorizes job submission, inspection and worker coordination. It is not per-user
authorization: do not expose it to untrusted visitors or use this release as a
multi-tenant service. Public website demonstrations are recorded.

Keep credentials outside Git, client bundles, command arguments and logs. Use
HTTPS for hosted API access, verified TLS for hosted PostgreSQL, bounded provider
ingress/rate controls and private metrics/database access. Only registered trusted
handlers run; child processes are supervision, not an untrusted-code sandbox.
Configure Supabase Data API permissions independently from Python authentication.

If a credential leaks, revoke/rotate it at the provider and inspect usage. Removing
it from a new commit does not remove it from Git history. Preserve evidence before
any coordinated history remediation. Never post a secret or private job payload
in a public GitHub issue. Dependency and pattern checks are bounded, not a security
certification. Cloud network and privilege checks remain the deployer's responsibility.
