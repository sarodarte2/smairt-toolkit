#!/usr/bin/env python
"""
compile_for_ai.py

Compiles the current project state into a single document that can be
pasted into a new AI session.

This is an essential part of the SMAIRT workflow - leaving a 'breadcrumb' trail
that allows you to A) track what you have done and keep a record of those
steps, results, and interpretation as you go along, B) provide a record that
can be used to feed back in to an AI to bring it up to speed on what was done,
for what reason, and what the results were.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# === CONFIGURATION ===
# Maximum characters to include from each file (to avoid context limits)
MAX_FILE_CHARS = 10000
# Maximum total output characters
MAX_TOTAL_CHARS = 100000

def get_project_root():
    """Get the project root directory (parent of scripts folder)."""
    return Path(__file__).parent.parent

def read_file_safely(filepath, max_chars=MAX_FILE_CHARS):
    """Read a file, truncating if necessary."""
    try:
        content = filepath.read_text()
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n[... TRUNCATED - {len(content)} total chars ...]"
        return content
    except Exception as e:
        return f"[Error reading file: {e}]"

def find_scripts_with_output(experiments_dir):
    """Find all Python scripts and extract their pasted output blocks."""
    scripts_info = []

    for phase_dir in sorted(experiments_dir.iterdir()):
        if phase_dir.is_dir() and not phase_dir.name.startswith('.'):
            scripts = sorted(phase_dir.glob("script_*.py"))
            for script in scripts:
                content = read_file_safely(script)
                scripts_info.append({
                    'path': script.relative_to(get_project_root()),
                    'phase': phase_dir.name,
                    'content': content
                })

    return scripts_info

def compile_project():
    """Compile the entire project state into a single document."""
    root = get_project_root()
    output = []
    total_chars = 0

    # Header
    output.append("=" * 70)
    output.append("SMAIRT PROJECT STATE COMPILATION")
    output.append(f"Generated: {datetime.now().isoformat()}")
    output.append(f"Project: {root.name}")
    output.append("=" * 70)
    output.append("")

    # === KEY CONTEXT FILES ===
    key_files = [
        ("prompts/AI_CONTEXT.md", "AI Context (Your Role)"),
        ("prompts/CODE_CONVENTIONS.md", "Code Conventions"),
        ("prompts/KNOWN_PATTERNS.md", "Known Patterns & Common Errors"),
        ("background/01_initial_question.md", "Initial Research Question"),
        ("hypotheses/hypothesis_log.md", "Hypothesis Log"),
        ("prompts/session_log.md", "Session Log"),
        ("prompts/intellectual_contribution.md", "Intellectual Contributions"),
        ("analysis/iteration_log.md", "Iteration Log"),
        ("analysis/future_directions.md", "Future Directions"),
    ]

    output.append("")
    output.append("#" * 70)
    output.append("# KEY CONTEXT FILES")
    output.append("#" * 70)

    for filepath, description in key_files:
        full_path = root / filepath
        if full_path.exists():
            content = read_file_safely(full_path)
            output.append("")
            output.append(f"## {description}")
            output.append(f"## File: {filepath}")
            output.append("-" * 50)
            output.append(content)
            output.append("")

            total_chars += len(content)
            if total_chars > MAX_TOTAL_CHARS:
                output.append(f"\n[TRUNCATED - Reached {MAX_TOTAL_CHARS} character limit]")
                break

    # === EXPERIMENT SCRIPTS ===
    if total_chars < MAX_TOTAL_CHARS:
        experiments_dir = root / "experiments"
        if experiments_dir.exists():
            output.append("")
            output.append("#" * 70)
            output.append("# EXPERIMENT SCRIPTS (with pasted output)")
            output.append("#" * 70)

            scripts_info = find_scripts_with_output(experiments_dir)

            for script in scripts_info:
                output.append("")
                output.append(f"## {script['path']}")
                output.append(f"## Phase: {script['phase']}")
                output.append("-" * 50)
                output.append("```python")
                output.append(script['content'])
                output.append("```")
                output.append("")

                total_chars += len(script['content'])
                if total_chars > MAX_TOTAL_CHARS:
                    output.append(f"\n[TRUNCATED - Reached {MAX_TOTAL_CHARS} character limit]")
                    break

    # === RESULTS LOGS ===
    if total_chars < MAX_TOTAL_CHARS:
        logs_dir = root / "results" / "logs"
        if logs_dir.exists():
            logs = sorted(logs_dir.glob("*.log"))[-5:]  # Last 5 logs

            if logs:
                output.append("")
                output.append("#" * 70)
                output.append("# RECENT OUTPUT LOGS (last 5)")
                output.append("#" * 70)

                for log in logs:
                    content = read_file_safely(log, max_chars=5000)
                    output.append("")
                    output.append(f"## {log.name}")
                    output.append("-" * 50)
                    output.append(content)
                    output.append("")

                    total_chars += len(content)
                    if total_chars > MAX_TOTAL_CHARS:
                        output.append(f"\n[TRUNCATED - Reached {MAX_TOTAL_CHARS} character limit]")
                        break

    # Footer
    output.append("")
    output.append("=" * 70)
    output.append("END OF COMPILATION")
    output.append(f"Total characters: {total_chars}")
    output.append("=" * 70)

    return "\n".join(output)

def main():
    """Main entry point."""
    # Compile the project
    compiled = compile_project()

    # Determine output destination
    root = get_project_root()
    output_path = root / "prompts" / "compiled_for_ai.md"

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    output_path.write_text(compiled)

    # Print summary
    print(f"Project state compiled successfully!")
    print(f"Output: {output_path}")
    print(f"Total characters: {len(compiled)}")
    print()
    print("You can now paste the contents of this file into a new AI session")
    print("to recreate the context and continue where you left off.")
    print()
    print("To copy to clipboard (Linux): ")
    print(f"  cat {output_path} | xclip -selection clipboard")
    print()
    print("To copy to clipboard (Mac): ")
    print(f"  cat {output_path} | pbcopy")

if __name__ == "__main__":
    main()
