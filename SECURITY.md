# Security Policy

## 🛡️ Zero Personal Data Commitment

TodayTech is built on the principle of strict personal privacy:
- **No Telemetry / No Tracking:** TodayTech transmits zero metrics, user activity, or analytics to any central server.
- **Local-Only Storage:** All opportunity history, profile information, and generated application drafts remain strictly on your own hardware or private container in `data/`, `profile.yaml`, and `.env`.
- **Pre-commit Secrets Scanning:** We enforce automated secret scanning via `.pre-commit-config.yaml` (`detect-secrets`) to prevent credentials from ever being staged or committed to Git.

---

## 🔒 Supported Versions

Only the latest release on the `main` branch is actively supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

---

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability or accidental exposure risk within TodayTech:

1. **Do NOT open a public GitHub issue.**
2. Send an email to the repository maintainer or create a private GitHub Security Advisory under the **Security** tab of the repository.
3. Include:
   - Description of the vulnerability.
   - Steps to reproduce or proof-of-concept.
   - Potential impact.

We take security issues seriously and will acknowledge receipt within 48 hours and work with you on a timely resolution.
