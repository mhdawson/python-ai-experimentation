#!/usr/bin/env python3
"""
Code quality runner for the project.
Runs Ruff for linting and Black for formatting on all Python files.
"""

import subprocess
import sys
from pathlib import Path


def run_ruff_on_file(file_path):
    """Run ruff on a single file and return the results."""
    try:
        result = subprocess.run(
            ["ruff", "check", str(file_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "file": str(file_path),
            "exit_code": result.returncode,
            "output": result.stdout,
            "errors": result.stderr,
        }
    except FileNotFoundError:
        return {
            "file": str(file_path),
            "exit_code": -1,
            "output": "",
            "errors": "ruff not found. Please install it with: pip install ruff",
        }


def run_black_check_on_file(file_path):
    """Run black --check on a single file and return the results."""
    try:
        result = subprocess.run(
            ["black", "--check", "--diff", str(file_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "file": str(file_path),
            "exit_code": result.returncode,
            "output": result.stdout,
            "errors": result.stderr,
        }
    except FileNotFoundError:
        return {
            "file": str(file_path),
            "exit_code": -1,
            "output": "",
            "errors": "black not found. Please install it with: pip install black",
        }


def find_python_files():
    """Find all Python files in the current directory."""
    python_files = []
    for file in Path().glob("*.py"):
        if file.name != "lint.py":  # Skip this script itself
            python_files.append(file)
    return python_files


def count_ruff_issues(output):
    if output == "All checks passed!\n":
        return 0

    """Count the number of issues from ruff output."""
    if not output.strip():
        return 0
    lines = output.strip().split("\n")
    # Each line in ruff output represents an issue
    return len([line for line in lines if line.strip() and not line.startswith("Found")])


def run_format_check():
    """Run black --check on all Python files."""
    python_files = find_python_files()
    format_issues = []

    for file in python_files:
        result = run_black_check_on_file(file)
        if result["exit_code"] != 0:
            format_issues.append(result)

    return format_issues


def run_ruff_linting(python_files):
    """Run ruff linting on all Python files and return results."""
    print("🔍 RUFF LINTING")
    print("-" * 30)

    ruff_results = []
    total_issues = 0
    successful_runs = 0

    for file in python_files:
        print(f"🔍 Linting {file}...")
        result = run_ruff_on_file(file)
        ruff_results.append(result)

        if result["exit_code"] >= 0:  # ruff ran successfully
            issue_count = count_ruff_issues(result["output"])
            total_issues += issue_count
            successful_runs += 1

            if issue_count == 0:
                print("  ✅ No issues found")
            else:
                print(f"  ⚠️  Issues found: {issue_count}")
        else:
            print(f"  ❌ Failed to run ruff: {result['errors']}")
        print()

    return ruff_results, total_issues


def run_formatting_check():
    """Run Black formatting check and print results."""
    print("🎨 BLACK FORMATTING CHECK")
    print("-" * 30)

    format_issues = run_format_check()
    if not format_issues:
        print("✅ All files are properly formatted")
    else:
        print(f"⚠️  {len(format_issues)} file(s) need formatting:")
        for issue in format_issues:
            print(f"  - {issue['file']}")
    print()

    return format_issues


def print_summary(python_files, total_issues, format_issues):
    """Print the summary of linting and formatting results."""
    print("=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)

    print(f"📂 Files processed: {len(python_files)}")
    print(f"🔍 Ruff issues: {total_issues}")
    print(f"🎨 Formatting issues: {len(format_issues)}")

    if total_issues == 0 and len(format_issues) == 0:
        print("🎉 Excellent! No issues found.")
    elif total_issues == 0:
        print("👍 Good linting, but formatting needs attention.")
    elif len(format_issues) == 0:
        print("👍 Good formatting, but linting issues need attention.")
    else:
        print("⚠️  Both linting and formatting need improvement.")


def show_detailed_results(ruff_results, format_issues):
    """Show detailed results if requested."""
    print("\n" + "=" * 50)
    print("📋 DETAILED RUFF RESULTS")
    print("=" * 50)

    for result in ruff_results:
        print(f"\n📄 {result['file']}")
        print("-" * 30)
        if result["exit_code"] >= 0:
            if result["output"].strip():
                print(result["output"])
            else:
                print("No issues found")
        else:
            print(f"Error: {result['errors']}")

    if format_issues:
        print("\n" + "=" * 50)
        print("📋 DETAILED FORMATTING RESULTS")
        print("=" * 50)

        for issue in format_issues:
            print(f"\n📄 {issue['file']}")
            print("-" * 30)
            if issue["output"].strip():
                print(issue["output"])
            else:
                print("Formatting needed (no diff shown)")


def show_fix_commands(total_issues, format_issues):
    """Show commands to fix issues."""
    print("\n" + "=" * 50)
    print("🛠️  HOW TO FIX")
    print("=" * 50)

    if len(format_issues) > 0:
        print("🎨 Format all files with Black:")
        print("   black .")
        print()

    if total_issues > 0:
        print("🔧 Auto-fix some Ruff issues:")
        print("   ruff check --fix .")
        print()
        print("🔍 Show all Ruff issues:")
        print("   ruff check .")


def main():
    """Main function to run ruff and black on all Python files."""
    print("🔍 Python Code Quality Report")
    print("=" * 50)

    python_files = find_python_files()

    if not python_files:
        print("❌ No Python files found to check.")
        return

    print(f"📄 Found {len(python_files)} Python file(s) to check:")
    for file in python_files:
        print(f"  - {file}")
    print()

    # Run Ruff linting
    ruff_results, total_issues = run_ruff_linting(python_files)

    # Run Black formatting check
    format_issues = run_formatting_check()

    # Print summary
    print_summary(python_files, total_issues, format_issues)

    # Show detailed results if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--detailed":
        show_detailed_results(ruff_results, format_issues)

    # Show commands to fix issues
    if total_issues > 0 or len(format_issues) > 0:
        show_fix_commands(total_issues, format_issues)


if __name__ == "__main__":
    main()
