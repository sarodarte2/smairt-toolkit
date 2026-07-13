# Experimental Safety Contract

SMAIRT safety checks are experimental and do not certify regulatory, institutional, contractual,
export-control, human-subject, or other compliance. A private repository is collaboration
infrastructure, not proof that a project is compliant. Controlled material is explicitly
unsupported for compliance in this beta.

Classification describes the material. Safety mode describes how aggressively SMAIRT responds.

## Classifications

- `public`: intended for open distribution; secrets remain prohibited.
- `unpublished`: ordinary prepublication research on public or private infrastructure.
- `private`: confidential or proprietary research requiring private collaboration.
- `controlled`: regulated, contractual, export-controlled, human-subject, or similarly restricted
  data. SMAIRT refuses to imply that its checks are sufficient.

## Standard and Strict

| Behavior | Standard | Strict |
|---|---|---|
| Intended use | Normal research collaboration | Sensitive or tightly restricted work |
| Repository visibility | Public/private for public or unpublished; private attestation for private work | Fresh observed private visibility required for consequential sharing and release |
| Unknown visibility | Warning where ordinary work can safely continue | Error for sharing and release |
| Secrets/private keys | Block in staged or tracked content | Same block |
| Raw protected data | Block protected paths and formats from Git | Same block with stronger local-only defaults |
| Protected summaries | Track only in an attested private repository | Local unless shareable and redaction-confirmed |
| Remote metadata | Explicit command; protected projects require confirmation | Protected queries denied by default unless explicitly confirmed |
| Release | Files, history, secrets, visibility, and provenance | Standard gates plus fresh private observation and protected-summary checks |
| Unknown policy state | Warn where safe | Fail closed for sharing and release |
| Compliance claim | None | None |

## Offline behavior and visibility

`status`, `validate`, `doctor`, and TUI refresh are offline. SMAIRT never hides a network lookup in
these operations. Refresh GitHub visibility explicitly:

```bash
smairt safety status --refresh-visibility --json
```

The cache stores visibility, observation time, source, and a stable status. It distinguishes a
missing `gh` CLI, unauthenticated access, timeout, unsupported host, and API failure without
storing the remote URL. Strict release rejects stale or unknown observations.

## Enforcement maturity

- SMAIRT CLI validation, Git hooks, immutable run gates, and publication gates are hard local
  controls within their documented scope.
- Cline `PreToolUse` is blocking only when Cline hooks are enabled.
- Codex project `PreToolUse` is advisory validation; it is not described as a guaranteed blocker.
- Zoo modes and all agent instruction files depend on agent cooperation.

Secret patterns and history scans are defense in depth, not comprehensive data-loss-prevention.
Stabilizing the safety policy requires team approval, a reviewed threat model, validated security
scanning, and a controlled-data policy review.
