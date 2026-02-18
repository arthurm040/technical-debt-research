import os
import json
import re
from lib2to3 import refactor
from radon.metrics import mi_visit
from radon.complexity import cc_visit
from radon.raw import analyze
from pathlib import Path

# needed for lib2 to 3 transformation
# some of the libraries are in python2
fixers = refactor.get_fixers_from_package('lib2to3.fixes')
converter = refactor.RefactoringTool(fixers)

patterns = ['TODO', 'FIXME', 'HACK', 'XXX', 'BUG']
LIBRARY_DIR = "./library-versions"
all_results = []

def convert_py2_to_py3(code):
    try:
        return str(converter.refactor_string(code + '\n', '<string>'))
    except Exception:
        return None

def find_tech_debt_markers(code):
    counts = {pattern: 0 for pattern in patterns}
    for line in code.split('\n'):
        for pattern in patterns:
            if re.search(rf'#.*\b{pattern}\b', line, re.IGNORECASE):
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
            with open(py_file, encoding='utf-8', errors='ignore') as f:
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
        'avg_maintainability': round(sum(all_mi) / len(all_mi), 2) if all_mi else 0,
        'avg_complexity': round(sum(all_complexity) / len(all_complexity), 2) if all_complexity else 0,
        'max_complexity': max(all_complexity) if all_complexity else 0,
        'total_loc': total_loc,
        'total_sloc': total_sloc,
        'total_comments': total_comments,
        'tech_debt_markers': tech_debt_markers,
        'files_analyzed': len(all_mi),
        'files_skipped': skipped
    }

for library in os.listdir(LIBRARY_DIR):
    library_dir_versions = f"{LIBRARY_DIR}/{library}"
    for version in os.listdir(library_dir_versions):
        print(f"Analyzing {library} {version}")
        metrics = analyze_library_version(f"{library_dir_versions}/{version}")

        all_results.append({
            "library": library,
            "version": version,
            **metrics
        })

with open("maintainability_results.json", "w") as f:
    json.dump(all_results, f, indent=2)

print(f"Total records: {len(all_results)}")