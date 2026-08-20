// Minimal shared prelude for the experiment-result Typst templates
// (comparison_table.typ, tradeoff_plots.typ). Only carries what those two
// actually use - re-exporting `strfmt` (for the number formatting in
// comparison_table.typ) and a small `colors` palette (its `lightgray`/
// `yellow` keys, used for that table's row/section shading).
#import "@preview/oxifmt:0.2.1": strfmt

#let colors = (
  lightgray: luma(90%),
  yellow: rgb("#fdf1c8"),
)

#let Geo = math.op("Geo")
#let Ber = math.op("Ber")
#let Uni = math.cal("U")
