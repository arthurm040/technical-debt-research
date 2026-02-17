import os
import json
import re
from lib2to3 import refactor
from radon.metrics import mi_visit
from radon.complexity import cc_visit
from radon.raw import analyze
from pathlib import Path

# Initialize lib2to3 converter
fixers = refactor.get_fixers_from_package('lib2to3.fixes')
converter = refactor.RefactoringTool(fixers)


def convert_py2_to_py3(code):
    """Convert Python 2 code to Python 3 syntax"""
    try:
        return str(converter.refactor_string(code + '\n', '<string>'))
    except:
        return None


def find_tech_debt_markers(code):
    """Count TODO, FIXME, HACK, XXX comments"""
    patterns = ['TODO', 'FIXME', 'HACK', 'XXX', 'BUG']
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
    tech_debt_markers = {pattern: 0 for pattern in ['TODO', 'FIXME', 'HACK', 'XXX', 'BUG']}
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

            # Tech debt markers
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
        'comment_ratio': round(total_comments / total_sloc * 100, 2) if total_sloc > 0 else 0,
        'tech_debt_markers': tech_debt_markers,
        'total_markers': sum(tech_debt_markers.values()),
        'files_analyzed': len(all_mi),
        'files_skipped': skipped
    }


LIBRARY_DIR = "./library-versions"
all_results = []

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

# Save to JSON
with open("maintainability_results.json", "w") as f:
    json.dump(all_results, f, indent=2)

print(f"\nResults saved to maintainability_results.json")
print(f"Total records: {len(all_results)}")
