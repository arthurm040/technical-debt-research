import json
from create_files import REQUESTS_PROMPT_ARRAY, PYDANTIC_PROMPT_ARRAY

TYPES = ["BUG", "CODE_SMELL", "VULNERABILITY"]
SEVERITIES = ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]
comparison = {}

with open("sonarqube_issues.json") as f:
    sonar_issues = json.load(f)

with open("responses_issues.json") as f:
    response_issues = json.load(f)


def count_issues(issues):
    counts = {"total": len(issues), **{k: 0 for k in TYPES + SEVERITIES}}
    for issue in issues:
        counts[issue["type"]] += 1
        counts[issue["severity"]] += 1
    return counts


def get_original_issues(src_path):
    parts = src_path.split("/")
    library, version = parts[1], parts[2]
    return sonar_issues.get(library, {}).get(version, {}).get(src_path, [])


def compare(prefix, prompt_array):
    results = {}
    for i, (task, src_path) in enumerate(prompt_array, start=1):
        key = f"{prefix}_{i:02d}"
        original = count_issues(get_original_issues(src_path))
        response = count_issues(response_issues.get(f"responses/{key}.py", []))
        results[key] = {
            "task": task,
            "original": original,
            "response": response,
            "diff": {k: response[k] - original[k] for k in original},
        }
    return results


comparison.update(compare("requests", REQUESTS_PROMPT_ARRAY))
comparison.update(compare("pydantic", PYDANTIC_PROMPT_ARRAY))

with open("comparison_results.json", "w") as f:
    json.dump(comparison, f, indent=2)
