"""Step 4 (part 2): tradeoff plots of relative overhead (over the
analytical entropy) vs. construction/query time.

One PDF per (dataset instance, {construction, query}) pair, where a
"dataset instance" is one exact distribution + swept-parameter-value
combination (e.g. "bernoulli, p=0.1") - see naming.dataset_instances, the
same enumeration tables.py uses for its columns. Within a plot, X is
relative space overhead and Y is time/key (log scale); each *algorithm*
(not each config) gets one fixed color+marker, and sibling configs of the
same algorithm - e.g. differently-tuned Consensus runs - are drawn as
separate points connected by a line (sorted by X) so the line traces out
that algorithm's own tradeoff curve on this one dataset. Each point is
annotated with its config's display label (naming.config_label).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

from experiments.naming import algorithm_family_label, instance_groups

# Fixed color/marker order (never reassigned per-plot) so a given algorithm
# keeps the same look across every plot it appears in.
_ALGO_COLORS = [
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#e87ba4",  # magenta
    "#008300",  # green
    "#4a3aa7",  # violet
    "#e34948",  # red
]
_MARKERS = ["x", "o", "*", "^", "s", "D", "P", "v", "<", ">"]

# Markers without a fillable interior (x, +, *, ...) don't take an
# edgecolor distinct from their face color; matplotlib warns if given one,
# so only pass it for markers that actually have a face.
_UNFILLED_MARKERS = {"x", "+", "*", "1", "2", "3", "4"}


def _algorithm_styles(algorithm_names: list[str]) -> dict[str, tuple[str, str]]:
    """{raw algorithm name: (color, marker)}, assigned once in first-seen
    order across the whole run."""
    return {
        name: (_ALGO_COLORS[i % len(_ALGO_COLORS)], _MARKERS[i % len(_MARKERS)])
        for i, name in enumerate(algorithm_names)
    }


def _plot_instance(
    group: pd.DataFrame,
    styles: dict[str, tuple[str, str]],
    y_col: str,
    ylabel: str,
    title: str,
    out_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(7, 5))

    for algo_name, rows in group.groupby("algorithm"):
        color, marker = styles[algo_name]
        rows = rows.sort_values("relative_overhead")

        if len(rows) > 1:
            ax.plot(rows["relative_overhead"], rows[y_col], color=color, linewidth=1.2, alpha=0.6, zorder=1)

        edge_kwargs = {} if marker in _UNFILLED_MARKERS else {"edgecolors": "black", "linewidths": 0.4}
        ax.scatter(
            rows["relative_overhead"],
            rows[y_col],
            color=color,
            marker=marker,
            s=70,
            alpha=0.9,
            zorder=2,
            **edge_kwargs,
        )
        for _, row in rows.iterrows():
            ax.annotate(
                row["algorithm_label"],
                (row["relative_overhead"], row[y_col]),
                textcoords="offset points",
                xytext=(6, 4),
                fontsize=7,
            )

    ax.set_yscale("log")
    ax.set_xlabel("relative overhead over entropy  ((bits/key - H) / H)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, which="both", linestyle=":", alpha=0.5)

    algo_handles = [
        Line2D(
            [0], [0], marker=marker, color=color, linestyle="None",
            markeredgecolor="black" if marker not in _UNFILLED_MARKERS else color,
            markeredgewidth=0.4, markersize=9, label=algorithm_family_label(name),
        )
        for name, (color, marker) in styles.items()
        if name in group["algorithm"].unique()
    ]
    ax.legend(handles=algo_handles, title="algorithm", loc="best")

    fig.tight_layout()
    fig.savefig(out_path, format="pdf")
    plt.close(fig)


def plot_overhead_vs_time(summary: pd.DataFrame, algorithms: list, plot_dir: Path) -> None:
    plot_dir.mkdir(parents=True, exist_ok=True)

    algo_names = list(dict.fromkeys(a.name for a in algorithms))
    styles = _algorithm_styles(algo_names)

    for instance, group in instance_groups(summary):
        label = f"{instance.distribution} ({instance.parameters})"
        _plot_instance(
            group,
            styles,
            y_col="construction_time_per_key_ns",
            ylabel="mean construction time per key (ns, log scale)",
            title=f"Relative overhead vs. construction time - {label}",
            out_path=plot_dir / f"overhead_vs_construction_{instance.stem}.pdf",
        )
        _plot_instance(
            group,
            styles,
            y_col="query_time_per_key_ns",
            ylabel="mean query time per key (ns, log scale)",
            title=f"Relative overhead vs. query time - {label}",
            out_path=plot_dir / f"overhead_vs_query_{instance.stem}.pdf",
        )
