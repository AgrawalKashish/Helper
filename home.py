#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
# Modified by William Thomas & You

import os
import re
import subprocess
import sys
from datetime import datetime

# Import Colorama for cross-platform ANSI color support
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    # If Colorama is not installed, define dummy color codes
    class Dummy:
        RESET_ALL = ''
    Fore = Style = Dummy()

# Global branch variables (placeholders)
BASE_BRANCH = ""
FEATURE_BRANCH = ""
REPORT_FILE = "branch_diff_report"
REPORT_FORMAT = "ansi"  # Options: "ansi" for colored text in terminal (and plain text file with ANSI codes) or "html" for an HTML report

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
    cmd = "git --no-pager diff --stat origin/{}..origin/{}".format(base, feature)
    retcode, output, err = run(cmd, cwd)
    if retcode != 0:
        return retcode, "", err
    # Split output into non-empty lines and take the last non-empty line for summary
    lines = [line for line in output.splitlines() if line.strip()]
    last_line = lines[-1] if lines else ""
    return retcode, last_line, err

def parseDiff(diff):
    # Regex to extract file count, insertions and deletions from the summary output line
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

def getChangedFileDiffs(base, feature, cwd=None):
    """
    Returns a list of dictionaries containing:
      - status: the status of the change (e.g., M, A, D)
      - filename: the file name/path
      - diff: the diff text for that file between the two branches.
    """
    cmd = "git diff --name-status origin/{}..origin/{}".format(base, feature)
    retcode, output, err = run(cmd, cwd)
    if retcode != 0:
        return []
    changes = []
    for line in output.splitlines():
        if line.strip():
            # Expecting output format to be: STATUS <TAB> filename
            parts = line.split('\t', 1)
            if len(parts) == 2:
                status, filename = parts
                diff_cmd = "git diff origin/{}..origin/{} -- {}".format(base, feature, filename)
                ret, file_diff, err_diff = run(diff_cmd, cwd)
                changes.append({
                    "status": status,
                    "filename": filename,
                    "diff": file_diff
                })
    return changes

def printComparisonReport(base, feature, repoName, files, insertions, deletions):
    # If using ANSI color codes for terminal output:
    if REPORT_FORMAT == "ansi":
        header = f"{Fore.CYAN}Comparing {base} {Fore.YELLOW}←{Fore.CYAN} {feature} ({repoName}){Style.RESET_ALL}"
        files_str = f"{Fore.MAGENTA}Files changed:{Style.RESET_ALL} {files}"
        add_str = f"{Fore.GREEN}Additions:{Style.RESET_ALL} {insertions}"
        del_str = f"{Fore.RED}Deletions:{Style.RESET_ALL} {deletions}"
        total_str = f"{Fore.BLUE}Total changes:{Style.RESET_ALL} {insertions + deletions}"
        print(header)
        print(files_str)
        print(add_str)
        print(del_str)
        print(total_str)
        print("-" * 40)
    else:
        # For HTML, we won't print to console in color
        print("Comparing {} ← {} ({}):".format(base, feature, repoName))
        print("Files changed: {}".format(files))
        print("Additions: {}".format(insertions))
        print("Deletions: {}".format(deletions))
        print("Total changes: {}".format(insertions + deletions))
        print("-" * 40)

def writeReport(results):
    if REPORT_FORMAT == "html":
        filename = REPORT_FILE + ".html"
        try:
            with open(filename, 'w', encoding='utf-8') as report:
                report.write("<html><head><meta charset='UTF-8'><title>Branch Comparison Report</title>")
                report.write("<style>")
                report.write("body { font-family: Arial, sans-serif; line-height: 1.6; }")
                report.write(".header { color: #1E90FF; }")
                report.write(".files { color: #9932CC; }")
                report.write(".add { color: green; }")
                report.write(".del { color: red; }")
                report.write(".total { color: #4169E1; }")
                report.write(".diff { background-color: #f4f4f4; padding: 5px; white-space: pre-wrap; }")
                report.write(".section { margin-bottom: 20px; border-bottom: 1px solid #ccc; padding-bottom: 10px; }")
                report.write("</style></head><body>")
                report.write("<h1 class='header'>Branch Comparison Report ({} ← {})</h1>".format(BASE_BRANCH, FEATURE_BRANCH))
                report.write("<p>Generated on: {}</p>".format(datetime.now()))
                
                for result in results:
                    report.write("<div class='section'>")
                    report.write("<h2>Repository: {}</h2>".format(result.get("repo", "Unknown")))
                    report.write("<p class='files'>Files changed: {}</p>".format(result.get("files", 0)))
                    report.write("<p class='add'>Additions: {}</p>".format(result.get("insertions", 0)))
                    report.write("<p class='del'>Deletions: {}</p>".format(result.get("deletions", 0)))
                    report.write("<h3>Changed files and differences:</h3>")
                    for change in result.get("changed_files", []):
                        report.write("<div class='diff'>")
                        report.write("<strong>Status:</strong> {} - <strong>File:</strong> {}<br/>".format(change.get("status", ""), change.get("filename", "")))
                        report.write("<pre>{}</pre>".format(change.get("diff", "")))
                        report.write("</div>")
                    report.write("</div>")
                
                if len(results) > 1:
                    total_files = sum(r.get("files", 0) for r in results)
                    total_insertions = sum(r.get("insertions", 0) for r in results)
                    total_deletions = sum(r.get("deletions", 0) for r in results)
                    report.write("<h2>CUMULATIVE SUMMARY:</h2>")
                    report.write("<p class='files'>Files changed: {}</p>".format(total_files))
                    report.write("<p class='add'>Additions: {}</p>".format(total_insertions))
                    report.write("<p class='del'>Deletions: {}</p>".format(total_deletions))
                report.write("</body></html>")
            print("Detailed report saved to {}".format(filename))
        except Exception as e:
            print("Error while writing report: {}".format(e))
    else:
        # For ANSI/plain text report (with ANSI codes)
        try:
            with open(REPORT_FILE + ".txt", 'w', encoding='utf-8') as report:
                report.write("Branch Comparison Report ({} ← {})\n".format(BASE_BRANCH, FEATURE_BRANCH))
                report.write("Generated on: {}\n\n".format(datetime.now()))
                
                for result in results:
                    report.write("Repository: {}\n".format(result.get("repo", "Unknown")))
                    report.write("Files changed: {}\n".format(result.get("files", 0)))
                    report.write("Additions: {}\n".format(result.get("insertions", 0)))
                    report.write("Deletions: {}\n".format(result.get("deletions", 0)))
                    report.write("Changed files and differences:\n")
                    for change in result.get("changed_files", []):
                        report.write("  Status: {} - File: {}\n".format(change.get("status", ""), change.get("filename", "")))
                        report.write("  Diff:\n")
                        report.write(change.get("diff", "") + "\n")
                        report.write("  " + "-"*20 + "\n")
                    report.write("-" * 40 + "\n")
                
                if len(results) > 1:
                    total_files = sum(r.get("files", 0) for r in results)
                    total_insertions = sum(r.get("insertions", 0) for r in results)
                    total_deletions = sum(r.get("deletions", 0) for r in results)
                    report.write("\nCUMULATIVE SUMMARY:\n")
                    report.write("Files changed: {}\n".format(total_files))
                    report.write("Additions: {}\n".format(total_insertions))
                    report.write("Deletions: {}\n".format(total_deletions))
    
            print("Detailed report saved to {}.txt".format(REPORT_FILE))
        except Exception as e:
            print("Error while writing report: {}".format(e))

def runComparisonForRepo(repo_path):
    repoName = getRepoName(repo_path)
    if not repoName:
        print("Not a git repository:", repo_path)
        return None

    result = compare(BASE_BRANCH, FEATURE_BRANCH, repo_path)
    if not result:
        return None

    result["repo"] = repoName
    # Get file-level diff details
    result["changed_files"] = getChangedFileDiffs(BASE_BRANCH, FEATURE_BRANCH, repo_path)
    printComparisonReport(BASE_BRANCH, FEATURE_BRANCH, repoName,
                          result.get('files', 0), result.get('insertions', 0), result.get('deletions', 0))
    return result

if __name__ == "__main__":
    # Ensure there are at least 2 arguments: BASE_BRANCH and FEATURE_BRANCH.
    # Additional arguments represent repository paths to process.
    if len(sys.argv) < 3:
        print("Usage: gitcompare BASE_BRANCH FEATURE_BRANCH [repo_directory ...]")
        sys.exit(1)

    BASE_BRANCH = sys.argv[1]
    FEATURE_BRANCH = sys.argv[2]
    repo_paths = sys.argv[3:] if len(sys.argv) > 3 else [os.getcwd()]

    results = []
    for repo in repo_paths:
        print("Processing repository at: {}".format(repo))
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
