"""Step 4 (part 3): summary table - rows grouped by algorithm *config*
(one group per [[algorithm]] entry, one metric sub-row each: construction
time/key, query time/key, space overhead %, bits/key, plus consensus's
consensus/insertion bits-per-key space breakdown - dashes for configs that
don't report it), columns grouped by distribution family (one column per
swept value, via naming.dataset_instances - the same enumeration
plotting.py uses).

Written as both a CSV (for further post-processing) and a Typst source
file (`summary_table.typ`) - compiling that to PDF is left as a separate,
manual step (`typst compile summary_table.typ`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pandas as pd

from experiments.naming import config_row_label, dataset_instances, param_label_and_key

# Each metric is computed from one row of `build_summary`'s output. Order
# here is the row order within each config's group in the table. The last
# two are algorithm-specific (currently only consensus, via
# results.py::_extra_bit_fields) - `.get` with a NaN default so configs
# that don't report them render as "-" instead of erroring, and so the
# whole table still builds even if no config in this run produces them.
_METRICS: dict[str, Callable[[pd.Series], float]] = {
    "construction time/key (ns)": lambda r: r["construction_time_per_key_ns"],
    "query time/key (ns)": lambda r: r["query_time_per_key_ns"],
    "space overhead (%)": lambda r: r["space_overhead_pct"],
    "bits/key": lambda r: r["bits_per_key"],
    "consensus bits/key": lambda r: r.get("consensus_bits_per_key", float("nan")),
    "insertion bits/key": lambda r: r.get("insertion_bits_per_key", float("nan")),
}

# Alternating column-group background shades, one per distribution family.
_GROUP_COLORS = ["#f4f4f2", "#e8e8e5"]


def build_table(summary: pd.DataFrame, algorithms: list) -> pd.DataFrame:
    """Pivot `summary` into rows = (algorithm config label, metric),
    columns = (distribution, parameters) - one row-group per
    [[algorithm]] config (declaration order), one column per dataset
    instance (naming.dataset_instances order)."""
    instances = dataset_instances(summary)

    df = summary.copy()
    labels_and_keys = df.apply(lambda r: param_label_and_key(r["distribution"], r), axis=1)
    df["_parameters"] = [lk[0] for lk in labels_and_keys]

    rows = []
    for algo_spec in algorithms:
        row_label = config_row_label(algo_spec, algorithms)
        subset = df[df["algo_spec"].apply(lambda s: s is algo_spec)]
        for metric, fn in _METRICS.items():
            row = {"config": row_label, "metric": metric}
            for inst in instances:
                match = subset[
                    (subset["distribution"] == inst.distribution) & (subset["_parameters"] == inst.parameters)
                ]
                row[(inst.distribution, inst.parameters)] = fn(match.iloc[0]) if not match.empty else float("nan")
            rows.append(row)

    table = pd.DataFrame(rows).set_index(["config", "metric"])
    table.columns = pd.MultiIndex.from_tuples(table.columns, names=["distribution", "parameters"])
    return table


def write_table_csv(table: pd.DataFrame, out_path: Path) -> None:
    table.to_csv(out_path)


def _format_value(v: float) -> str:
    if pd.isna(v):
        return "–"
    if abs(v) >= 100:
        return f"{v:,.0f}"
    return f"{v:.3g}"


def _typst_cell(
    content: str,
    *,
    colspan: int = 1,
    rowspan: int = 1,
    fill: str | None = None,
    align: str | None = None,
) -> str:
    args = []
    if colspan != 1:
        args.append(f"colspan: {colspan}")
    if rowspan != 1:
        args.append(f"rowspan: {rowspan}")
    if fill is not None:
        args.append(f'fill: rgb("{fill}")')
    if align is not None:
        args.append(f"align: {align}")
    prefix = f"table.cell({', '.join(args)})" if args else ""
    return f"{prefix}[{content}]"


def _column_family_spans(instances: list[tuple[str, str]]) -> list[tuple[str, int]]:
    """[(distribution, number of consecutive columns)] in column order."""
    spans: list[tuple[str, int]] = []
    for dist, _params in instances:
        if spans and spans[-1][0] == dist:
            spans[-1] = (dist, spans[-1][1] + 1)
        else:
            spans.append((dist, 1))
    return spans


def write_table_typ(table: pd.DataFrame, out_path: Path) -> None:
    """Emit a Typst source file rendering `table` with merged header cells
    (one per distribution family) and column shading by distribution
    family. Not compiled to PDF here.

    Each algorithm config gets its own full-width section row for its
    label (bold, left-aligned) followed by its metric rows - matching the
    whiteboard sketch's layout (a title band per config, not a
    vertically-centered side label)."""
    instances = [(dist, params) for dist, params in table.columns]
    family_spans = _column_family_spans(instances)
    fill_for_family = {d: _GROUP_COLORS[i % len(_GROUP_COLORS)] for i, (d, _span) in enumerate(family_spans)}
    fill_for_col: list[str] = []
    for dist, span in family_spans:
        fill_for_col += [fill_for_family[dist]] * span

    n_cols = 1 + len(instances)
    cells: list[str] = []

    # Header row 1: corner (spans both header rows, just the metric-name
    # column) + one colspan cell per distribution family.
    cells.append(_typst_cell("", rowspan=2))
    for dist, span in family_spans:
        cells.append(_typst_cell(dist, colspan=span, fill=fill_for_family[dist]))
    # Header row 2: one cell per instance (its swept-parameter label).
    for (_dist, params), fill in zip(instances, fill_for_col):
        cells.append(_typst_cell(params, fill=fill))

    # Body: one full-width title row per config, then one row per metric.
    for config in dict.fromkeys(c for c, _m in table.index):
        sub = table.loc[config]
        cells.append(_typst_cell(f"*{config}*", colspan=n_cols, align="left + horizon"))
        for metric in sub.index:
            cells.append(_typst_cell(metric, align="left + horizon"))
            row = sub.loc[metric]
            for col, fill in zip(instances, fill_for_col):
                cells.append(_typst_cell(_format_value(row[col]), fill=fill))

    body = ",\n  ".join(cells)
    content = f"""#set page(width: auto, height: auto, margin: 1cm)
#set text(size: 8pt)

#table(
  columns: {n_cols},
  align: center + horizon,
  stroke: 0.5pt,
  {body},
)
"""
    out_path.write_text(content)


def write_tables(summary: pd.DataFrame, algorithms: list, plot_dir: Path) -> None:
    plot_dir.mkdir(parents=True, exist_ok=True)
    table = build_table(summary, algorithms)
    write_table_csv(table, plot_dir / "summary_table.csv")
    write_table_typ(table, plot_dir / "summary_table.typ")
