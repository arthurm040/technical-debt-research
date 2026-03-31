import json
from create_files import REQUESTS_PROMPT_ARRAY, PYDANTIC_PROMPT_ARRAY
from utils import analyze_single_file

RESPONSES_DIR = "responses"


def compare_metrics(prefix, prompt_array):
    results = {}
    for i, (_, src_path) in enumerate(prompt_array, start=1):
        key = f"{prefix}_{i:02d}"
        original = analyze_single_file(src_path)
        response = analyze_single_file(f"{RESPONSES_DIR}/{key}.py")
        if "error" in original or "error" in response:
            results[key] = {"error": "failed to analyze one or both files"}
            continue
        results[key] = {
            "original": original,
            "response": response,
            "diff": {k: round(response[k] - original[k], 2) for k in original},
        }
    return results


metrics = {}
metrics.update(compare_metrics("requests", REQUESTS_PROMPT_ARRAY))
metrics.update(compare_metrics("pydantic", PYDANTIC_PROMPT_ARRAY))

with open("responses_metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)
