"""Create publication figures from the saved Sprint 3 review CSV files.

Run from the repository root:
    python report/figures/generate_sprint3_figures.py

SVG files are written for direct use in the report.
This script does not rerun the trials or change their source files.
"""

from pathlib import Path
import argparse

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as np
import pandas as pd

TRIALS = (1, 2, 3)
# Desaturated blue-gray accents complement the LaTeX table palette:
# reportTableHead #E8EEF3 and reportTableStripe #F6F8FA.
BLUE = "#607E96"
BLACK = "#384750"
LIGHT_BLUE = "#A1B5C5"
GRAY = "#B5BEC6"
INK = "#29343D"
MUTED = "#56636D"
GRID = "#E8EEF3"

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
        "font.size": 8.4,
        "svg.fonttype": "none",  # SVG text remains selectable and editable.
        "savefig.facecolor": "white",
    })


def save_svg(fig: plt.Figure, output: Path) -> None:
    fig.savefig(output.with_suffix(".svg"), format="svg", bbox_inches="tight")
    plt.close(fig)


def make_rate_figure(families: pd.DataFrame, output: Path) -> None:
    """Compact, single-column dot plot at approximately the report's 9 pt scale.

    The existing output basename is retained for report compatibility.
    """
    by_trial = families.groupby("trial")["pairs_with_indicators"].agg(
        count="size", positive=lambda counts: int(counts.gt(0).sum())
    ).reindex(TRIALS)
    positives = [int(by_trial.loc[t, "positive"]) for t in TRIALS]
    denominators = [int(by_trial.loc[t, "count"]) for t in TRIALS]
    positives.append(int(families["pairs_with_indicators"].gt(0).sum()))
    denominators.append(len(families))
    rates = [100 * yes / total for yes, total in zip(positives, denominators)]
    labels = ["Trial 1", "Trial 2", "Trial 3", "Combined"]
    y_positions = [3.15, 2.15, 1.15, 0.05]

    # Build the chart at final print size instead of shrinking a page-width
    # presentation graphic into the report's two-column layout.
    fig, ax = plt.subplots(figsize=(3.32, 1.93))
    fig.subplots_adjust(left=0.23, right=0.995, top=0.96, bottom=0.22)
    ax.set_xlim(0, 39)
    ax.set_ylim(-0.45, 3.62)
    ax.set_yticks(y_positions, labels, fontsize=7.7)
    ax.set_xticks([0, 10, 20, 30])
    ax.set_xticklabels(["0", "10", "20", "30"], fontsize=7.1)
    ax.set_xlabel("Families with a supported indicator (%)", color=INK,
                  fontsize=7.1, labelpad=4)
    ax.xaxis.grid(True, color=GRID, linewidth=0.65)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", length=0, colors=MUTED, pad=4)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#CFD8E1")
    # Horizontal marker stems and dots take less space than large filled bars.
    for label, y, rate, count, total in zip(labels, y_positions, rates, positives, denominators):
        is_total = label == "Combined"
        color = BLACK if is_total else BLUE
        ax.plot([0, rate], [y, y], color=color, alpha=0.34,
                linewidth=1.2, solid_capstyle="round", zorder=2)
        ax.scatter(rate, y, color=color, s=30 if is_total else 24,
                   zorder=3)
        ax.text(rate + 1.15, y, f"{rate:.0f}%  ({count}/{total})",
                fontsize=7.4, fontweight="semibold" if is_total else "normal",
                color=INK, va="center", ha="left")
    save_svg(fig, output)


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
    fig, ax = plt.subplots(figsize=(7.65, 4.55))
    fig.subplots_adjust(left=0.365, right=0.92, top=0.78, bottom=0.19)
    y = np.arange(len(ids))
    colors = [BLUE, BLUE, LIGHT_BLUE, LIGHT_BLUE, GRAY, GRAY, GRAY, GRAY]
    bars = ax.barh(y, np.array(counts) / total_families * 100,
                   color=colors, height=0.57)
    ax.set_yticks(y, [f"{ri}  {RI_LABELS[ri]}" for ri in ids], fontsize=7.9)
    ax.invert_yaxis()
    ax.set_xlim(0, 16.2)
    ax.set_xlabel("Sampled families with supported indicator (%)", labelpad=7, color=INK, fontsize=8.1)
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#D8DEE4")
    ax.tick_params(axis="both", length=0, labelcolor=MUTED)
    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + 0.20, bar.get_y() + bar.get_height() / 2,
                f"{100*count/total_families:.1f}%  ({count})",
                va="center", fontsize=8.1, weight="semibold", color=INK)

    fig.text(0.065, 0.97, "Security-Sensitive Changes Across Sampled Families",
             fontsize=10.4, weight="bold", color=INK, va="top")
    fig.text(0.065, 0.918,
             "Eight indicators had detections; categories overlap",
             fontsize=8.2, color=MUTED, va="top")
    fig.text(0.065, 0.083,
             f"RI-010 and/or RI-005: {len(top_union)} of {len(positive_families)} indicator-bearing families "
             f"({100 * len(top_union) / len(positive_families):.1f}%).",
             fontsize=7.6, color=MUTED, va="center")
    fig.text(0.065, 0.047,
             "No supported detections for RI-002, RI-004, or RI-009.",
             fontsize=7.6, color=MUTED, va="center")
    save_svg(fig, output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path,
                        default=Path("notebooks/end_to_end_pipeline/sprint3"))
    parser.add_argument("--output", type=Path, default=Path("report/figures"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    families, pairs = load_trials(args.results_root)
    figure_style()
    make_rate_figure(families, args.output / "sprint3-family-vs-pair-rates.svg")
    make_indicator_figure(families, pairs, args.output / "sprint3-indicators-by-family.svg")


if __name__ == "__main__":
    main()
