# Security Policy

## Supported Versions

The project is currently maintained on the `main` branch. Security fixes are applied there first.

## Reporting a Vulnerability

Please do not open public GitHub issues for sensitive security reports.

Instead:

1. Email the maintainer with the subject line `Security Report: FaceProof`.
2. Include clear reproduction steps, impact, and any logs or screenshots that help validate the issue.
3. If the issue affects privacy, stored face images, embeddings, or operator authentication, mention that explicitly.

The project aims to acknowledge valid reports within 72 hours and provide a remediation plan as quickly as possible.

## Security Principles

- Face images are treated as sensitive data.
- Embeddings are stored as identity artifacts and should be protected like credentials.
- Verification images are not retained by default.
- Secrets must be provided through environment variables, never committed to the repository.
- Public demo deployments should not use real personal data.

## Deployment Notes

- Change the bootstrap operator password before any public or shared deployment.
- Use a reverse proxy and HTTPS outside local development.
- Review model licenses before enabling a real ONNX recognition model in commercial settings.
