# Safety Modes

SMAIRT is a guardrail, not institutional compliance certification.

SMAIRT uses contributor attestations because a remote URL alone cannot prove whether a repository
is private. For GitHub remotes, it also attempts an authenticated, read-only `gh repo view` query.
When that succeeds, observed visibility is authoritative. A disagreement between observed and
attested visibility is an error and must be resolved before release.

Standard mode supports ordinary research collaboration. Private and controlled projects require
a contributor-confirmed private-repository acknowledgment. Editing a tracked summary later does
not remove earlier content from Git history.

Strict mode keeps summaries derived from private or controlled sources in `.smairt/local/` unless
the contributor marks them shareable and confirms redaction. Unknown or public visibility is an
error. Remote Crossref/OpenAlex requests require explicit confirmation because identifiers leave
the local project.

Both modes block common credentials, private keys, raw-data paths, ignored PDFs, and protected
research formats from Git. Run `smairt validate --staged` before committing and
`smairt safety release-check` before changing visibility or publishing.
