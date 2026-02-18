# Priming Prompts for {{ cookiecutter.project_name }}

## First Time Setup

At the start of your first session, ask AI to read:
1. `prompts/AI_CONTEXT.md` - Framework understanding
2. `prompts/CODE_CONVENTIONS.md` - How to format output
3. `background/01_initial_question.md` - The research question

## Session Start Prompt

See `prompts/SESSION_START.md` for ready-to-paste prompts.

## Quick Priming Prompt

If you need something shorter:
This is a SMAIRT project (Scientific Method with AI Research Template).

Key conventions:

Scripts named: script_XX_description.py
Output to console AND results/logs/
Paste output as comments at end of scripts
Follow: Background → Hypothesis → Methods → Results → Analysis → Future Directions
Current iteration: [X]
Phase: [synthetic/downloaded/real]
Hypothesis: [Y]

[Your request here]

## Interpretation Prompt

After running an experiment:
Results from script_XX:

[Paste output]

Interpret through the lens of the hypothesis: [State hypothesis]

Does this support or refute the hypothesis?
Where does this approach work "within certain boundaries"?
Where does it break down?
What are logical next experiments?

## Compile Context Prompts

When context gets long:
Please run scripts/compile_for_ai.py and I'll paste the output so you have full project context.
