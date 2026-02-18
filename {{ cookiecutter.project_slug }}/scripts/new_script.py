#!/usr/bin/env python
"""
new_script.py

Creates a new numbered script with the standard SMAIRT template.
Auto-detects the next script number based on existing scripts.

"I kept individual scripts they were numbered for each round that I did."

"It should provide output on the command line but really it should provide
an output log file that is named the same thing as the script."
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime

def get_project_root():
    """Get the project root directory (parent of scripts folder)."""
    return Path(__file__).parent.parent

def get_next_script_number(experiments_dir):
    """Find the highest script number across all phases and return next number."""
    max_num = 0

    for phase_dir in experiments_dir.iterdir():
        if phase_dir.is_dir() and not phase_dir.name.startswith('.'):
            for script in phase_dir.glob("script_*.py"):
                match = re.match(r"script_(\d+)", script.name)
                if match:
                    num = int(match.group(1))
                    max_num = max(max_num, num)

    return max_num + 1

def get_phase_choice():
    """Prompt user to select a phase."""
    print("\nSelect phase:")
    print("  1. synthetic   (01_synthetic)   - Fast iteration, no dependencies")
    print("  2. downloaded  (02_downloaded)  - Benchmark data, validation")
    print("  3. real        (03_real_data)   - Actual target data")
    print()

    while True:
        choice = input("Enter choice [1/2/3]: ").strip()
        if choice == "1":
            return "01_synthetic"
        elif choice == "2":
            return "02_downloaded"
        elif choice == "3":
            return "03_real_data"
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def get_script_description():
    """Prompt user for script description."""
    print("\nEnter a brief description for the script.")
    print("This will be used in the filename: script_XX_<description>.py")
    print("Use lowercase with underscores, no spaces.")
    print()

    while True:
        description = input("Description: ").strip().lower().replace(" ", "_")
        description = re.sub(r'[^a-z0-9_]', '', description)

        if description:
            return description
        else:
            print("Description cannot be empty.")

def get_hypothesis():
    """Prompt user for the hypothesis being tested."""
    print("\nWhat hypothesis are you testing with this script?")
    print("(This will be included in the script docstring)")
    print()

    hypothesis = input("Hypothesis: ").strip()
    return hypothesis if hypothesis else "[STATE HYPOTHESIS HERE]"

def get_iteration():
    """Prompt user for the iteration number."""
    print("\nWhat iteration is this? (Enter a number)")
    print()

    while True:
        iteration = input("Iteration [1]: ").strip()
        if not iteration:
            return "1"
        if iteration.isdigit():
            return iteration
        print("Please enter a valid number.")

def create_script(phase_dir, script_num, description, hypothesis, iteration):
    """Create the script file with the standard template."""

    script_name = f"script_{script_num:02d}_{description}"
    script_path = phase_dir / f"{script_name}.py"

    template = f'''#!/usr/bin/env python
"""
Script {script_num:02d}: {description.replace('_', ' ').title()}
Hypothesis: {hypothesis}
Phase: {phase_dir.name}
Iteration: {iteration}
Created: {datetime.now().isoformat()}
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# === CONFIGURATION ===
SCRIPT_NAME = "{script_name}"
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOG_DIR = PROJECT_ROOT / "results" / "logs"

# === LOGGING SETUP ===
class Logger:
    """Log to both console and file."""

    def __init__(self, log_path):
        self.terminal = sys.stdout
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_file = open(log_path, "w")

    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()

    def close(self):
        self.log_file.close()
        sys.stdout = self.terminal


# === MAIN CODE ===
def main():
    # Setup logging
    log_path = LOG_DIR / f"{{SCRIPT_NAME}}_output.log"
    logger = Logger(log_path)
    sys.stdout = logger

    print("=" * 60)
    print(f"Script: {{SCRIPT_NAME}}")
    print(f"Timestamp: {{datetime.now().isoformat()}}")
    print(f"Hypothesis: {hypothesis}")
    print("=" * 60)
    print()

    # ========================================
    # YOUR CODE HERE
    # ========================================

    print("TODO: Implement experiment")

    # Example output format:
    # print(f"Results:")
    # print(f"  - Metric 1: {{value}}")
    # print(f"  - Metric 2: {{value}}")

    # ========================================
    # END YOUR CODE
    # ========================================

    print()
    print("=" * 60)
    print("=== COMPLETE ===")
    print(f"Log saved to: {{log_path}}")
    print("=" * 60)

    # Close logger
    logger.close()


if __name__ == "__main__":
    main()


# === PASTE OUTPUT HERE ===
"""
[After running, paste the console output here as a comment]
[This creates a breadcrumb trail for future AI sessions]

=== OUTPUT ===


=== INTERPRETATION ===
[Did this support or refute the hypothesis?]
[Where did the approach work "within certain boundaries"?]
[Where did it break down?]

=== NEXT STEPS ===
[What should we try next based on these results?]

"""
'''

    script_path.write_text(template)
    return script_path

def main():
    """Main entry point."""
    root = get_project_root()
    experiments_dir = root / "experiments"

    print("=" * 60)
    print("SMAIRT New Script Generator")
    print("=" * 60)

    # Get next script number
    next_num = get_next_script_number(experiments_dir)
    print(f"\nNext script number: {next_num:02d}")

    # Get user inputs
    phase = get_phase_choice()
    description = get_script_description()
    hypothesis = get_hypothesis()
    iteration = get_iteration()

    # Create the script
    phase_dir = experiments_dir / phase
    phase_dir.mkdir(parents=True, exist_ok=True)

    script_path = create_script(phase_dir, next_num, description, hypothesis, iteration)

    # Summary
    print()
    print("=" * 60)
    print("Script created successfully!")
    print("=" * 60)
    print(f"  Path: {script_path}")
    print(f"  Phase: {phase}")
    print(f"  Hypothesis: {hypothesis}")
    print(f"  Iteration: {iteration}")
    print()
    print("Next steps:")
    print(f"  1. Edit {script_path.name} to implement your experiment")
    print(f"  2. Run the script")
    print(f"  3. Paste the output in the comment block at the end")
    print(f"  4. Update prompts/session_log.md with this experiment")
    print(f"  5. Log your intellectual contributions in prompts/intellectual_contribution.md")
    print()

if __name__ == "__main__":
    main()
