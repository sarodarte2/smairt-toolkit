# Security Policy

SMAIRT is an unreleased research preview. Security fixes are developed against the current
repository state; compatibility with an older generated project is evaluated case by case.

Do not open a public vulnerability issue. Use GitHub private vulnerability reporting for
[`sarodarte2/smairt-toolkit`](https://github.com/sarodarte2/smairt-toolkit/security/advisories/new).
Include the affected version, impact, minimal reproduction, and a suggested mitigation when known.
Do not include real credentials, private PDFs, protected research data, or sensitive remote URLs.

SMAIRT is not a sandbox and runs with the user's filesystem permissions. Secret scans,
protected-path checks, hooks, locks, and integrity records reduce accidents but do not provide
compliance certification or defend against a malicious local user with equal access.
