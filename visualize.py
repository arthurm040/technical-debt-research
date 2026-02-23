import json
import pprint
import matplotlib.pyplot as plt

pp = pprint.PrettyPrinter(indent=4)

unique_libraries = {}

with open("maintainability_results.json") as file:
    data = json.load(file)
    for entry in data:
        calculate_debt_markers = sum(list(entry["tech_debt_markers"].values()))
        metrics_only = {"avg_complexity": entry["avg_complexity"],
                        "avg_maintainability": entry["avg_maintainability"],
                        "comment_ratio": entry["comment_ratio"],
                        "max_complexity": entry["max_complexity"],
                        "tech_debt_markers": calculate_debt_markers,
                        "version": entry["version"]}
        if entry["library"] not in unique_libraries:
            unique_libraries[entry["library"]] = [metrics_only]
        else:
            unique_libraries[entry["library"]].append(metrics_only)

pp.pprint(unique_libraries)

for library, metrics in unique_libraries.items():
    library_versions = [m["version"] for m in metrics]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(library)

    axes[0, 0].plot(library_versions, [m['avg_maintainability'] for m in metrics], marker='o')
    axes[0, 0].set_title("Average Maintainability")
    axes[0, 0].set_ylabel("score")
    axes[0, 0].set_xlabel("Version")

    axes[0, 1].plot(library_versions, [m['avg_complexity'] for m in metrics], marker='o')
    axes[0, 1].set_title("Average Complexity")
    axes[0, 1].set_ylabel("score")
    axes[0, 0].set_xlabel("Version")

    axes[1, 0].plot(library_versions, [m['max_complexity'] for m in metrics], marker='o')
    axes[1, 0].set_title("Maximum Complexity")
    axes[1, 0].set_ylabel("score")
    axes[1, 0].set_xlabel("Version")

    axes[1, 1].bar(library_versions, [m['tech_debt_markers'] for m in metrics])
    axes[1, 1].set_title("Tech Debt Over Time")
    axes[1, 1].set_ylabel("total")
    axes[1, 1].set_xlabel("Version")


    plt.tight_layout()
    plt.savefig(f"./metrics_images/{library}_metrics.png")
    plt.close()
    # break