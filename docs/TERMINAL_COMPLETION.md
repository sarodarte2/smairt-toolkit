# Terminal completion

SMAIRT has two complementary suggestion surfaces.

Inside `smairt menu`, choose **Find an action** and type any part of an action or command. A fuzzy,
multi-column popup updates beneath the cursor. Suggestions come only from SMAIRT's command catalog
and identifiers already present in the current project. This interaction performs no network
requests, preserves the current menu selection, and returns one level with Escape.

For the ordinary command line, install Typer's native completion once:

```bash
smairt --install-completion
```

Restart the shell afterward. Bash, Zsh, Fish, and PowerShell are supported by the underlying
completion system. Preview the generated script without changing shell configuration with:

```bash
smairt --show-completion
```

Completion suggests command and option names; it never reveals credential values. Keep the normal
terminal font controls: SMAIRT creates hierarchy with spacing, weight, and orange/cyan accents and
does not attempt to resize terminal text.
