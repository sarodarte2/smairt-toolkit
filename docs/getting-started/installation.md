# Install SMAIRT

SMAIRT currently supports macOS, Linux, and Windows through WSL. Python 3.11–3.13 is supported.
Native Windows is not supported in this research preview.

There is no tagged or PyPI release. The supported installation path uses the current source tree.

## Install prerequisites

Install [Git](https://git-scm.com/downloads) and
[uv](https://docs.astral.sh/uv/getting-started/installation/). Close and reopen the terminal after
installing uv so its tool directory is available on `PATH`.

GitHub is optional for local research. If you plan to collaborate through GitHub, install the
[GitHub CLI](https://cli.github.com/) and authenticate with `gh auth login`.

## Install the source preview

```bash
git clone https://github.com/sarodarte2/smairt-toolkit.git
cd smairt-toolkit
uv tool install --python 3.11 .
smairt --version
```

This creates an isolated user-wide `smairt` command. If the command is not found, run
`uv tool update-shell`, reopen the terminal, and try again. To replace an existing source install:

```bash
uv tool install --force --python 3.11 .
```

## Check this machine

```bash
smairt setup doctor --json
```

The setup doctor checks Python, SMAIRT, Git, uv, optional Conda, Git identity, and GitHub CLI
visibility. It remains offline unless you explicitly add `--check-github`.

Open the user-wide setup workspace for guided configuration:

```bash
smairt setup
```

Setup can configure optional profiles for Zotero, OpenAlex, Semantic Scholar, Unpaywall, and Slurm.
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
