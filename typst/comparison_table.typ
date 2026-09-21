#import "style.typ": *

#let comp-table(data) = [

// +1 for the trailing geometric-mean (GM) column.
#let num_cols =  2 + data.at("distrs").map(x => x.at("sub")).flatten().len()


#let distr_names = (bernoulli: $Ber(p)$, uniform: $Uni([k])$, truncated_geometric: $Geo(p) mod k$)

#let row(alg, fn) = {
  for distr in data.distrs {
          for sub in distr.sub {
            let measurements = alg.distrs.find(x => x.at("name") == distr.name).variants.find(x => x.params == sub.params).measurements
            (table.cell(fn(measurements)),)
          }
        }
}

// Raw (unformatted) values for one algorithm/metric across every swept
// distribution/param combination, in the same order `row` iterates them.
#let values-for(alg, extractor) = {
  data.distrs.map(distr => distr.sub.map(sub => {
    let measurements = alg.distrs.find(x => x.at("name") == distr.name).variants.find(x => x.params == sub.params).measurements
    extractor(measurements)
  })).flatten()
}

// Geometric mean: nth root of the product. Requires strictly positive values
// - see the caller comments below for how each metric is kept positive.
#let geomean(values) = calc.pow(values.fold(1, (acc, v) => acc * v), 1 / values.len())

#let gmean-cell(alg, extractor, fmt) = table.cell(fmt(geomean(values-for(alg, extractor))), stroke: (left: 0.5pt))

#show table.cell: it => if it.x  == 0 {
  set align(horizon + left)
  it
} else {
  set align(right)
  it
}

//#set table.cell(stroke: (x,y) => colors)

#set table(fill: (x,y) => if (calc.rem(y,2) == 0) {colors.lightgray} else {white})

#figure(table(columns: num_cols,

table.header(
  [], ..data.distrs.map(x => table.cell(distr_names.at(x.name), colspan: x.sub.len(), align: center)),
  table.cell(rowspan: 3, align: horizon + center, stroke: (left: 0.5pt))[*GM*],
  [], ..data.at("distrs").map(x => x.at("sub")).flatten().map(x =>  table.cell([#x.params])),
  [$H_0$], ..data.at("distrs").map(x => x.at("sub")).flatten().map(x =>  table.cell([#strfmt("{:.2}", x.empirical_entropy)])),

),

..for alg in data.algs {
  let name = alg.name
  (table.cell(colspan: num_cols,[#set text();*#name* #if name.starts-with("Consensus") [$"max_diff"=#alg.params.max_difficulty_of_task$]] , stroke: (y: 0.5pt), fill: colors.yellow, align: left),)
   
  ([C [µs]],) + row(alg, mes => [#strfmt("{:.2}", mes.constr_time / 1000)]) + (gmean-cell(alg, mes => mes.constr_time / 1000, v => [#strfmt("{:.2}", v)]),)
  ([Q [ns]],) + row(alg, mes => [#strfmt("{:.1}", mes.query_time)\ #text(strfmt("±{:.1}", mes.query_std), fill: luma(40%))]) + (gmean-cell(alg, mes => mes.query_time, v => [#strfmt("{:.1}", v)]),)
  ([S [bit]],) + row(alg, mes => [#strfmt("{:.2}", mes.space_bits)]) + (gmean-cell(alg, mes => mes.space_bits, v => [#strfmt("{:.2}", v)]),)
  // GM here is the geomean of the bits/entropy *ratio* (1 + overhead), converted back to a percentage - not a
  // naive geomean of the overhead percentages themselves, which breaks at 0% and is undefined below 0%.
  ([O [%]],) + row(alg, mes => [#strfmt("{:.1}", mes.rel_space_overhead * 100)]) + (gmean-cell(alg, mes => 1 + mes.rel_space_overhead, v => [#strfmt("{:.1}", (v - 1) * 100)]),)

},


), caption: [Benchmarking results for $n=strfmt("{}", #data.n,   fmt-thousands-separator: "\u{2006}")$. C denotes construction time, Q query time, S space usage, O space overhead relative to $H_0$. All measurement values are per key. GM is the geometric mean across all swept distribution/parameter columns for that row (for O, computed on the bits/entropy ratio and converted back to a percentage).])

//#data
]
