"""Create publication figures from the saved Sprint 3 review CSV files.

Run from the repository root:
    python report/figures/generate_sprint3_figures.py

Both SVG (editable vector) and PNG (portable PDF-build input) are written.
This script does not rerun the trials or change their source files.
"""

from pathlib import Path
import argparse

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as np
import pandas as pd

TRIALS = (1, 2, 3)
BLUE = "#087DB8"
BLACK = "#292D32"
LIGHT_BLUE = "#56AEDA"
GRAY = "#969DA3"
INK = "#25292D"
MUTED = "#5B626A"
GRID = "#E7EAEE"

RI_LABELS = {
    "RI-010": "Local script execution",
    "RI-005": "External code acquisition",
    "RI-003": "Network expansion",
    "RI-006": "Destructive file operation",
    "RI-008": "System / permissions modification",
    "RI-001": "Direct download-and-execute",
    "RI-007": "Credential access",
    "RI-011": "External instruction dependency",
}


def load_trials(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    family_frames = []
    pair_frames = []
    for trial in TRIALS:
        folder = root / f"results{trial}" / "review"
        families = pd.read_csv(folder / "families.csv").assign(trial=trial)
        pairs = pd.read_csv(folder / "directed_pairs.csv").assign(trial=trial)
        family_frames.append(families)
        pair_frames.append(pairs)
    return pd.concat(family_frames, ignore_index=True), pd.concat(pair_frames, ignore_index=True)


def figure_style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "svg.fonttype": "none",  # SVG text remains selectable and editable.
        "savefig.facecolor": "white",
    })


def save_both(fig: plt.Figure, output: Path) -> None:
    fig.savefig(output.with_suffix(".svg"), format="svg", bbox_inches="tight")
    fig.savefig(output.with_suffix(".png"), format="png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def make_rate_figure(families: pd.DataFrame, output: Path) -> None:
    by_trial = families.groupby("trial")["pairs_with_indicators"].agg(
        count="size", positive=lambda counts: int(counts.gt(0).sum())
    ).reindex(TRIALS)
    values = [100 * by_trial.loc[t, "positive"] / by_trial.loc[t, "count"] for t in TRIALS]
    combined_positive = int(families["pairs_with_indicators"].gt(0).sum())
    values.append(100 * combined_positive / len(families))
    labels = ["Trial 1", "Trial 2", "Trial 3", "Combined"]
    numerators = [int(by_trial.loc[t, "positive"]) for t in TRIALS] + [combined_positive]
    denominators = [int(by_trial.loc[t, "count"]) for t in TRIALS] + [len(families)]

    fig, ax = plt.subplots(figsize=(9.3, 4.15))
    fig.subplots_adjust(left=0.09, right=0.98, top=0.72, bottom=0.20)
    x = np.arange(4)
    bars = ax.bar(x, values, width=0.48, color=[BLUE, BLUE, BLUE, BLACK])
    ax.set_ylim(0, 34)
    ax.set_xticks(x, [f"{label}\n(n={denom})" for label, denom in zip(labels, denominators)])
    ax.set_ylabel("Families with an indicator (%)", color=INK)
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#D8DEE4")
    ax.tick_params(axis="both", length=0, labelcolor=MUTED, pad=7)

    for bar, percentage, numerator in zip(bars, values, numerators):
        ax.text(bar.get_x() + bar.get_width() / 2, percentage + 1,
                f"{percentage:.1f}%\n({numerator} families)",
                ha="center", va="bottom", fontsize=10.2, fontweight="bold", color=INK)
    fig.text(0.09, 0.955, "Families with Supported Risk Indicators", fontsize=15.5,
             weight="bold", color=INK, ha="left", va="top")
    fig.text(0.09, 0.888, "Three non-overlapping stratified samples; 300 families in total",
             fontsize=10.6, color=MUTED, ha="left", va="top")
    save_both(fig, output)


def make_indicator_figure(families: pd.DataFrame, pairs: pd.DataFrame, output: Path) -> None:
    # Each indicator is counted at most once per family, even if it occurs
    # in multiple primary comparisons. The categories are not exclusive.
    detected = {}
    indicator_sets = pairs["indicator_ids"].fillna("").str.split(";")
    for indicator in RI_LABELS:
        selected = pairs.loc[indicator_sets.map(lambda ids: indicator in ids), ["trial", "family"]]
        detected[indicator] = len(selected.drop_duplicates())

    # The three family lists are intentionally non-overlapping; count the
    # union rather than adding the two leading indicator counts together.
    top_union = pairs.loc[indicator_sets.map(
        lambda ids: "RI-010" in ids or "RI-005" in ids
    ), ["trial", "family"]].drop_duplicates()
    positive_families = families.loc[families["pairs_with_indicators"].gt(0), ["trial", "family"]]
    total_families = len(families)

    ids = list(RI_LABELS)
    counts = [detected[ri] for ri in ids]
    fig, ax = plt.subplots(figsize=(10.0, 5.6))
    fig.subplots_adjust(left=0.32, right=0.92, top=0.79, bottom=0.18)
    y = np.arange(len(ids))
    colors = [BLUE, BLUE, LIGHT_BLUE, LIGHT_BLUE, GRAY, GRAY, GRAY, GRAY]
    bars = ax.barh(y, np.array(counts) / total_families * 100,
                   color=colors, height=0.57)
    ax.set_yticks(y, [f"{ri}  {RI_LABELS[ri]}" for ri in ids], fontsize=9.8)
    ax.invert_yaxis()
    ax.set_xlim(0, 16.2)
    ax.set_xlabel("Sampled families with supported indicator (%)", labelpad=9, color=INK)
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#D8DEE4")
    ax.tick_params(axis="both", length=0, labelcolor=MUTED)
    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + 0.20, bar.get_y() + bar.get_height() / 2,
                f"{100*count/total_families:.1f}%  ({count})",
                va="center", fontsize=9.8, weight="bold", color=INK)

    fig.text(0.065, 0.97, "Security-Sensitive Changes Across Sampled Families",
             fontsize=15, weight="bold", color=INK, va="top")
    fig.text(0.065, 0.909,
             "Eight indicators had detections; individual families may appear in several rows",
             fontsize=10, color=MUTED, va="top")
    fig.text(0.065, 0.079,
             f"RI-010 and/or RI-005: {len(top_union)} of {len(positive_families)} indicator-bearing families "
             f"({100 * len(top_union) / len(positive_families):.1f}%).",
             fontsize=9.3, color=MUTED, va="center")
    fig.text(0.065, 0.044,
             "No supported detections for RI-002, RI-004, or RI-009.",
             fontsize=9.3, color=MUTED, va="center")
    save_both(fig, output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path,
                        default=Path("notebooks/end_to_end_pipeline/sprint3"))
    parser.add_argument("--output", type=Path, default=Path("report/figures"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    families, pairs = load_trials(args.results_root)
    figure_style()
    make_rate_figure(families, args.output / "sprint3-family-vs-pair-rates.png")
    make_indicator_figure(families, pairs, args.output / "sprint3-indicators-by-family.png")


if __name__ == "__main__":
    main()
