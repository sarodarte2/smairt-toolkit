# Terminal completion

SMAIRT has two complementary suggestion surfaces.

Inside `smairt menu`, choose **Find an action** and type any part of an action or command. A fuzzy,
multi-column popup updates beneath the cursor. Suggestions come only from SMAIRT's command catalog
and identifiers already present in the current project. This interaction performs no network
requests, preserves the current menu selection, and returns one level with Left or Escape. Every
menu also has a Back row that can be reached with Up/Down and selected with Enter.

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
terminal font controls: SMAIRT creates hierarchy with spacing, weight, and configurable accents and
does not attempt to resize terminal text. Setup → Appearance offers Scientific, PNNL, UTEP,
Matrix, Dracula, Nord, Solarized, Amber, High Contrast, Monochrome, and Custom palettes. The SMAIRT
wordmark remains visible; optional institutional or custom marks are secondary and responsive.
These preferences live only in the user-local SMAIRT configuration and do not change a research
project or the terminal background.

Institutional names and marks belong to their respective institutions. The included terminal
approximations are unofficial easter eggs and do not imply endorsement.
