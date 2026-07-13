# Terminal workflow hub

The former alternate-screen Textual interface was replaced by an inline Prompt Toolkit workflow
hub. It preserves terminal scrollback and uses Up/Down, Enter, Escape-to-parent, and Ctrl-C.

The hub covers discovery and everyday setup. Expert or human-gated research actions show current
state and the exact CLI handoff instead of maintaining a second research-command implementation.

Automated interaction tests cover real key input, retained creation values, cancellation,
destination preflight, schema-v3 metadata, and managed licenses. Manual release readiness still
includes narrow and normal macOS Terminal widths and WSL.
