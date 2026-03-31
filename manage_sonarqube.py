import json
import os
import re
import time

from utils import create_project, is_digit_dot_regex, run_scanner, get_all_issues

seen_set = set()
all_issues = {}


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
