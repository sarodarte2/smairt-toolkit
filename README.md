# SMAIRT: Scientific Method with AI Research Template

A cookiecutter template for AI-assisted computational research that follows the scientific method.

---

## Overview

SMAIRT provides a structured framework for doing tightly integrated AI-assisted research. It creates a project structure that:

- Follows the **scientific method** in an iterative loop
- Creates a **breadcrumb trail** so you can feed your entire project back to AI
- Tracks your **intellectual contributions** vs. AI-generated ideas
- Progresses through **synthetic → downloaded → real data** phases
- Records the **4-part structure**: Background, Hypothesis, Methods, Results

---

## Quick Start

```bash
# Install cookiecutter if you haven't already
pip install cookiecutter

# Create a new SMAIRT project
cookiecutter gh:yourusername/smairt-template
```

You'll be prompted for:
- Project name
- Author name and email
- Research question
- Domain (computational biology, machine learning, etc.)
- AI tool (Claude, ChatGPT, etc.)
- Whether to initialize a git repository

---

## Philosophy

### AI's Role

AI excels at regression toward the mean so it can't really innovate in a
meaningful way. But it *can* help you get quickly to the frontier of what's
already known. It helps you:
- Understand very quickly what is working and what isn't
- Suggest approaches that have been tried before
- Iterate through hypothesis-experiment-results-interpretation loops
- Generate code that can be tested immediately

### Your Role

The human contribution remains essential for:
- Making innovative connections
- Identifying truly novel questions
- Recognizing where AI suggestions fall short
- Seeing the gaps that represent real opportunities

---

## The Workflow

SMAIRT follows the scientific method in an iterative loop:

```
Background → Hypothesis → Methods/Code → Results → Analysis → Future Directions
     ↑                                                                │
     └────────────────────────────────────────────────────────────────┘
```

### The 4-Part Structure

The template records **4 pieces of information in separate files**:

1. **Background** - The question, what's known from literature, summary of previous results
2. **Hypothesis** - What is the question you're testing
3. **Methods** - The actual code and data required to test the hypothesis
4. **Results + Interpretation** - The output logs plus analysis through the lens of the hypothesis

Future directions from your analysis feed right back into the **Background** for the next iteration.

### Data Progression

1. **Synthetic data** - Fast iteration, no dependencies
2. **Downloaded benchmark data** - Diversity, validation, robustness
3. **Real data** - Full test of approach

Some questions will be amenable to starting out with tests on synthetic data
to address the most basic questions, they can then move to downloaded publicly
available datasets, and finally to your real data.

---

## Generated Project Structure

```
your_project/
├── docs/
│   ├── SMAIRT_PHILOSOPHY.md       # Core philosophy of the framework
│   └── 12_STEPS.md                # The 12-step guide
│
├── prompts/
│   ├── AI_CONTEXT.md              # Give this to your AI - explains its role
│   ├── CODE_CONVENTIONS.md        # Give this to your AI - code formatting
│   ├── SESSION_START.md           # Ready-to-paste prompts for new sessions
│   ├── 00_priming_prompts.md      # Additional priming prompts
│   ├── session_log.md             # Running log of all prompts + responses
│   └── intellectual_contribution.md  # Track YOUR critical contributions
│
├── background/
│   └── 01_initial_question.md     # Your research question + literature context
│
├── hypotheses/
│   └── hypothesis_log.md          # Track all hypotheses tested
│
├── experiments/
│   ├── 01_synthetic/              # Phase 1: Synthetic data tests
│   ├── 02_downloaded/             # Phase 2: Benchmark data tests
│   └── 03_real_data/              # Phase 3: Real data tests
│
├── results/
│   ├── logs/                      # Output logs (named to match scripts)
│   └── figures/                   # Generated figures
│
├── analysis/
│   ├── iteration_log.md           # Interpretation of results
│   └── future_directions.md       # What to try next
│
├── data/
│   ├── synthetic/
│   ├── downloaded/
│   └── real/
│
├── scripts/
│   ├── compile_for_ai.py          # Compile project state for AI sessions
│   └── new_script.py              # Create new numbered scripts
│
└── paper_draft/
    ├── methods_schematic.md
    └── results_narrative.md
```

---

## Key Features

### The Breadcrumb Trail

Output is pasted at the bottom of scripts as comments. This creates a breadcrumb trail so when you feed the repo back to AI, it can immediately see:
- All the things you've tried
- The different datasets you ran on
- The algorithms you tried
- The prompts that went into it
- What the output was

You can then use the helper script scripts/compile_for_ai.py to combine all the
parts of this breadcrumb trail in to a single text file that can be used to
prompt your AI helper of choice to bring it up to speed on what has been tried,
what worked, what failed, and lead to the next steps.

### Intellectual Contribution Tracking

SMAIRT includes a dedicated file for tracking where YOU made critical insights vs. where AI generated ideas.

"If AI is just generating these ideas and testing them all by itself and moving things forward, your intellectual contribution might be that you pressed the button. But you really need to know where you made those critical steps."

### AI Context Files

The template includes files specifically designed to prime your AI to understand the SMAIRT workflow:
- `prompts/AI_CONTEXT.md` - Explains AI's role and the framework
- `prompts/CODE_CONVENTIONS.md` - How to format code output
- `prompts/SESSION_START.md` - Ready-to-paste prompts for new sessions

---

## Helper Scripts

### compile_for_ai.py

Compiles the current project state into a single document that can be pasted into a new AI session.

```bash
python scripts/compile_for_ai.py
```

### new_script.py

Creates a new numbered script with the standard template, logging setup, and output conventions.

```bash
python scripts/new_script.py
```

Additional helper scripts can be generated on demand using prompts provided in `scripts/README.md`.

---

## Requirements

- Python 3.8 or higher
- cookiecutter (`pip install cookiecutter`)
- git (optional, for repository initialization)

---

## Usage Tips

### Starting a Session

1. Give your AI the context files:
   - `prompts/AI_CONTEXT.md`
   - `prompts/CODE_CONVENTIONS.md`

2. Use the prompts in `prompts/SESSION_START.md` to initialize the session

3. Or run `python scripts/compile_for_ai.py` and paste the output

### Creating New Experiments

```bash
python scripts/new_script.py
```

This will:
- Auto-detect the next script number
- Prompt for phase (synthetic/downloaded/real)
- Prompt for hypothesis being tested
- Create a script with logging already configured

### Recording Results

After running a script:
1. Paste the output in the comment block at the end of the script
2. Add interpretation and next steps
3. Update `prompts/session_log.md`
4. Log your intellectual contributions in `prompts/intellectual_contribution.md`

---

## Template Options

When generating a project, you'll be prompted for:

| Option | Description |
|--------|-------------|
| `project_name` | Human-readable project name |
| `author_name` | Your name |
| `author_email` | Your email |
| `description` | Brief project description |
| `initial_research_question` | The main question you're trying to answer |
| `domain` | computational_biology, machine_learning, data_science, physics, chemistry, other |
| `ai_tool` | claude, chatgpt, copilot, other |
| `include_example` | Include example files (yes/no) |
| `license` | MIT, BSD-3-Clause, Apache-2.0, GPL-3.0, proprietary |
| `create_git_repo` | Initialize a git repository (yes/no) |

---

## The Hard Problem of Science

One of the drivers for SMAIRT is that a very hard problem in science is
identifying the questions that are really cutting edge, that would provide
useful answers, and that are addressable using the data and tools available.

SMAIRT is a great method for exploring a question to answer those points
and rapidly identify the most interesting research directions. AI can enable
you to very quickly explore that space and find potential frontiers and gaps
that are worthy of further research and innovation.

The SMAIRT framework is set up to provide a reasonable tracking method using
the scientific method, that will provide a reproducible (-ish, depending on AI
output) process for scientific discovery.
---

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

## License

This template is released under the MIT License. Projects generated from this template can use any license you choose.

---

## Acknowledgments

SMAIRT was developed based on practical experience doing AI-assisted computational research, with the goal of creating a structured approach that captures the benefits of AI collaboration while maintaining clear documentation of human intellectual contributions.
