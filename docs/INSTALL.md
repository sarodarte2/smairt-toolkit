# Install SMAIRT

SMAIRT supports macOS, Linux, and Windows through WSL. Python 3.11–3.13 is supported; the command
below asks uv to use Python 3.11 for the isolated tool environment.

## 1. Install prerequisites

Install [Git](SETUP_GIT_GITHUB.md) and [uv](https://docs.astral.sh/uv/getting-started/installation/).
Close and reopen the terminal after installing uv so its tool directory is on `PATH`.

## 2. Clone and install

```bash
git clone https://github.com/PNNL-CompBio/smairt-template.git
cd smairt-template
uv tool install --python 3.11 .
smairt --version
```

If `smairt` is not found, run `uv tool update-shell`, reopen the terminal, and try again. To update
from a newer checkout, run `uv tool install --force --python 3.11 .` in that checkout.

## 3. Check the setup

```bash
smairt setup doctor
```

The doctor checks Python, SMAIRT, Git, uv, optional Conda, Git identity, and GitHub CLI visibility.
It stays offline unless you explicitly run `smairt setup doctor --check-github`.

## 4. Start

```bash
smairt
```

Conda is optional for SMAIRT itself. For reproducible experiment environments, install
[Miniforge](SETUP_CONDA.md).

## Credential backends

SMAIRT never stores API-key values in `smairt.yaml`. On macOS it uses Keychain through Python
keyring; the first access may display a system permission prompt. Linux and WSL need a working
Secret Service backend and unlocked session keyring. Headless systems can set `OPENALEX_API_KEY`
or `ZOTERO_API_KEY`; environment variables take precedence over the OS keyring.

```bash
smairt credential doctor
smairt credential set openalex --profile default
```

Zotero Desktop 7 must be running for local access. `smairt integration zotero test` is an explicit
connection test; ordinary doctor and status commands remain offline.
