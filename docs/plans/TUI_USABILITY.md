# Terminal workflow UX

The inline Prompt Toolkit interface keeps the normal terminal buffer while redrawing one anchored
viewport. Submenus replace the current frame instead of walking down the terminal. Global setup,
project creation, and the project dashboard have distinct entry points. It uses circular Up/Down
and j/k navigation, Enter, Escape-to-parent, and Ctrl-C.

The frame responds to terminal width and height. Narrow terminals use a compact `◆ SMAIRT`
identity, medium terminals use a full-width heading, and wide terminals use an original ASCII
wordmark beside neofetch-style project status. Motion is a brief first-entry reveal only and can
be disabled under Setup → Appearance or with `SMAIRT_REDUCED_MOTION=1`.

The dashboard uses compact cards and five non-overlapping areas: Continue research, References,
Project setup, Health, and Advanced. References explain and receipt each mutation. Health favors a
concise result and remediation over raw diagnostic dumps. Recommended work includes a bounded,
context-aware prompt without crossing human gates.

Automated interaction tests cover real key input, retained creation values, cancellation,
destination preflight, schema-v6 migration, responsive branding, circular navigation, and managed licenses. Manual release readiness still
includes narrow and normal macOS Terminal widths and WSL.
