import json
import os
import time

from utils import create_project, run_scanner, get_all_issues, analyze_files

PROJECT_KEY = "responses-verification"
RESPONSES_DIR = "responses"

existing_issues = json.load(open("responses_issues.json")) if os.path.exists("responses_issues.json") else {}
existing_metrics = json.load(open("responses_metrics.json")) if os.path.exists("responses_metrics.json") else {}

# create_project(PROJECT_KEY, PROJECT_KEY)
# run_scanner(PROJECT_KEY, RESPONSES_DIR, "1.0")
# time.sleep(20)

# existing_issues.update(get_all_issues(PROJECT_KEY))
# with open("responses_issues.json", "w") as f:
#     json.dump(existing_issues, f, indent=2)

# existing_metrics.update(analyze_files(RESPONSES_DIR))
with open("responses_metrics.json", "w") as f:
    json.dump(analyze_files(RESPONSES_DIR), f, indent=2)
