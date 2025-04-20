#!/usr/local/bin/python3
# Written by William Thomas (Modified by You)

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
    # Note: This command assumes that the desired branches exist as origin/branches.
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

def runComparisonForRepo(cwd, base, feature):
    repoName = getRepoName(cwd)
    if not repoName:
        print("Not a git repository:", cwd)
        return None

    result = compare(base, feature, cwd)
    if not result:
        return None

    result["repo"] = repoName
    printComparisonReport(base, feature, repoName, result['files'], result['insertions'], result['deletions'])
    return result

if __name__ == "__main__":
    # Expect at least 2 arguments: BASE_BRANCH FEATURE_BRANCH
    # Optionally, additional arguments indicate directories of repos to compare.
    if len(sys.argv) < 3:
        print("Usage: gitcompare BASE_BRANCH FEATURE_BRANCH [repo_directory ...]")
        sys.exit(1)

    base = sys.argv[1]
    feature = sys.argv[2]

    # If no additional directory arguments provided, default to the current directory.
    repo_dirs = sys.argv[3:] if len(sys.argv) > 3 else [os.getcwd()]

    results = []
    for repo_dir in repo_dirs:
        print("Processing repository at: %s" % repo_dir)
        result = runComparisonForRepo(repo_dir, base, feature)
        if result:
            results.append(result)
        else:
            print("Failed to process repository at:", repo_dir)
        print()

    # If more than one repository was processed, print a cumulative summary.
    if len(results) > 1:
        total_files = sum(r.get("files", 0) for r in results)
        total_insertions = sum(r.get("insertions", 0) for r in results)
        total_deletions = sum(r.get("deletions", 0) for r in results)
        print("CUMULATIVE SUMMARY:")
        printComparisonReport(base, feature, "Total", total_files, total_insertions, total_deletions)
