#!/usr/local/bin/python3
# Modified by William Thomas & You
# This script generates a report comparing two branches for one or more repositories.
# It uses the branch names provided by the user (via command-line arguments) and accepts repository paths.

import os
import re
import subprocess
import sys

def run(cmd, cwd=None):
    if not cwd:
        cwd = os.getcwd()
    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True,
                            cwd=cwd)
    stdout, stderr = proc.communicate()
    return proc.returncode, stdout.decode('utf-8').strip(), stderr.decode('utf-8').strip()

def runComparison(base, feature, cwd=None):
    # This command assumes that the branch names exist as origin/branches.
    cmd = "git --no-pager diff --stat origin/%s..origin/%s | tail -n 1" % (base, feature)
    return run(cmd, cwd)

def parseDiff(diff):
    regex = r"(\d+).*file[^\d]+(\d+).*insertion[^\d]+(\d+).*deletion"
    matches = re.finditer(regex, diff, re.MULTILINE)
    for match in matches:
        if len(match.groups()) == 3:
            return {
                "files": int(match.group(1)),
                "insertions": int(match.group(2)),
                "deletions": int(match.group(3)),
            }
    return False

def compare(base, feature, cwd=None):
    code, out, err = runComparison(base, feature, cwd)
    if err:
        print(err)
        return False
    return parseDiff(out)

def getRepoName(cwd=None):
    code, out, err = run("basename `git rev-parse --show-toplevel`", cwd)
    if err:
        return False
    return out

def printComparisonReport(base, feature, repoName, files, insertions, deletions):
    print("Comparing %s ← %s (%s):" % (base, feature, repoName))
    print("Files changed: %d" % files)
    print("Additions: %d" % insertions)
    print("Deletions: %d" % deletions)
    print("Total changes: %d" % (insertions + deletions))
    print("-" * 40)

# Note: This function now takes only the repository path.
def runComparisonForRepo(repo_path):
    repoName = getRepoName(repo_path)
    if not repoName:
        print("Not a git repository:", repo_path)
        return None

    result = compare(BASE_BRANCH, FEATURE_BRANCH, repo_path)
    if not result:
        return None

    result["repo"] = repoName
    printComparisonReport(BASE_BRANCH, FEATURE_BRANCH, repoName,
                          result['files'], result['insertions'], result['deletions'])
    return result

if __name__ == "__main__":
    # Expect at least 2 arguments: BASE_BRANCH FEATURE_BRANCH
    # Optionally, additional arguments indicate directory paths (each a Git repo).
    if len(sys.argv) < 3:
        print("Usage: gitcompare BASE_BRANCH FEATURE_BRANCH [repo_directory ...]")
        sys.exit(1)

    # Set the global branch names
    BASE_BRANCH = sys.argv[1]
    FEATURE_BRANCH = sys.argv[2]

    # Use provided repository paths or default to the current directory
    repo_paths = sys.argv[3:] if len(sys.argv) > 3 else [os.getcwd()]

    results = []
    for repo in repo_paths:
        print("Processing repository at: %s" % repo)
        res = runComparisonForRepo(repo)
        if res:
            results.append(res)
        else:
            print("Failed to process repository at:", repo)
        print()

    # If more than one repository was processed, print a cumulative summary.
    if len(results) > 1:
        total_files = sum(r.get("files", 0) for r in results)
        total_insertions = sum(r.get("insertions", 0) for r in results)
        total_deletions = sum(r.get("deletions", 0) for r in results)
        print("CUMULATIVE SUMMARY:")
        printComparisonReport(BASE_BRANCH, FEATURE_BRANCH, "Total", total_files,
                              total_insertions, total_deletions)
