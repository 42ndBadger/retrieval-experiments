// Entry point compiled by render.sh: renders the full summary report (the
// comparison table, then the tradeoff plots) for one experiment run, from
// its summary.json. Expects the path to that summary.json passed in as
// the `summary` Typst input, e.g.:
//
//   typst compile --input summary=/path/to/summary.json summary.typ out.pdf
//
// (render.sh sets this up with the right --root/--input for you.)

#import "comparison_table.typ": comp-table
#import "tradeoff_plots.typ": tradeoff-plots

#let summary = json(sys.inputs.at("summary"))

#comp-table(summary)
#pagebreak()
#tradeoff-plots(summary)
