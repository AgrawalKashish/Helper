#!/usr/local/bin/python3
# Modified by William Thomas & You

import os
import re
import subprocess
import sys
from datetime import datetime

BASE_BRANCH = ""
FEATURE_BRANCH = ""
REPORT_FILE = "branch_diff_report.txt"

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
    cmd = f"git --no-pager diff --stat origin/{base}..origin/{feature}"
    retcode, output, err = run(cmd, cwd)
    if retcode != 0:
        return retcode, "", err
    lines = [line for line in output.splitlines() if line.strip()]
    last_line = lines[-1] if lines else ""
    return retcode, last_line, err

def getChangedFiles(base, feature, cwd=None):
    cmd = f"git diff --name-status origin/{base}..origin/{feature}"
    retcode, output, err = run(cmd, cwd)
    if retcode != 0:
        return []
    return [line.strip() for line in output.splitlines()]

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
        print("Error comparing branches:", err)
        return False
    return parseDiff(out)

def getRepoName(cwd=None):
    code, out, err = run("git rev-parse --show-toplevel", cwd)
    if code != 0 or err:
        return None
    return os.path.basename(out)

def printComparisonReport(base, feature, repoName, files, insertions, deletions):
    print("Comparing %s ← %s (%s):" % (base, feature, repoName))
    print("Files changed: %d" % files)
    print("Additions: %d" % insertions)
    print("Deletions: %d" % deletions)
    print("Total changes: %d" % (insertions + deletions))
    print("-" * 40)

def writeReport(results):
    with open(REPORT_FILE, 'w') as f:
        f.write(f"Branch Comparison Report ({BASE_BRANCH} ← {FEATURE_BRANCH})\n")
        f.write(f"Generated on: {datetime.now()}\n\n")

        for result in results:
            f.write(f"Repository: {result['repo']}\n")
            f.write(f"Files changed: {result['files']}\n")
            f.write(f"Insertions: {result['insertions']}\n")
            f.write(f"Deletions: {result['deletions']}\n")
            f.write("Changed files:\n")
            for change in result.get("changed_files", []):
                f.write(f"  {change}\n")
            f.write("-" * 40 + "\n")

        if len(results) > 1:
            total_files = sum(r.get("files", 0) for r in results)
            total_insertions = sum(r.get("insertions", 0) for r in results)
            total_deletions = sum(r.get("deletions", 0) for r in results)
            f.write("\nCUMULATIVE SUMMARY:\n")
            f.write(f"Files changed: {total_files}\n")
            f.write(f"Insertions: {total_insertions}\n")
            f.write(f"Deletions: {total_deletions}\n")

    print(f"Detailed report saved to {REPORT_FILE}")

def runComparisonForRepo(repo_path):
    repoName = getRepoName(repo_path)
    if not repoName:
        print("Not a git repository:", repo_path)
        return None

    result = compare(BASE_BRANCH, FEATURE_BRANCH, repo_path)
    if not result:
        return None

    result["repo"] = repoName
    result["changed_files"] = getChangedFiles(BASE_BRANCH, FEATURE_BRANCH, repo_path)
    printComparisonReport(BASE_BRANCH, FEATURE_BRANCH, repoName,
                          result['files'], result['insertions'], result['deletions'])
    return result

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: gitcompare BASE_BRANCH FEATURE_BRANCH [repo_directory ...]")
        sys.exit(1)

    BASE_BRANCH = sys.argv[1]
    FEATURE_BRANCH = sys.argv[2]
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

    if len(results) > 1:
        total_files = sum(r.get("files", 0) for r in results)
        total_insertions = sum(r.get("insertions", 0) for r in results)
        total_deletions = sum(r.get("deletions", 0) for r in results)
        print("CUMULATIVE SUMMARY:")
        printComparisonReport(BASE_BRANCH, FEATURE_BRANCH, "Total",
                              total_files, total_insertions, total_deletions)

    writeReport(results)
