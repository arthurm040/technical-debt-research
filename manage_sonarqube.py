import os
import re
import json
import time
import subprocess
import requests

BASE_URL = "http://localhost:9000"
TOKEN = "squ_fc30c47f173ad8a70cfe955bfdbe05f2c2e3e7f5"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

seen_set = set()
all_issues = {}


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


for root, dirs, files in os.walk("./library-versions", topdown=True):
    last_folder = root.rsplit("\\")[-1]
    if is_digit_dot_regex(last_folder):
        version = last_folder
        src_folder = dirs[0]
        actual_src = src_folder.rsplit("-")[0] if re.search(r"-\d", src_folder) else src_folder

        if actual_src not in seen_set:
            seen_set.add(actual_src)
            create_project(actual_src, actual_src)
            all_issues[actual_src] = {}

        run_scanner(actual_src, os.path.join(root, src_folder), version)
        time.sleep(20)

        all_issues[actual_src][version] = get_all_issues(actual_src)
        print(all_issues[actual_src][version])
        print(f"Pulled issues for {actual_src} {version}")

with open("sonarqube_issues.json", "w") as f:
    json.dump(all_issues, f, indent=2)
