<p align="center">
  <img src="docs/assets/smairt-banner.svg" alt="SMAIRT — research provenance in the terminal" width="820">
</p>

# SMAIRT

## Install from source

There is no verified SMAIRT release yet. The supported installation path is deliberately simple
and truthful:

```bash
git clone https://github.com/PNNL-CompBio/smairt-template.git
cd smairt-template
uv tool install --python 3.11 .
smairt --version
```

This installs `smairt` as an isolated user-wide tool. Conda is not required to run SMAIRT. We
recommend Miniforge for isolated experiment environments that SMAIRT can discover or create.

Need the prerequisites? Follow [Installation](docs/INSTALL.md),
[Miniforge and Conda](docs/SETUP_CONDA.md), or [Git and GitHub](docs/SETUP_GIT_GITHUB.md).

## Science is the hard part

The hard problem of science is not producing more text or code. It is maintaining a trustworthy
line from a question, through sources and experiments, to the judgment a researcher is prepared to
defend. AI can help researchers search, summarize, propose, and implement, but it must not quietly
become the author of scientific decisions.

SMAIRT—the Scientific Method with AI Research Toolkit—is a local-first workspace for that division
of labor. It keeps research state in readable YAML, JSON, and Markdown, asks humans to approve
consequential steps, and gives coding agents a bounded, inspectable place to work.

## Start working

Start with the small command-line welcome:

```bash
smairt
```

It shows the installed version, credits, license, and the three useful entry points. Run `smairt
setup` for machine-wide keys and literature connections, `smairt new` to create a project, and
`smairt menu` inside a project for its dashboard. Screens redraw in place and adapt from a branded
four-card workspace to a compact single-column view as the terminal changes size. Use Up/Down (or
j/k) to move, Enter to accept, Escape to go back exactly one level, and Ctrl-C to stop. The visible
Back row is part of normal arrow navigation and can be selected with Enter. Selection wraps through
that row, and the project home includes a fuzzy action finder that filters commands as you type.

The SMAIRT ASCII wordmark remains the product identity in every layout. Setup → Appearance can add
a responsive PNNL- or UTEP-inspired terminal mark as a small easter egg and apply familiar named
color palettes without changing the terminal background. Institutional names and marks belong to
their respective institutions; these terminal approximations are unofficial and do not imply
endorsement.

See [terminal easter-egg attributions](docs/ATTRIBUTIONS.md) for the complete notice.

For beginners, the workflow hub keeps each screen in the terminal rather than opening a separate
application. Outside a project it helps create or initialize one. Inside a project it opens
research guidance, references, settings, people, environments, safety, and validation tools.

The project wizard first asks whether to create a named child folder or initialize the folder you
already chose. It never treats an unrelated project above a Git worktree as the current project.

For scripts or experienced terminal users, every important setup action also has an explicit
command:

```bash
smairt new my-study --name "My Study" --author "Researcher Name" \
  --confirm-contributor --field Biology --license MIT --no-git
cd my-study
smairt settings show --json
smairt next --json
smairt next --prompt
```

Enable normal shell Tab completion once with `smairt --install-completion`, then restart the shell.
See [Terminal completion](docs/TERMINAL_COMPLETION.md) for supported shells and the local-only
privacy boundary.

## Choose your coding harness

SMAIRT generates a native project adapter for one harness at a time. Scientific records remain
portable when you switch.

| Harness | Best fit | SMAIRT workflow | Review isolation |
| --- | --- | --- | --- |
| Codex | Terminal-first OpenAI agent work | `$smairt-*` skills | Read-only project subagent |
| Zoo Code | Modes and orchestrated handoffs | `/smairt-*` skills | Dedicated review mode |
| Cline | Explicit Plan/Act transitions | `/smairt-*` workflows | Standard read-only subagent |
| OpenCode | Provider-flexible terminal work | `/smairt-*` commands | Read-only project subagent |
| Cursor | IDE-centered research coding | `/smairt-*` skills | Read-only project subagent |
| Claude Code | Terminal-native Claude projects | `/smairt-*` skills | Read-only plan-mode subagent |

Compare them before or after creating a project:

```bash
smairt harness list
smairt harness info codex
smairt harness select cursor --dry-run
```

The detailed [harness chooser](docs/HARNESSES.md) explains setup, hooks, permissions, modes,
cross-model review, and limitations for each tool.

## Human and AI roles

SMAIRT lets an AI assistant propose hypotheses, organize references, draft experiment code, and
assemble review artifacts. The researcher confirms identity, directs or selects hypotheses and
exploratory purposes, decides whether runs support claims, approves corrections, and reviews
manuscript claims. Those choices are recorded as provenance rather than hidden in chat history.

```text
question + references -> grounded background -> proposals -> human selection
-> experiment + iteration -> immutable run -> human decision -> accepted evidence
-> approved claim -> reviewed manuscript
```

A generated project has a recognizable scientific home:

```text
my-study/
├── smairt.yaml             project, people, policy, environment
├── LICENSE                 managed only while its checksum matches
├── background/             questions, descriptions, and source summaries
├── hypotheses/             proposals and selected scientific direction
├── experiments/            readable protocols and analysis code
├── runs/                   immutable execution records
├── evidence/               accepted, superseded, or retracted evidence
├── paper/                  claims and reviewed manuscript builds
└── .smairt/                transactions, provenance, manifests, recovery state
```

## What works today

- Terminal-native global setup, project creation, and a five-area project dashboard.
- Durable project identity, fields of study, license, contributors, and environment settings.
- Reference indexing, research proposals, registered experiments, immutable runs, decisions,
  evidence, claims, and Markdown/DOCX paper builds.
- DOI-first Crossref metadata, optional OpenAlex supplementation, and read-only local or Web
  Zotero imports. Collection imports are bounded; PDFs are copied only when explicitly selected
  from a local Zotero library and validated before one atomic commit.
- Maintained Codex, Zoo Code, Cline, OpenCode, Cursor, and Claude Code adapters with six workflows,
  isolated adversarial review, and truthful hook coverage.
- Bounded OpenAlex and Semantic Scholar discovery, cited-by/reference exploration, DataCite
  not-found fallback, Unpaywall access resolution, and deterministic managed PDF names.
- Schema-8 scientific protocols with declared inputs, outcomes, checksums, run snapshots, and
  interpretation gates before evidence can be accepted.
- Optional native or OpenSSH Slurm submission with typed resources and explicit status, sync, and
  cancel operations; local execution remains the default.
- User-local connection profiles, OS-keyring credentials, and a five-tool, metadata-only MCP
  server for every maintained harness. Shared project YAML contains policy, not account or
  library IDs.
- Transactional writes, mutation locks, recovery journals, validation, safety modes, and adapter
  guidance tailored to each maintained harness.
- Offline project doctor checks and a setup doctor with an explicit opt-in GitHub auth check.

This is beta software. Safety checks are technical guardrails, not institutional, regulatory,
export-control, clinical, or human-subject compliance. Controlled data is not supported as a
compliance claim. Native Windows is not supported; use WSL.

Continue with the [User Guide](docs/USER_GUIDE.md), [CLI Reference](docs/CLI_REFERENCE.md),
[Harness chooser](docs/HARNESSES.md), [Safety contract](docs/SAFETY.md), or
[Architecture](docs/ARCHITECTURE.md).
Developers can use the [Developer Guide](docs/DEVELOPER_GUIDE.md) and [Release Guide](docs/RELEASE.md).
Literature setup and its privacy boundaries are in [Integrations](docs/INTEGRATIONS.md).
Follow the human-run, installation-to-result [SMAIRT demo](DEMO.md). The automated fixture under
`examples/` exists only to keep that walkthrough numerically tested.

SMAIRT itself is distributed under the [MIT License](LICENSE).
