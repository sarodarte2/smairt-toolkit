# Git and GitHub setup

Git stores project history locally. A GitHub account and the GitHub CLI are useful for private
collaboration, but are not required for local SMAIRT work.

## Install and identify yourself

Install Git using the [official Git guide](https://git-scm.com/downloads), then configure the name
and email that should appear in commits:

```bash
git config --global user.name "Researcher Name"
git config --global user.email "researcher@example.org"
git config --global --list
```

## Connect to GitHub with HTTPS

Install the [GitHub CLI](https://cli.github.com/), then use the beginner-friendly HTTPS flow:

```bash
gh auth login
```

Choose GitHub.com, HTTPS, and browser authentication. Verify only when you intend to contact
GitHub:

```bash
gh auth status
smairt setup doctor --check-github
```

SSH keys are a useful advanced alternative; follow GitHub's
[SSH guide](https://docs.github.com/en/authentication/connecting-to-github-with-ssh).
