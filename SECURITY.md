# Security Policy

Security fixes target the latest GitHub prerelease. Earlier beta projects may need export and
recreation rather than migration.

Do not open a public vulnerability issue. Use GitHub private vulnerability reporting for
`PNNL-CompBio/smairt-template`. Include the affected version, impact, reproduction, and suggested
mitigation without real credentials or protected research data.

SMAIRT is not a sandbox and runs with the user's filesystem permissions. Secret scans,
protected-path checks, hooks, locks, and integrity records reduce accidents but do not provide
compliance certification or defend against a malicious local user with equal access.
