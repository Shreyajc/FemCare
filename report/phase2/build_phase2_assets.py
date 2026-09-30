from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

BLUE = "#2E74B5"
DARK_BLUE = "#1F4D78"
PINK = "#D53F8C"
PLUM = "#7A2E67"
LIGHT_BLUE = "#E8EEF5"
LIGHT_PINK = "#FCE4EC"
GRAY = "#666666"
GRID = "#D7DCE2"


def save(fig, name: str) -> None:
    fig.savefig(ASSETS / name, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def architecture() -> None:
    labels = [
        ("Fused CSV", "17,976 rows\n56 columns"),
        ("Preparation", "select safe fields\nformat documents"),
        ("Documents", "cycle + state +\nsummary records"),
        ("TF-IDF", "numeric text\nvectors"),
        ("Vector index", "18,061 searchable\ndocuments"),
        ("Retriever", "top relevant\ncontext"),
        ("Llama 3.2", "grounded answer\nwith source"),
    ]
    fig, ax = plt.subplots(figsize=(12, 3.4))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 4)
    ax.axis("off")
    for i, (title, subtitle) in enumerate(labels):
        x = 0.25 + i * 1.95
        fill = LIGHT_PINK if i in (0, 6) else LIGHT_BLUE
        edge = PLUM if i in (0, 6) else BLUE
        box = FancyBboxPatch(
            (x, 1.05), 1.55, 1.65,
            boxstyle="round,pad=0.05,rounding_size=0.08",
            facecolor=fill, edgecolor=edge, linewidth=1.7,
        )
        ax.add_patch(box)
        ax.text(x + 0.775, 2.22, title, ha="center", va="center", fontsize=10.5,
                color=DARK_BLUE, fontweight="bold")
        ax.text(x + 0.775, 1.55, subtitle, ha="center", va="center", fontsize=8.7,
                color="#30343B", linespacing=1.25)
        if i < len(labels) - 1:
            ax.annotate("", xy=(x + 1.89, 1.88), xytext=(x + 1.58, 1.88),
                        arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.6))
    ax.text(7, 3.42, "Phase 2 retrieval-augmented generation workflow",
            ha="center", va="center", fontsize=15, color=DARK_BLUE, fontweight="bold")
    ax.text(7, 0.42,
            "The API-enriched fields become searchable evidence; the language model answers only from retrieved context.",
            ha="center", va="center", fontsize=9.5, color=GRAY)
    save(fig, "fig07_phase2_rag_pipeline.png")


def evaluation_charts() -> None:
    summary = pd.read_csv(ASSETS / "phase2_rag_summary.csv")
    ordered = summary.set_index("system").loc[["Before fusion", "After fusion"]]

    fig, ax = plt.subplots(figsize=(8, 4.8))
    colors = [GRID, PINK]
    bars = ax.bar(ordered.index, ordered["accuracy_percent"], color=colors, width=0.55)
    ax.set_ylim(0, 110)
    ax.set_ylabel("Correct answers (%)")
    ax.set_title("LLM evaluation accuracy before and after data enrichment",
                 color=DARK_BLUE, fontweight="bold", pad=12)
    ax.grid(axis="y", color="#EBEEF2", linewidth=0.9)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, ordered["accuracy_percent"]):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 3, f"{value:.0f}%",
                ha="center", color=DARK_BLUE, fontweight="bold", fontsize=12)
    ax.text(0.5, -0.18, "Ten fixed questions: five original-domain and five API/fusion questions",
            ha="center", transform=ax.transAxes, fontsize=9, color=GRAY)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    save(fig, "fig08_before_after_accuracy.png")

    fig, ax = plt.subplots(figsize=(8, 4.8))
    times = ordered["average_response_time_seconds"]
    bars = ax.bar(ordered.index, times, color=[LIGHT_BLUE, BLUE], width=0.55)
    ax.set_ylim(0, max(times) * 1.25)
    ax.set_ylabel("Average response time (seconds)")
    ax.set_title("Measured response time trade-off",
                 color=DARK_BLUE, fontweight="bold", pad=12)
    ax.grid(axis="y", color="#EBEEF2", linewidth=0.9)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, times):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.8, f"{value:.1f} s",
                ha="center", color=DARK_BLUE, fontweight="bold", fontsize=11)
    ax.text(0.5, -0.18, "Local Ollama execution; timings are machine-specific and not a production benchmark",
            ha="center", transform=ax.transAxes, fontsize=9, color=GRAY)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    save(fig, "fig09_response_time.png")


def state_comparison() -> None:
    df = pd.read_csv(ROOT / "data" / "api_fusion" / "final" / "femcare_final_cleaned.csv")
    state = (
        df.groupby("state", as_index=False)
        .agg(avg_pain=("pain_level", "mean"), avg_stress=("stress_score_cycle", "mean"))
    )
    subset = state[state["state"].isin(["California", "Texas", "Massachusetts"])].copy()
    subset = subset.set_index("state").loc[["California", "Texas", "Massachusetts"]]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    x = range(len(subset))
    ax.bar([i - 0.19 for i in x], subset["avg_pain"], width=0.38, label="Average pain", color=PINK)
    ax.bar([i + 0.19 for i in x], subset["avg_stress"], width=0.38, label="Average stress", color=BLUE)
    ax.set_xticks(list(x), subset.index)
    ax.set_ylim(0, 7)
    ax.set_ylabel("Mean score (0-10)")
    ax.set_title("State-level comparison enabled by fusion",
                 color=DARK_BLUE, fontweight="bold", pad=12)
    ax.legend(frameon=False, ncol=2, loc="upper right")
    ax.grid(axis="y", color="#EBEEF2", linewidth=0.9)
    ax.set_axisbelow(True)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f", padding=3, fontsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    save(fig, "fig10_state_comparison.png")


def capability_matrix() -> None:
    labels = ["General menstrual\nhealth", "Census\ncontext", "CDC risk\ncontext", "Weather-pain\nrelationships", "Cross-state\ncomparison"]
    matrix = [[1, 0, 0, 0, 0], [1, 1, 1, 1, 1]]
    fig, ax = plt.subplots(figsize=(9, 3.6))
    cmap = plt.matplotlib.colors.ListedColormap(["#F3F4F6", "#D53F8C"])
    ax.imshow(matrix, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_yticks([0, 1], ["Before fusion", "After fusion"])
    ax.set_xticks(range(len(labels)), labels)
    ax.tick_params(axis="x", labelsize=9)
    ax.set_title("Knowledge coverage gained from API fusion",
                 color=DARK_BLUE, fontweight="bold", pad=12)
    for i in range(2):
        for j in range(5):
            ax.text(j, i, "Available" if matrix[i][j] else "Unavailable",
                    ha="center", va="center", fontsize=9,
                    color="white" if matrix[i][j] else GRAY,
                    fontweight="bold")
    ax.set_xticks([i - 0.5 for i in range(1, 5)], minor=True)
    ax.set_yticks([0.5], minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", bottom=False, left=False)
    save(fig, "fig11_capability_matrix.png")


def response_excerpt() -> None:
    evaluation = pd.read_csv(ASSETS / "phase2_rag_evaluation.csv")
    row = evaluation[(evaluation["system"] == "After fusion") & (evaluation["id"] == "F1")].iloc[0]
    payload = {
        "question": row["question"],
        "retrieved_source": row["source"],
        "answer": row["response"],
        "correct": bool(row["correct"]),
    }
    (ASSETS / "evaluation_excerpt.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    architecture()
    evaluation_charts()
    state_comparison()
    capability_matrix()
    response_excerpt()
    print(f"Phase 2 assets written to {ASSETS}")
