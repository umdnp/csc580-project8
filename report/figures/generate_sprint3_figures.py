"""Build the two report figures from the three saved Sprint 3 trial CSVs."""

from pathlib import Path
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

RI_LABELS = {
    "RI-001": "Direct download/execute",
    "RI-002": "Executed source change",
    "RI-003": "Network expansion",
    "RI-004": "Weakened network security",
    "RI-005": "External code acquisition",
    "RI-006": "Destructive file operation",
    "RI-007": "Credential access",
    "RI-008": "System or permissions",
    "RI-009": "Sensitive file access",
    "RI-010": "Local script execution",
    "RI-011": "External instructions",
}


def load_trials(results_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    family_tables = []
    pair_tables = []
    for trial in (1, 2, 3):
        review_dir = results_root / f"results{trial}" / "review"
        families = pd.read_csv(review_dir / "families.csv")
        pairs = pd.read_csv(review_dir / "directed_pairs.csv")
        families["trial"] = trial
        pairs["trial"] = trial
        family_tables.append(families)
        pair_tables.append(pairs)
    return pd.concat(family_tables, ignore_index=True), pd.concat(pair_tables, ignore_index=True)


def make_rate_figure(families: pd.DataFrame, pairs: pd.DataFrame, output: Path) -> None:
    family_rates = families.groupby("trial")["pairs_with_indicators"].apply(lambda values: 100 * values.gt(0).mean())
    pair_rates = pairs.groupby("trial")["indicator_ids"].apply(lambda values: 100 * values.notna().mean())
    x = np.arange(3)
    fig, ax = plt.subplots(figsize=(8.0, 3.9))
    a = ax.bar(x - 0.2, family_rates.reindex([1, 2, 3]), width=0.36, label="Families with indicator")
    b = ax.bar(x + 0.2, pair_rates.reindex([1, 2, 3]), width=0.36, label="Comparisons with indicator")
    for bars in (a, b):
        ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=9)
    ax.set_xticks(x, ["Trial 1", "Trial 2", "Trial 3"])
    ax.set_ylim(0, 31)
    ax.set_ylabel("Percent within each trial")
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.14), ncol=2, frameon=False)
    fig.tight_layout()
    fig.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(fig)


def make_indicator_figure(pairs: pd.DataFrame, output: Path) -> None:
    counts = {}
    for ri in RI_LABELS:
        selected = pairs[pairs["indicator_ids"].fillna("").str.split(";").apply(lambda ids: ri in ids)]
        counts[ri] = len(selected[["trial", "family"]].drop_duplicates())
    order = sorted(RI_LABELS, key=lambda ri: (counts[ri], ri))
    fig, ax = plt.subplots(figsize=(7.6, 5.2))
    y = np.arange(len(order))
    bars = ax.barh(y, [counts[ri] for ri in order], height=0.7)
    ax.set_yticks(y, [f"{ri}  {RI_LABELS[ri]}" for ri in order], fontsize=10)
    ax.set_xlim(0, 45)
    ax.set_xlabel("Distinct sampled families with a supported indicator")
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    for bar, ri in zip(bars, order):
        ax.text(bar.get_width() + 0.4, bar.get_y() + bar.get_height() / 2, str(counts[ri]), va="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path,
                        default=Path("notebooks/end_to_end_pipeline/sprint3"))
    parser.add_argument("--output", type=Path, default=Path("report/figures"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    families, pairs = load_trials(args.results_root)
    make_rate_figure(families, pairs, args.output / "sprint3-family-vs-pair-rates.png")
    make_indicator_figure(pairs, args.output / "sprint3-indicators-by-family.png")


if __name__ == "__main__":
    main()
