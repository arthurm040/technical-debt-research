import json
import os
import numpy as np
import matplotlib.pyplot as plt

with open("comparison_results.json") as f:
    issues_data = json.load(f)

with open("comparison_metrics.json") as f:
    metrics_data = json.load(f)

os.makedirs("metrics_images/comparison_overview", exist_ok=True)
os.makedirs("metrics_images/comparison_library", exist_ok=True)
os.makedirs("metrics_images/comparison_summary", exist_ok=True)

LIBRARIES = ["requests", "pydantic", "click", "marshmallow"]
COLORS = {"original": "steelblue", "response": "darkorange"}


def get_library(key):
    return key.rsplit("_", 1)[0]


def plot_overview():
    tasks = list(issues_data.keys())
    original = [issues_data[k]["original"]["total"] for k in tasks]
    response = [issues_data[k]["response"]["total"] for k in tasks]

    y = np.arange(len(tasks))
    height = 0.35

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.barh(y - height / 2, original, height, label="Human", color=COLORS["original"])
    ax.barh(y + height / 2, response, height, label="AI", color=COLORS["response"])
    ax.set_yticks(y)
    ax.set_yticklabels(tasks)
    ax.set_title("Total Issues: Human vs AI per Task")
    ax.set_xlabel("Issue count")
    ax.legend()
    plt.tight_layout()
    plt.savefig("metrics_images/comparison_overview/issue_overview.png")
    plt.close()


def plot_library_dashboard():
    for library in LIBRARIES:
        lib_keys = [k for k in issues_data if get_library(k) == library]
        if not lib_keys:
            continue

        x = np.arange(len(lib_keys))
        width = 0.35
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle(library)

        for ax, metric in zip(axes.flat, ["total", "BUG", "CRITICAL", "MAJOR"]):
            original = [issues_data[k]["original"][metric] for k in lib_keys]
            response = [issues_data[k]["response"][metric] for k in lib_keys]
            ax.bar(x - width / 2, original, width, label="Human", color=COLORS["original"])
            ax.bar(x + width / 2, response, width, label="AI", color=COLORS["response"])
            ax.set_xticks(x)
            ax.set_xticklabels(lib_keys, rotation=15)
            ax.set_title(f"{metric} Issues")
            ax.set_ylabel("count")
            ax.legend()

        plt.tight_layout()
        plt.savefig(f"metrics_images/comparison_library/{library}_issues.png")
        plt.close()


def plot_summary():
    avg_original_issues = [
        sum(issues_data[k]["original"]["total"] for k in issues_data if get_library(k) == lib) /
        max(sum(1 for k in issues_data if get_library(k) == lib), 1)
        for lib in LIBRARIES
    ]
    avg_response_issues = [
        sum(issues_data[k]["response"]["total"] for k in issues_data if get_library(k) == lib) /
        max(sum(1 for k in issues_data if get_library(k) == lib), 1)
        for lib in LIBRARIES
    ]
    avg_original_maintainability = [
        sum(metrics_data[k]["original"]["maintainability"] for k in metrics_data if get_library(k) == lib) /
        max(sum(1 for k in metrics_data if get_library(k) == lib), 1)
        for lib in LIBRARIES
    ]
    avg_response_maintainability = [
        sum(metrics_data[k]["response"]["maintainability"] for k in metrics_data if get_library(k) == lib) /
        max(sum(1 for k in metrics_data if get_library(k) == lib), 1)
        for lib in LIBRARIES
    ]

    x = np.arange(len(LIBRARIES))
    width = 0.35
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Per Library Summary: Human vs AI")

    axes[0].bar(x - width / 2, avg_original_issues, width, label="Human", color=COLORS["original"])
    axes[0].bar(x + width / 2, avg_response_issues, width, label="AI", color=COLORS["response"])
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(LIBRARIES)
    axes[0].set_title("Avg Issue Count")
    axes[0].set_ylabel("avg count")
    axes[0].legend()

    axes[1].bar(x - width / 2, avg_original_maintainability, width, label="Human", color=COLORS["original"])
    axes[1].bar(x + width / 2, avg_response_maintainability, width, label="AI", color=COLORS["response"])
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(LIBRARIES)
    axes[1].set_title("Avg Maintainability")
    axes[1].set_ylabel("score")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig("metrics_images/comparison_summary/library_summary.png")
    plt.close()


plot_overview()
plot_library_dashboard()
plot_summary()
