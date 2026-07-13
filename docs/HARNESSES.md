# Harness Adapters

SMAIRT supports exactly one active harness per project: Codex, Zoo Code, or Cline. The active
adapter is stored in `smairt.yaml`; portable scientific records do not change when the harness
changes.

Always preview a switch. The preview classifies files as created/updated, removed, locally
modified, conflicting, or preserved custom content. SMAIRT removes only unchanged paths in its
ownership manifest. It never removes an adapter directory wholesale.

`AGENTS.md` contains a marked shared SMAIRT block. Researchers may add durable project rules
outside that block. Zoo and Cline native rules contain only harness-specific behavior to avoid
duplicating the shared block.

Provider profiles, API keys, and concrete model selections remain user settings. Zoo users bind
profiles to modes in Zoo. Cline users may configure separate Plan/Act or CLI profiles. Codex users
choose an available model and reasoning effort. `smairt model recommend` supplies the portable
capability tier.

Future adapters, including Claude Code, must implement the same adapter registry contract:
managed paths, shared instruction blocks, conflict reporting, activation/deactivation, health
checks, capabilities, and model guidance.
