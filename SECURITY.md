# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it
**privately** rather than opening a public issue.

- Use [GitHub's private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
  ("Report a vulnerability" under the repository's **Security** tab), or
- Contact the maintainers directly.

Please include enough detail to reproduce the issue. We aim to acknowledge
reports within a few business days.

## Scope & Sensitive Material

This project handles sensitive credentials. When deploying or contributing, never
commit any of the following:

- `.env` files (real values) — only `.env.example` with placeholders belongs in the repo.
- GitHub App private keys (`pem/*.pem`).
- `GITHUB_WEBHOOK_SECRET`, `CLOUDFLARE_TUNNEL_TOKEN`, or any other secret.
- Real databases or fixtures containing personal/business data.

These paths are already excluded via `.gitignore`. Verify `git status` before every
commit and push.

## Security Notes

- Authentication uses a **GitHub App** (JWT-based) instead of a Personal Access Token.
- Incoming webhooks are verified with HMAC (SHA-1 / SHA-256); keep `WEBHOOK_VERIFY=true`
  in production.
- Runners are **ephemeral** — destroyed after each job to limit credential exposure.
- Store the GitHub App private key with `600` permissions.
