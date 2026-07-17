# Install SMAIRT

SMAIRT currently supports macOS, Linux, and Windows through WSL. Python 3.11–3.13 is supported.
Native Windows is not supported in this research preview.

There is no tagged or PyPI release. The supported installation path uses the current source tree.

## Open a terminal and install prerequisites

SMAIRT is terminal-native, but you do not need to know Python. Open Terminal on macOS, your usual
terminal on Linux, or a Linux terminal inside WSL. Commands below can be copied and pasted.

Install [Git](https://git-scm.com/downloads) and
[uv](https://docs.astral.sh/uv/getting-started/installation/). Close and reopen the terminal after
installing uv so its tool directory is available on `PATH`.

GitHub is optional for local research. If you plan to collaborate through GitHub, install the
[GitHub CLI](https://cli.github.com/) and authenticate with `gh auth login`.

## Install the source preview

```bash
uv tool install --python 3.11 git+https://github.com/sarodarte2/smairt-toolkit.git
smairt
```

uv manages the compatible Python runtime and creates an isolated user-wide `smairt` command. If the command is not found, run
`uv tool update-shell`, reopen the terminal, and try again. To replace an existing source install:

```bash
uv tool install --force --python 3.11 git+https://github.com/sarodarte2/smairt-toolkit.git
```

## Check this machine

Choose **Set up SMAIRT** from Home. The guided check separates required readiness from conditional
and optional capabilities, explains problems in plain language, and supports retesting. It remains
offline unless you explicitly request a network check.

The optional starter profile stores only values you enter: contributor identity, usual project
parent, fields of study, and preferred AI assistant. Blank values never prefill a project.

Later setup can configure optional profiles for Zotero, OpenAlex, Semantic Scholar, Unpaywall, and Slurm.
Connection identities stay in the operating system's user configuration area; secrets stay in
environment variables or the OS keyring. A project later chooses which local profile it uses.

## Optional Conda environments

SMAIRT does not require Conda. It can use Conda to isolate experiment dependencies. Miniforge is
the recommended distribution because it defaults to conda-forge; Miniconda is also compatible.

Install Miniforge from the [official project](https://github.com/conda-forge/miniforge), allow shell
initialization, reopen the terminal, and verify:

```bash
conda --version
conda info --envs
smairt setup doctor --json
```

If an existing installation is not on `PATH`, run the appropriate `conda init` command from its
installation directory or select an already configured prefix when creating the project.

## Credential storage

SMAIRT never stores API-key values in `smairt.yaml`. macOS uses Keychain through Python keyring.
Linux and WSL need a working Secret Service backend and an unlocked session keyring. Headless
systems may use the documented environment variables; environment variables take precedence over
keyring values.

```bash
smairt setup credential list
smairt setup credential doctor
```

Local Zotero access requires Zotero Desktop 7 to be running with its local API enabled. Ordinary
doctor and project-status commands do not test remote or local provider connections implicitly.

Continue with the [Quickstart](quickstart.md).
