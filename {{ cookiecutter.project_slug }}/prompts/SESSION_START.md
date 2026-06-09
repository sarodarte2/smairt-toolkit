# {{ cookiecutter.project_slug }}/prompts/SESSION_START.md

```markdown
# Session Start Prompts

Ready-to-paste prompts for starting new AI sessions.

---

## First Session Prompt

Use this for the very first session on a new project:

```
I'm starting a new research project called "{{ cookiecutter.project_name }}" using the SMAIRT framework (Scientific Method with AI Research Template).

Please read and understand these files:
- `prompts/AI_CONTEXT.md` - Your role and the SMAIRT workflow
- `prompts/CODE_CONVENTIONS.md` - How to format code output
- `prompts/KNOWN_PATTERNS.md` - Reusable code patterns and common errors to avoid

Research Question: {{ cookiecutter.initial_research_question }}

The SMAIRT framework follows the scientific method in an iterative loop:
Background → Hypothesis → Methods/Code → Results → Analysis → Future Directions → (repeat)

We record 4 pieces of information in separate files:
1. Background - The question, what's known from literature, summary of previous results
2. Hypothesis - What we're testing (could be at end of background)
3. Methods - The actual code and data required to test the hypothesis
4. Results - The log file output plus interpretation

For all code you generate:
1. Use numbered script naming: script_XX_brief_description.py
2. Output to both console AND a log file in results/logs/
3. Include a comment block at the end for pasting results

If I'm starting with real data you should prompt me about that data.
If I have code that I've written that would be useful you
should ask me about that.

Please help me:
1. Refine the research question
2. Identify what's known about this area
3. Formulate an initial hypothesis
4. Design the first experiment
```

---

## Continuing Session Prompt

Use this when starting a new session on an existing project:

```
I'm continuing work on "{{ cookiecutter.project_name }}" - a SMAIRT project.

Please review:
- `prompts/AI_CONTEXT.md` - Your role and the workflow
- `prompts/CODE_CONVENTIONS.md` - Code formatting conventions
- `prompts/KNOWN_PATTERNS.md` - Reusable patterns and errors to avoid

Current state:
- **Iteration:** [X]
- **Phase:** [synthetic / downloaded / real]
- **Hypothesis being tested:** [State it]
- **Last experiment:** [script_XX_description.py]
- **Last result:** [Brief summary of what happened]

Here's the recent session log:
[Paste relevant entries from prompts/session_log.md]

Here's the current hypothesis log:
[Paste from hypotheses/hypothesis_log.md]

Current limitations identified:
[Paste from analysis/iteration_log.md]

Please help me design the next experiment.
```

---

## Quick Context Reload Prompt

A shorter version when context is fresh:

```
Continuing "{{ cookiecutter.project_name }}" - SMAIRT project.

Iteration [X], Phase [synthetic/downloaded/real].
Hypothesis: [State hypothesis]
Last result: [What happened]

[Paste recent output or session_log entries]

What should we try next?
```

---

## Full Context Reload Prompt

When you need to bring AI fully up to speed:

```
I'm continuing work on "{{ cookiecutter.project_name }}" using the SMAIRT framework.

I'll paste the compiled project state from scripts/compile_for_ai.py:

[Paste output from compile_for_ai.py]

Please review this context and help me continue from where we left off.
```

---

## Interpretation Prompt

Use after running an experiment:

```
I just ran script_XX and here are the results:

[Paste output]

The hypothesis we were testing: [State hypothesis]

Please help me interpret these results:
1. Do they support or refute the hypothesis?
2. Where does this approach work "within certain boundaries"?
3. Where does it break down or stop working?
4. What limitations or caveats should I note?
5. What are the logical next experiments to try?
6. Are there any surprising observations worth investigating?
```

---

## Dead End Prompt

When you seem to be at a dead end:

```
We seem to be at a dead end with the current approach.

What we've tried:
[List approaches from session_log.md]

Where things break down:
[Describe limitations]

The original hypothesis was: [State it]
The research question is: [State it]

Can you suggest:
1. Alternative approaches we haven't considered?
2. Ways to reframe the problem?
3. Related problems in other domains that might have solutions?
4. Whether we should adjust the hypothesis?

Note: This is where I need to be especially attentive to making my own intellectual contribution. You may suggest things, but I'll evaluate whether they represent truly innovative directions or just variations on what we've tried.
```

---

## Phase Transition Prompt

When moving from synthetic → downloaded or downloaded → real:

```
We're transitioning from [synthetic/downloaded] data to [downloaded/real] data.

Summary of what worked in the previous phase:
[Paste from analysis/iteration_log.md]

Hypothesis that was supported:
[State it]

Limitations identified:
[List them]

For the next phase, please help me:
1. Identify appropriate [benchmark datasets / real data] to test on
2. Adapt the approach for this new data
3. Design experiments that will validate whether results transfer
```

---

## Priming Reminders

If AI forgets conventions mid-session:

```
Reminder - SMAIRT conventions:
- Script naming: script_XX_brief_description.py
- Output to console AND results/logs/
- Include comment block at end for pasting results
- Evaluate results through the lens of the hypothesis
- Note where approaches work "within certain boundaries" and where they break
- Check prompts/KNOWN_PATTERNS.md before writing code (reuse patterns, avoid known errors)
- After resolving new errors, suggest adding them to KNOWN_PATTERNS.md
```

---

## Tips for Effective Sessions

1. **Start each session by providing context** - AI doesn't remember previous sessions
2. **Feed the breadcrumb trail back** - Paste previous outputs and session logs
3. **State the current hypothesis clearly** - All interpretation should be through this lens
4. **Track your intellectual contributions** - Note when YOU make critical suggestions vs. AI
5. **Document dead ends** - These are valuable for future sessions

The documentation you create serves as a breadcrumb trail, allowing you to return to your current state even when starting a completely new thread or switching to a different AI tool.
```
