"""Step 4 (part 2): tradeoff plots of relative overhead (over the
analytical entropy) vs. construction/query time.

One PDF per (distribution family, {construction, query}) pair. Within a
plot, marker shape distinguishes the distribution's swept parameter(s) and
color distinguishes the algorithm - so a legend entry's shape reads across
algorithms and its color reads across parameter values.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

from experiments.naming import param_label_and_key

# Fixed marker order (never reassigned per-plot) so the same swept
# parameter, when it appears in more than one plot, keeps its shape.
_MARKERS = ["x", "o", "v", "^", "s", "D", "P", "*", "<", ">"]

# Validated categorical palette (see the dataviz skill's palette.md), first
# slots first - colorblind-safe for up to 3 series at once. Assigned once,
# in a fixed order (config declaration order), never re-derived per plot.
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


def _algorithm_colors(algorithms: list[str]) -> dict[str, str]:
    return {algo: _ALGO_COLORS[i % len(_ALGO_COLORS)] for i, algo in enumerate(algorithms)}


def _plot_overhead_vs(
    group: pd.DataFrame,
    time_col: str,
    xlabel: str,
    title: str,
    out_path: Path,
    algo_colors: dict[str, str],
) -> None:
    distribution = group["distribution"].iloc[0]
    group = group.copy()
    labels_and_keys = group.apply(
        lambda r: param_label_and_key(distribution, r), axis=1
    )
    group["_param_label"] = [lk[0] for lk in labels_and_keys]
    sort_keys = {lk[0]: lk[1] for lk in labels_and_keys}
    ordered_labels = sorted(sort_keys, key=lambda l: sort_keys[l])
    marker_for_label = {l: _MARKERS[i % len(_MARKERS)] for i, l in enumerate(ordered_labels)}

    # Markers without a fillable interior (x, +, *, ...) don't take an
    # edgecolor distinct from their face color; matplotlib warns if given
    # one, so only pass it for markers that actually have a face.
    _UNFILLED_MARKERS = {"x", "+", "*", "1", "2", "3", "4"}

    fig, ax = plt.subplots(figsize=(7, 5))
    for (algorithm, label), rows in group.groupby(["algorithm", "_param_label"]):
        rows = rows.sort_values(time_col)
        marker = marker_for_label[label]
        edge_kwargs = {} if marker in _UNFILLED_MARKERS else {"edgecolors": "black", "linewidths": 0.4}
        ax.scatter(
            rows[time_col],
            rows["relative_overhead"],
            color=algo_colors[algorithm],
            marker=marker,
            s=70,
            alpha=0.85,
            **edge_kwargs,
        )
    ax.set_xscale("log")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("relative overhead over entropy  ((bits/key - H) / H)")
    ax.set_title(title)
    ax.grid(True, which="both", linestyle=":", alpha=0.5)

    algo_handles = [
        Line2D(
            [0], [0], marker="o", color="w", markerfacecolor=color,
            markeredgecolor="black", markeredgewidth=0.4, markersize=9, label=algo,
        )
        for algo, color in algo_colors.items()
        if algo in group["algorithm"].unique()
    ]
    param_handles = [
        Line2D(
            [0], [0], marker=marker, color="black", linestyle="None",
            markersize=9, label=label,
        )
        for label, marker in marker_for_label.items()
    ]
    algo_legend = ax.legend(handles=algo_handles, title="algorithm", loc="upper left")
    ax.add_artist(algo_legend)
    ax.legend(handles=param_handles, title="parameters", loc="upper right", fontsize=8)

    fig.tight_layout()
    fig.savefig(out_path, format="pdf")
    plt.close(fig)


def plot_overhead_vs_time(summary: pd.DataFrame, algorithms: list[str], plot_dir: Path) -> None:
    plot_dir.mkdir(parents=True, exist_ok=True)
    algo_colors = _algorithm_colors(algorithms)
    for distribution, group in summary.groupby("distribution"):
        _plot_overhead_vs(
            group,
            time_col="mean_construction_time_ns",
            xlabel="mean construction time (ns, log scale)",
            title=f"Relative overhead vs. construction time ({distribution})",
            out_path=plot_dir / f"overhead_vs_construction_{distribution}.pdf",
            algo_colors=algo_colors,
        )
        _plot_overhead_vs(
            group,
            time_col="mean_query_time_ns",
            xlabel="mean query time (ns, log scale)",
            title=f"Relative overhead vs. query time ({distribution})",
            out_path=plot_dir / f"overhead_vs_query_{distribution}.pdf",
            algo_colors=algo_colors,
        )
