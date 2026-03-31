import os
import re
import subprocess
from lib2to3 import refactor
from radon.metrics import mi_visit
from radon.complexity import cc_visit
from radon.raw import analyze
from pathlib import Path

import requests

# needed for lib2 to 3 transformation
# some of the libraries are in python2
fixers = refactor.get_fixers_from_package("lib2to3.fixes")
converter = refactor.RefactoringTool(fixers)

BASE_URL = "http://localhost:9000"
TOKEN = "squ_fc30c47f173ad8a70cfe955bfdbe05f2c2e3e7f5"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

patterns = ["TODO", "FIXME", "HACK", "XXX", "BUG"]


def project_exists(project_key):
    response = requests.get(f"{BASE_URL}/api/projects/search", params={"projects": project_key}, headers=HEADERS)
    return len(response.json()["components"]) > 0


def create_project(name, project_key):
    if not project_exists(project_key):
        requests.post(
            f"{BASE_URL}/api/projects/create",
            params={"name": name, "project": project_key, "newCodeDefinitionType": "PREVIOUS_VERSION"},
            headers=HEADERS,
        )
        print(f"Created {project_key}")


def run_scanner(project_key, src_path, version_):
    env = os.environ.copy()
    env["PIPENV_VERBOSITY"] = "-1"
    subprocess.run(
        [
            "pipenv",
            "run",
            "pysonar",
            f"--sonar-host-url={BASE_URL}",
            f"--sonar-token={TOKEN}",
            f"--sonar-project-key={project_key}",
            f"--sonar-sources={src_path}",
            f"--sonar-project-version={version_}",
            "-Dsonar.scm.disabled=true",
        ],
        env=env,
    )


def get_all_issues(project_key):
    issues_by_file = {}
    page = 1
    while True:
        response = requests.get(
            f"{BASE_URL}/api/issues/search",
            params={"componentKeys": project_key, "types": "CODE_SMELL,BUG,VULNERABILITY", "ps": 500, "p": page},
            headers=HEADERS,
        ).json()

        for issue in response["issues"]:
            file_path = issue["component"].replace(f"{project_key}:", "")
            if file_path not in issues_by_file:
                issues_by_file[file_path] = []
            issues_by_file[file_path].append(
                {
                    "rule": issue["rule"],
                    "rule_name": issue.get("ruleName"),
                    "severity": issue["severity"],
                    "type": issue["type"],
                    "line": issue.get("line"),
                    "message": issue["message"],
                    "tags": issue.get("tags", []),
                }
            )

        if page * 500 >= response["total"]:
            break
        page += 1

    return issues_by_file


def is_digit_dot_regex(s):
    return bool(re.match(r"^\d+(\.\d+)*$", s))


def convert_py2_to_py3(code):
    try:
        return str(converter.refactor_string(code + "\n", "<string>"))
    except Exception:
        return None


def find_tech_debt_markers(code):
    counts = {pattern: 0 for pattern in patterns}
    for line in code.split("\n"):
        for pattern in patterns:
            if re.search(rf"#.*\b{pattern}\b", line, re.IGNORECASE):
                counts[pattern] += 1
    return counts


def analyze_library_version(version_dir):
    all_mi = []
    all_complexity = []
    total_loc = 0
    total_sloc = 0
    total_comments = 0
    tech_debt_markers = {pattern: 0 for pattern in patterns}
    skipped = 0

    for py_file in Path(version_dir).rglob("*.py"):
        try:
            with open(py_file, encoding="utf-8", errors="ignore") as f:
                code = f.read()

            # Try to analyze as-is first
            try:
                mi_score = mi_visit(code, multi=True)
                cc_results = cc_visit(code)
                raw_metrics = analyze(code)
            except SyntaxError:
                # Convert Python 2 to Python 3 and retry
                converted = convert_py2_to_py3(code)
                if converted:
                    mi_score = mi_visit(converted, multi=True)
                    cc_results = cc_visit(converted)
                    raw_metrics = analyze(converted)
                else:
                    raise

            # Aggregate metrics
            all_mi.append(mi_score)
            all_complexity.extend([r.complexity for r in cc_results])
            total_loc += raw_metrics.loc
            total_sloc += raw_metrics.sloc
            total_comments += raw_metrics.comments

            markers = find_tech_debt_markers(code)
            for key in tech_debt_markers:
                tech_debt_markers[key] += markers[key]

        except Exception:
            skipped += 1

    return {
        "avg_maintainability": round(sum(all_mi) / len(all_mi), 2) if all_mi else 0,
        "avg_complexity": round(sum(all_complexity) / len(all_complexity), 2) if all_complexity else 0,
        "max_complexity": max(all_complexity) if all_complexity else 0,
        "total_loc": total_loc,
        "total_sloc": total_sloc,
        "total_comments": total_comments,
        "tech_debt_markers": tech_debt_markers,
        "files_analyzed": len(all_mi),
        "files_skipped": skipped,
    }


def analyze_files(directory):
    results = {}
    for py_file in Path(directory).glob("*.py"):
        try:
            with open(py_file, encoding="utf-8", errors="ignore") as f:
                code = f.read()
            try:
                mi_score = mi_visit(code, multi=True)
                cc_results = cc_visit(code)
                raw_metrics = analyze(code)
            except SyntaxError:
                converted = convert_py2_to_py3(code)
                if converted:
                    mi_score = mi_visit(converted, multi=True)
                    cc_results = cc_visit(converted)
                    raw_metrics = analyze(converted)
                else:
                    raise
            complexities = [r.complexity for r in cc_results]
            results[py_file.name] = {
                "maintainability": round(mi_score, 2),
                "avg_complexity": round(sum(complexities) / len(complexities), 2) if complexities else 0,
                "max_complexity": max(complexities) if complexities else 0,
                "loc": raw_metrics.loc,
                "sloc": raw_metrics.sloc,
                "comments": raw_metrics.comments,
                "tech_debt_markers": find_tech_debt_markers(code),
            }
        except Exception:
            results[py_file.name] = {"error": "failed to analyze"}
    return results


def analyze_single_file(file_path):
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            code = f.read()
        try:
            mi_score = mi_visit(code, multi=True)
            cc_results = cc_visit(code)
            raw_metrics = analyze(code)
        except SyntaxError:
            converted = convert_py2_to_py3(code)
            if converted:
                mi_score = mi_visit(converted, multi=True)
                cc_results = cc_visit(converted)
                raw_metrics = analyze(converted)
            else:
                raise
        complexities = [r.complexity for r in cc_results]
        return {
            "maintainability": round(mi_score, 2),
            "avg_complexity": round(sum(complexities) / len(complexities), 2) if complexities else 0,
            "max_complexity": max(complexities) if complexities else 0,
            "loc": raw_metrics.loc,
            "sloc": raw_metrics.sloc,
            "comments": raw_metrics.comments,
        }
    except Exception:
        return {"error": "failed to analyze"}
