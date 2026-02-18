# {{ cookiecutter.project_slug }}/prompts/CODE_CONVENTIONS.md

```markdown
# Code Conventions for This Project

When generating code for this project, follow these conventions.

---

## Script Naming

Use numbered scripts for each round:

```
script_XX_brief_description.py
```

Examples:
- `script_01_initial_synthetic_test.py`
- `script_02_add_noise_robustness.py`
- `script_03_iris_benchmark.py`
- `script_04_real_data_validation.py`

This provides a clear timeline of what was tried and allows very rapid turnaround time.

---

## Required Output Format

Every script should:

1. **Print to console** for immediate feedback
2. **Write to log file** at `../../results/logs/script_XX_description_output.log`
3. **Include a results comment block** at the end for pasting output

"It should provide output on the command line but really it should provide an output log file that is named the same thing as the script. That way you have all the log files in one place and you have the scripts which are closely associated with that."

---

## Script Template

```python
#!/usr/bin/env python
"""
Script XX: Brief description of what this script tests
Hypothesis: [What we're testing]
Phase: synthetic / downloaded / real
Iteration: [X]
"""

import os
import sys
from datetime import datetime

# === CONFIGURATION ===
SCRIPT_NAME = "script_XX_description"
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "results", "logs")

# === LOGGING SETUP ===
class Logger:
    """Log to both console and file."""
    def __init__(self, log_path):
        self.terminal = sys.stdout
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self.log_file = open(log_path, "w")

    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()

    def close(self):
        self.log_file.close()

# === MAIN CODE ===
def main():
    # Setup logging
    log_path = os.path.join(LOG_DIR, f"{SCRIPT_NAME}_output.log")
    sys.stdout = Logger(log_path)

    print(f"{'='*60}")
    print(f"Script: {SCRIPT_NAME}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Hypothesis: [STATE HYPOTHESIS HERE]")
    print(f"{'='*60}")
    print()

    # ========================================
    # YOUR CODE HERE
    # ========================================



    # ========================================
    # END YOUR CODE
    # ========================================

    print()
    print(f"{'='*60}")
    print("=== COMPLETE ===")
    print(f"{'='*60}")

    # Close logger
    sys.stdout.close()
    sys.stdout = sys.__stdout__

if __name__ == "__main__":
    main()


# === PASTE OUTPUT HERE ===
"""
[After running, paste the console output here as a comment]
[This creates a breadcrumb trail for future AI sessions]

=== OUTPUT ===


=== INTERPRETATION ===
[Add your interpretation of the results]
[Did this support or refute the hypothesis?]
[Where did the approach work "within certain boundaries"?]
[Where did it break down?]

=== NEXT STEPS ===
[What should we try next based on these results?]

"""
```

---

## The Breadcrumb Trail

"I took the output of that script and I pasted it in at the bottom of the end of the code and made it into comments. That's to provide a record for me so I can go back and say 'oh that's what the output was.' But almost more importantly it's to provide a record for AI."

"You can then take your repo and feed it back in and Claude or whatever tool will immediately be able to say 'oh here are all the things we tried, here's the different datasets that we ran it on, here's the algorithms we tried, here's the prompts that went into it, and here's what the output was.' Now I can recreate the thought process through this whole thing and come out on the other end basically starting right up where you were."

"It's a breadcrumb trail that allows you to get right back to where you started from—even if you start in a completely new thread, even if you give it to a new API."

---

## Results Comment Block

At the end of every script, include this block:

```python
# === PASTE OUTPUT HERE ===
"""
=== OUTPUT ===
[Paste console output here]

=== INTERPRETATION ===
[Did this support the hypothesis?]
[What worked? Within what boundaries?]
[What didn't work? Where did it break?]

=== NEXT STEPS ===
[What should we try next?]
"""
```

---

## Log File Naming

Log files go in `results/logs/` and should match script names:

| Script | Log File |
|--------|----------|
| `script_01_initial_test.py` | `script_01_initial_test_output.log` |
| `script_02_add_noise.py` | `script_02_add_noise_output.log` |
| `script_03_benchmark.py` | `script_03_benchmark_output.log` |

---

## Directory Conventions

Place scripts in the appropriate phase directory:

```
experiments/
├── 01_synthetic/      # Phase 1: Synthetic data tests
│   ├── script_01_xxx.py
│   └── script_02_xxx.py
├── 02_downloaded/     # Phase 2: Benchmark data tests
│   ├── script_03_xxx.py
│   └── script_04_xxx.py
└── 03_real_data/      # Phase 3: Real data tests
    ├── script_05_xxx.py
    └── script_06_xxx.py
```

---

## Data Validation

Include data validation checks where appropriate:

```python
# Validate input data
assert data is not None, "Data failed to load"
assert len(data) > 0, "Data is empty"
print(f"Loaded {len(data)} samples")
print(f"Data shape: {data.shape}")
print(f"Data types: {data.dtypes}")
```

---

## Documenting Limitations

When results show limited success, document where and why:

```python
# === LIMITATIONS OBSERVED ===
# - Works on synthetic data up to X% accuracy
# - Breaks down when noise > Y%
# - Not robust to Z
# - "They work within certain boundaries and then they stop working"
```

---

## The 4-Part Structure in Code

Remember that each script is part of the 4-part structure:

1. **Background** → documented in `background/` folder
2. **Hypothesis** → stated in script docstring
3. **Methods** → the script itself (code + data)
4. **Results** → the output log + pasted output + interpretation

"The methods are the actual code—the code and the data that's required to run to test this experiment. So the hypothesis, the methods are the experimental design and the methods to get there. And then the results—the results is the log file."
```
