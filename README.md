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

The hard problem of science is not producing more text or code. It is keeping a trustworthy line
from a question, through sources and experiments, to the judgment a researcher is prepared to
defend. AI can help bring researchers quickly to the frontier of science; helping them search, 
summarize, propose, and implement; but the overatching consensus is that it must not quietly become the
author of scientific decisions.

SMAIRT (Scientific Method with AI Research Toolkit, previously Scientific Method with AI Research Template) (at least in this branch) is a local-first 
workspace for that division of labor. It keeps research state in readable YAML, JSON, and Markdown, asks humans to approve the
consequential steps, and gives coding agents a bounded, inspectable place to work.

## Start working

Run the command with no arguments:

```bash
smairt
```
## For Beginners:
The workflow hub stays in your terminal scrollback. Use Up/Down to move, Enter to open or accept,
Escape to go back one level, and Ctrl-C to stop. Outside a project it helps create or initialize
one. Inside a project it opens research guidance, references, settings, people, environments,
safety, and validation scaffolds.

For scripts or experienced terminal local users, every important setup action also has an explicit command:

```bash
smairt new my-study --name "My Study" --author "Researcher Name" \
  --confirm-contributor --field Biology --license MIT --no-git
cd my-study
smairt settings show --json
smairt next --json
```

## Human and AI roles

SMAIRT lets an AI assistant propose hypotheses, organize references, draft experiment code, and
assemble review artifacts. The researcher confirms identity, chooses, edits and guides hypotheses 
as well as exploratory purposes, decides whether runs support a claim, approves corrections, and 
reviews manuscript claims. Those choices are recorded as provenance rather than hidden in chat history.

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

- Terminal-native project creation and a contextual workflow hub.
- Durable project identity, fields of study, license, contributors, and environment settings.
- Reference indexing, research proposals, registered experiments, immutable runs, decisions,
  evidence, claims, and Markdown/DOCX paper builds.
- DOI-first Crossref metadata, optional OpenAlex supplementation, and read-only local or Web
  Zotero imports. Collection imports are bounded; PDFs are copied only when explicitly selected
  from a local Zotero library and validated before one atomic commit.
- OS-keyring credential profiles and a five-tool, metadata-only MCP server for Codex and Zoo.
- Transactional writes, mutation locks, recovery journals, validation, safety modes, and adapter
  guidance for Codex, Zoo Code, and Cline.
- Offline project doctor checks and a setup doctor with an explicit opt-in GitHub auth check.

This is beta software. Safety checks are technical guardrails, not institutional, regulatory,
export-control, clinical, or human-subject compliance. Controlled data is not supported as a
compliance claim. Native Windows is not supported; use WSL.

Continue with the [User Guide](docs/USER_GUIDE.md), [CLI Reference](docs/CLI_REFERENCE.md),
[Safety contract](docs/SAFETY.md), or [Architecture](docs/ARCHITECTURE.md). 
Developers can use the [Developer Guide](docs/DEVELOPER_GUIDE.md) and [Release Guide](docs/RELEASE.md).
Literature setup and its privacy boundaries are in [Integrations](docs/INTEGRATIONS.md).

SMAIRT itself is distributed under the [MIT License](LICENSE).
