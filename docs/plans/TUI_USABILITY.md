# TUI usability roadmap

## Current friction

The current Textual interface is visually isolated in a large bordered card and exposes a long
form before establishing a clear step or focus path. It also discovers Conda environments during
application construction and creates projects synchronously in the button handler. Both operations
can block painting and keyboard response, producing the reported choppy feel.

The project menu is an editable metadata form rather than a working research dashboard. It shows
counts but not the recommended next action, active contributor, harness, safety state, or direct
actions. Feedback is written into a static message region, so progress and errors can be easy to
miss in a real terminal.

## Design direction

The TUI should feel like a native command surface, not a modal desktop form inside a terminal:

- use the terminal background and restrained separators instead of a full-screen colored card;
- keep a compact command/status header and an always-visible one-line help/footer region;
- support predictable Tab/Shift-Tab focus, Enter to continue, Escape to go back, and `q` to exit;
- use progressive steps for creation: location, research identity, policy/harness, then review;
- show validation beside the field that needs correction and preserve entered values when moving
  backward;
- show non-blocking progress for environment discovery, validation, and project creation;
- make the project dashboard action-oriented around `smairt next`, not primarily metadata editing.

## Implementation phases

### Phase 1 — responsiveness and terminal integration

1. Move Conda discovery and scaffold creation into Textual workers.
2. Disable only the relevant action while work runs and show a `LoadingIndicator` plus concise
   status text.
3. Add bindings for quit, back, refresh, and submit; expose them in the footer.
4. Replace broad exception handling with expected domain errors and a concise error notification.
5. Respect terminal width with narrow-layout CSS and avoid a fixed 78-column form.

Acceptance: first paint does not wait for Conda; repeated submit cannot duplicate work; resizing to
80x24 keeps primary actions and current status visible; keyboard-only creation is deterministic.

### Phase 2 — guided creation flow

1. Split the long form into four screens or step containers with a visible `1/4` progress marker.
2. Validate each step before advancing and focus the first invalid field.
3. Replace the preview toggle state with a dedicated review step showing destination, safety,
   harness ownership, contributor confirmation, environment work, and Git effects.
4. Add a success screen with the project path and recommended first command.

Acceptance: a first-time user can explain what will be written before confirming and can return to
change any choice without losing other input.

### Phase 3 — research dashboard

1. Lead with active contributor, active hypothesis/purpose, current iteration, validation health,
   harness, safety mode, and the recommendation from `next_guidance`.
2. Add commands for opening the recommended artifact, refreshing, validating, switching
   contributor, and returning to the shell with a copyable CLI command.
3. Keep project-detail editing as a secondary screen.
4. Use notifications for success/failure and a small log panel for long-running actions.

Acceptance: the dashboard answers “where am I, is it safe, and what should I do next?” without
requiring the user to leave the TUI.

## Verification

- Add Textual pilot tests for focus order, bindings, narrow terminal layout, validation, worker
  completion, failure recovery, and duplicate-submit prevention.
- Mock Conda discovery and project creation; do not make tests depend on a local Conda install.
- Run a manual smoke matrix at 80x24, 120x30, and 160x45 in macOS Terminal, iTerm2, and a basic SSH
  terminal before declaring the redesign complete.
