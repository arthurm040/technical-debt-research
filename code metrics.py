import json
import os

from utils import analyze_library_version

LIBRARY_DIR = "./library-versions"
all_results = []


for library in os.listdir(LIBRARY_DIR):
    library_dir_versions = f"{LIBRARY_DIR}/{library}"
    for version in os.listdir(library_dir_versions):
        print(f"Analyzing {library} {version}")
        metrics = analyze_library_version(f"{library_dir_versions}/{version}")

        all_results.append({"library": library, "version": version, **metrics})

with open("maintainability_results.json", "w") as f:
    json.dump(all_results, f, indent=2)

print(f"Total records: {len(all_results)}")
