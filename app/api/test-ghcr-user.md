# Test GHCR Push - User Namespace

Testing Docker image push to GHCR under user namespace instead of organization.

Changed from:
- `ghcr.io/ageekey/mirai-api` (organization)

To:
- `ghcr.io/ageekey/mirai-api` (user - github.actor)

This should resolve the 403 Forbidden error during GHCR push.
