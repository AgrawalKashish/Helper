#!/usr/bin/env python3
import sys
import argparse
from git import Repo, exc

def box_text(text, width=80, padding=2):
    """
    Returns the text in a box with a border.
    """
    # Create the horizontal border
    border = "+" + "-" * (width - 2) + "+"
    # Prepare the text lines with padding
    lines = []
    for line in text.splitlines():
        line = line.strip()
        lines.append("|" + " " * padding + line.center(width - 2 - 2 * padding) + " " * padding + "|")
    return "\n".join([border] + lines + [border])

def format_section_header(title, width=80):
    """
    Returns a section header line for clarity.
    """
    return "\n" + "=" * width + "\n" + title.center(width) + "\n" + "=" * width + "\n"

def compare_commits(repo, branch1, branch2):
    """
    Returns a formatted string containing commits that are unique to each branch.
    """
    output = []
    output.append(format_section_header("Commit Differences"))
    
    commits_in_branch2 = list(repo.iter_commits(f'{branch1}..{branch2}'))
    commits_in_branch1 = list(repo.iter_commits(f'{branch2}..{branch1}'))
    
    output.append(f"Commits in '{branch2}' that are not in '{branch1}':\n")
    if commits_in_branch2:
        for commit in commits_in_branch2:
            output.append(f"  - {commit.hexsha[:7]}: {commit.summary}")
    else:
        output.append("  None")
    
    output.append("\n" + "-" * 80 + "\n")
    
    output.append(f"Commits in '{branch1}' that are not in '{branch2}':\n")
    if commits_in_branch1:
        for commit in commits_in_branch1:
            output.append(f"  - {commit.hexsha[:7]}: {commit.summary}")
    else:
        output.append("  None")
    
    return "\n".join(output)

def compare_diff(repo, branch1, branch2):
    """
    Returns a formatted string containing the diff between two branches.
    """
    output = []
    output.append(format_section_header("Code Differences (Unified Diff)"))
    try:
        diff = repo.git.diff(f"{branch1}...{branch2}", unified=3)
        if diff:
            output.append(diff)
        else:
            output.append("No differences found.")
    except Exception as e:
        output.append(f"Error generating diff: {e}")
    
    return "\n".join(output)

def main():
    parser = argparse.ArgumentParser(
        description="Compare two Git branches by showing differences in commits and code."
    )
    # Use options so that the branch names can contain spaces.
    parser.add_argument("--branch1", required=True, help="First branch name (can include spaces)")
    parser.add_argument("--branch2", required=True, help="Second branch name (can include spaces)")
    args = parser.parse_args()

    try:
        repo = Repo(".")
    except exc.InvalidGitRepositoryError:
        print("Error: Current directory is not a Git repository.")
        sys.exit(1)

    # Validate branch existence.
    branches = [head.name for head in repo.heads]
    if args.branch1 not in branches:
        print(f"Error: Branch '{args.branch1}' not found in the repository.")
        sys.exit(1)
    if args.branch2 not in branches:
        print(f"Error: Branch '{args.branch2}' not found in the repository.")
        sys.exit(1)

    # Overall Header for the Report
    header_text = f"Git Branch Comparison Report\n\nComparing branches:\n    Branch 1: {args.branch1}\n    Branch 2: {args.branch2}"
    overall_output = [box_text(header_text)]
    
    # Append commit differences and code diff sections.
    commit_output = compare_commits(repo, args.branch1, args.branch2)
    diff_output = compare_diff(repo, args.branch1, args.branch2)
    
    overall_output.append(commit_output)
    overall_output.append("\n" + "=" * 80 + "\n")
    overall_output.append(diff_output)
    
    full_output = "\n".join(overall_output)
    
    # Print output to the terminal.
    print(full_output)
    
    # Create a file name from the branch names.
    # Replace spaces with underscores for the file name.
    safe_branch1 = args.branch1.replace(" ", "_")
    safe_branch2 = args.branch2.replace(" ", "_")
    output_filename = f"{safe_branch1}_{safe_branch2}.txt"
    
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(full_output)
        print(f"\nResults written to file: {output_filename}")
    except Exception as e:
        print(f"Error writing output to file: {e}")

if __name__ == "__main__":
    main()
