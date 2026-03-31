import json
import time

from utils import create_project, run_scanner, get_all_issues, analyze_files

PROJECT_KEY = "responses-verification"
RESPONSES_DIR = "responses"

create_project(PROJECT_KEY, PROJECT_KEY)
run_scanner(PROJECT_KEY, RESPONSES_DIR, "1.0")
time.sleep(20)

with open("responses_issues.json", "w") as f:
    json.dump(get_all_issues(PROJECT_KEY), f, indent=2)

with open("responses_metrics.json", "w") as f:
    json.dump(analyze_files(RESPONSES_DIR), f, indent=2)
