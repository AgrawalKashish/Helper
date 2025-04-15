#!/usr/bin/env python3
import sys
import argparse
from git import Repo, exc

def compare_commits(repo, branch1, branch2):
    """
    Prints commits that are unique to each branch.
    """
    commits_in_branch2 = list(repo.iter_commits(f'{branch1}..{branch2}'))
    commits_in_branch1 = list(repo.iter_commits(f'{branch2}..{branch1}'))

    print(f"Commits in '{branch2}' that are not in '{branch1}':")
    if commits_in_branch2:
        for commit in commits_in_branch2:
            print(f"  - {commit.hexsha[:7]}: {commit.summary}")
    else:
        print("  None")

    print(f"\nCommits in '{branch1}' that are not in '{branch2}':")
    if commits_in_branch1:
        for commit in commits_in_branch1:
            print(f"  - {commit.hexsha[:7]}: {commit.summary}")
    else:
        print("  None")

def compare_diff(repo, branch1, branch2):
    """
    Prints the diff between two branches.
    """
    print("\nDifferences between branches (unified diff):")
    try:
        diff = repo.git.diff(f"{branch1}...{branch2}", unified=3)
        if diff:
            print(diff)
        else:
            print("No differences found.")
    except Exception as e:
        print("Error generating diff:", e)

def main():
    parser = argparse.ArgumentParser(
        description="Compare two Git branches by showing differences in commits and code."
    )
    parser.add_argument("branch1", help="First branch name")
    parser.add_argument("branch2", help="Second branch name")
    args = parser.parse_args()

    try:
        repo = Repo(".")
    except exc.InvalidGitRepositoryError:
        print("Error: Current directory is not a Git repository.")
        sys.exit(1)

    # Validate branch existence
    branches = [head.name for head in repo.heads]
    if args.branch1 not in branches:
        print(f"Error: Branch '{args.branch1}' not found in the repository.")
        sys.exit(1)
    if args.branch2 not in branches:
        print(f"Error: Branch '{args.branch2}' not found in the repository.")
        sys.exit(1)

    print(f"Comparing branches '{args.branch1}' and '{args.branch2}'...\n")
    compare_commits(repo, args.branch1, args.branch2)
    compare_diff(repo, args.branch1, args.branch2)

if __name__ == "__main__":
    main()
