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

// `environment` is only present in summary.json from 2026-08-20 onward
// (experiments/environment.py) - missing entirely for older files, and
// any individual field can be `null` too (best-effort capture, see that
// module's docstring), so both are tolerated rather than erroring.
#let env = summary.at("environment", default: none)

#comp-table(summary)
#pagebreak()
#tradeoff-plots(summary)

#if env != none {
  let fields = (
    ("Host", env.at("hostname", default: none)),
    ("OS", env.at("os", default: none)),
    ("CPU", env.at("cpu", default: none)),
    ("Logical cores", env.at("logical_cpus", default: none)),
    ("rustc", env.at("rustc_version", default: none)),
    ("C++ compiler", env.at("cxx_compiler_version", default: none)),
    ("cmake", env.at("cmake_version", default: none)),
  ).filter(f => f.at(1) != none)

  v(1em)
  [= Execution environment]
  fields.map(f => [#f.at(0): #f.at(1)]).join([ · ])
}
