# Miniforge and Conda

SMAIRT does not require Conda to run. Conda is recommended for research experiment environments,
where dependency isolation matters. Miniforge is the first choice because it defaults to the
conda-forge channel used by generated SMAIRT environments; Miniconda is also compatible.

## Install Miniforge

Download the installer for your operating system and architecture from the
[Miniforge project](https://github.com/conda-forge/miniforge). Follow its interactive installer,
allow shell initialization, then close and reopen the terminal.

Verify:

```bash
conda --version
conda info --envs
smairt setup doctor
```

If Conda is installed but not found, initialize the current shell and reopen it:

```bash
~/miniforge3/bin/conda init
```

Use the actual installation path if yours differs. On managed systems where shell initialization
is not permitted, source `conda.sh` for the current session or select an already configured
environment noninteractively with `smairt env select --mode existing_conda --prefix PATH`.

Miniconda installation instructions are available from the
[official Conda documentation](https://docs.conda.io/projects/conda/en/stable/user-guide/install/).
