"""Step 4 (part 3): summary tables - one row per dataset, with a
(algorithm, metric) column per algorithm: relative space overhead,
absolute bits/key, and per-key construction/query time.

Written as both a CSV (for further post-processing) and a rendered PDF
(matching the plots' PDF convention), grouped and shaded by distribution
family so the "one table" still reads as separate distribution sections.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import pandas as pd

from experiments.naming import param_label_and_key

# Each metric is computed from one row of `build_summary`'s output.
_METRICS: dict[str, Callable[[pd.Series], float]] = {
    "space overhead (%)": lambda r: r["relative_overhead"] * 100,
    "bits/key": lambda r: r["bits_per_key"],
    "construction time/key (ns)": lambda r: r["mean_construction_time_ns"] / r["n"],
    "query time/key (ns)": lambda r: r["mean_query_time_ns"],
}

# Alternating row-group background shades, one per distribution family (light surface).
_GROUP_COLORS = ["#f4f4f2", "#e8e8e5"]


def build_table(summary: pd.DataFrame, algorithms: list) -> pd.DataFrame:
    """Pivot `summary` into rows = (distribution, parameters), columns =
    (algorithm_label, metric), sorted by distribution (declaration order in the
    data) then swept parameter value."""
    from experiments.results import algo_label

    df = summary.copy()
    labels_and_keys = df.apply(
        lambda r: param_label_and_key(r["distribution"], r), axis=1
    )
    df["parameters"] = [lk[0] for lk in labels_and_keys]
    df["_sort_key"] = [lk[1] for lk in labels_and_keys]

    algo_labels = {a.name: algo_label(a) for a in algorithms}

    dist_order = list(dict.fromkeys(df["distribution"]))
    dataset_keys = (
        df[["distribution", "parameters", "_sort_key"]]
        .drop_duplicates(subset=["distribution", "parameters"])
        # stable sort by sweep key first, then by distribution (declaration
        # order), so each distribution's rows come out low-to-high internally.
        .sort_values(by="_sort_key", kind="stable")
        .sort_values(by="distribution", key=lambda col: col.map(dist_order.index), kind="stable")
    )

    rows = []
    for _, key in dataset_keys.iterrows():
        subset = df[
            (df["distribution"] == key["distribution"])
            & (df["parameters"] == key["parameters"])
        ]
        row = {"distribution": key["distribution"], "parameters": key["parameters"]}
        for algo_spec in algorithms:
            label = algo_labels[algo_spec.name]
            matches = subset[subset["algorithm_label"] == label]
            if matches.empty:
                for metric in _METRICS:
                    row[(label, metric)] = float("nan")
                continue
            algo_row = matches.iloc[0]
            for metric, fn in _METRICS.items():
                row[(label, metric)] = fn(algo_row)
        rows.append(row)

    table = pd.DataFrame(rows).set_index(["distribution", "parameters"])
    table.columns = pd.MultiIndex.from_tuples(table.columns, names=["algorithm", "metric"])
    return table


def write_table_csv(table: pd.DataFrame, out_path: Path) -> None:
    table.to_csv(out_path)


def _format_value(v: float) -> str:
    if pd.isna(v):
        return "–"
    if abs(v) >= 100:
        return f"{v:,.0f}"
    return f"{v:.3g}"


def write_table_pdf(table: pd.DataFrame, out_path: Path) -> None:
    n_rows, n_cols = table.shape
    col_labels = [f"{algo}\n{metric}" for algo, metric in table.columns]
    row_labels = [f"{dist}\n{params}" for dist, params in table.index]
    cell_text = [[_format_value(v) for v in row] for row in table.itertuples(index=False)]

    fig_w = 1.8 + 1.5 * n_cols
    fig_h = 0.9 + 0.45 * n_rows
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis("off")

    mpl_table = ax.table(
        cellText=cell_text,
        rowLabels=row_labels,
        colLabels=col_labels,
        loc="center",
        cellLoc="center",
    )
    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(8)
    mpl_table.scale(1, 1.8)

    dist_order = list(dict.fromkeys(d for d, _ in table.index))
    color_for_dist = {d: _GROUP_COLORS[i % len(_GROUP_COLORS)] for i, d in enumerate(dist_order)}
    for i, (dist, _params) in enumerate(table.index):
        color = color_for_dist[dist]
        mpl_table[(i + 1, -1)].set_facecolor(color)
        for j in range(n_cols):
            mpl_table[(i + 1, j)].set_facecolor(color)

    fig.tight_layout()
    fig.savefig(out_path, format="pdf")
    plt.close(fig)


def write_tables(summary: pd.DataFrame, algorithms: list, plot_dir: Path) -> None:
    plot_dir.mkdir(parents=True, exist_ok=True)
    table = build_table(summary, algorithms)
    write_table_csv(table, plot_dir / "summary_table.csv")
    write_table_pdf(table, plot_dir / "summary_table.pdf")
