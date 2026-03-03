# SMAIRT Git Best Practices

## A) Single-User Use Case

### File Creation Timeline

**At Project Start:**
1. `background/01_initial_question.md` - Define your research question
2. `hypotheses/hypothesis_log.md` - Record your first hypothesis
3. `prompts/session_log.md` - Begin logging your first AI session
4. `prompts/intellectual_contribution.md` - Start tracking your contributions

**At Each Iteration:**
1. Create script: `experiments/[phase]/script_XX_description.py`
2. Run and paste output as comments at bottom of script
3. Update `hypotheses/hypothesis_log.md` with results (supported/not supported)
4. Update `analysis/iteration_log.md` with interpretation
5. Update `analysis/future_directions.md` for next iteration
6. Update `prompts/session_log.md` with prompts and responses
7. Update `prompts/intellectual_contribution.md` with YOUR critical insights

**At Phase Transitions (synthetic → downloaded → real):**
1. Create `background/iteration_XX_background.md` summarizing what was learned
2. Archive or tag the phase completion

### Git Workflow

```
# Commit cadence: Once per completed iteration

# Pattern for commit messages:
git commit -m "Iteration XX: [hypothesis tested] - [result: supported/refuted]"

# Example commits:
git commit -m "Iteration 01: Test linear separability on synthetic data - supported"
git commit -m "Iteration 02: Add noise robustness test - partial support, breaks >20% noise"
git commit -m "Iteration 03: Validate on Iris benchmark - supported"
```

**Tagging Strategy:**
```bash
# Tag phase completions
git tag -a "phase-synthetic-complete" -m "Synthetic phase complete. Key findings: [summary]"
git tag -a "phase-downloaded-complete" -m "Benchmark validation complete"
git tag -a "v1.0-initial-findings" -m "First complete cycle through all phases"
```

**Branch Strategy (optional for single user):**
- Keep it simple: work on `main`
- Use branches only for exploratory tangents you might abandon
```bash
git checkout -b explore/alternative-algorithm
# If it works, merge back; if not, leave as documentation of what didn't work
```

### Recommended Commit Points

| Event | Commit? | Message Pattern |
|-------|---------|-----------------|
| New hypothesis formulated | ✓ | "Hypothesis XX: [brief statement]" |
| Script created and run | ✓ | "Iteration XX: [script name] - [result]" |
| Dead end reached | ✓ | "Dead end: [approach] - [why it failed]" |
| Phase transition | ✓ + Tag | "Complete [phase] phase" |
| Major insight | ✓ | "Insight: [discovery]" |
| Session log updated | Bundle with iteration | — |

---

## B) Collaborative Use Case

### Branch Strategy

```
main
├── user-alice/iteration-XX      # Alice's current work
├── user-bob/iteration-YY        # Bob's current work
└── experiments/[topic-branch]   # Shared experimental branches
```

**Workflow:**
1. Each user works on their own branch
2. Merge to `main` only when an iteration is **complete** (hypothesis tested, results interpreted)
3. Pull from `main` before starting new iterations to get others' findings

### File Ownership & Conventions

**Shared Files (merge carefully):**
- `hypotheses/hypothesis_log.md` - Append only, use clear headers
- `analysis/iteration_log.md` - Append only, attribute entries
- `analysis/future_directions.md` - Can be edited by anyone
- `background/` files - Additions welcome, edits need discussion

**User-Specific Files:**
```
prompts/
├── session_log.md                    # SHARED - append with user attribution
├── session_log_alice.md              # Alice's detailed logs
├── session_log_bob.md                # Bob's detailed logs
├── intellectual_contribution.md       # SHARED - append with user attribution
└── intellectual_contribution_alice.md # Alice's detailed contributions
```

**Script Numbering Convention:**
```
# Option 1: Global numbering with user prefix
script_01_alice_initial_test.py
script_02_bob_alternative_approach.py

# Option 2: User-specific numbering ranges
# Alice: 01-49, Bob: 50-99, Carol: 100-149
script_01_initial_test.py      # Alice
script_50_different_approach.py # Bob
```

### Merge Conflict Prevention

**Structure entries for easy merging:**

```markdown
<!-- In hypothesis_log.md -->
## Iteration 5 (Alice, 2024-01-15)
- **Hypothesis:** ...
- **Result:** ...

---

## Iteration 6 (Bob, 2024-01-16)
- **Hypothesis:** ...
- **Result:** ...
```

**Use append-only pattern for logs:**
```markdown
<!-- In session_log.md -->
# Session Log

---
## Alice - Session 2024-01-15
[content]

---
## Bob - Session 2024-01-16
[content]
```

### Collaborative Git Workflow

```bash
# Starting new work
git checkout main
git pull origin main
git checkout -b user-alice/iteration-05

# Do your iteration work...
# Create scripts, run experiments, update logs

# Before merging
git checkout main
git pull origin main
git checkout user-alice/iteration-05
git rebase main  # or merge main into your branch

# Merge completed iteration
git checkout main
git merge user-alice/iteration-05
git push origin main

# Tag collaborative milestones
git tag -a "collab-v1.0" -m "Team consensus: [finding]. Contributors: Alice, Bob"
```

### Communication Protocol

**Required Updates for Each Merge to Main:**

1. **Hypothesis log entry** with your name and date
2. **Iteration log entry** with interpretation
3. **Future directions update** if you identified new paths
4. **Brief summary in commit message** so others can scan git log

**Async Communication File (optional):**
```markdown
<!-- coordination/COLLABORATION_LOG.md -->
## Active Work

| User | Current Iteration | Hypothesis | ETA |
|------|------------------|------------|-----|
| Alice | 05 | Testing noise robustness | 2024-01-17 |
| Bob | 06 | Alternative algorithm | 2024-01-18 |

## Decisions Needed
- [ ] Should we pivot to downloaded data? (raised by Alice, 2024-01-15)

## Recent Findings to Note
- Bob's iteration 04 found the approach breaks above 30% noise - important constraint
```

### Intellectual Contribution Tracking (Collaborative)

This becomes especially important with multiple contributors:

```markdown
<!-- intellectual_contribution.md -->
## Iteration 5 (Alice)
### My Contributions
- Suggested testing with correlated noise (not just i.i.d.)
- Identified that Bob's result from Iter 04 implied we need regularization

### AI Contributions
- Generated the test harness code
- Suggested three approaches (I chose option 2)

### Collaborative Contributions
- Built on Bob's noise threshold finding from Iteration 04
```

---

## Summary Comparison

| Aspect | Single User | Collaborative |
|--------|-------------|---------------|
| Branch strategy | Main only (+ optional exploration branches) | User branches, merge completed iterations |
| Commit frequency | Per iteration | Per iteration, coordinate merges |
| Session logs | Single file | Per-user files + shared summary |
| Script numbering | Sequential | Prefixed or range-based |
| Hypothesis log | Simple append | Attributed, dated append |
| Intellectual contribution | Track yours vs AI | Track yours vs AI vs collaborators |
| Tags | Phase milestones | Phase + team consensus points |

The key principle for both cases: **the breadcrumb trail should be clear enough that anyone (including a new AI session) can reconstruct the full thought process and continue from where you left off.**
