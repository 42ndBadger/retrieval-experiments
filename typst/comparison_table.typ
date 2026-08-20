#import "style.typ": *

#let comp-table(data) = [

#let num_cols =  1+ data.at("distrs").map(x => x.at("sub")).flatten().len()


#let distr_names = (bernoulli: $Ber(p)$, uniform: $Uni([k])$, truncated_geometric: $Geo(p) mod k$) 

#let row(alg, fn) = {
  for distr in data.distrs {
          for sub in distr.sub {
            let measurements = alg.distrs.find(x => x.at("name") == distr.name).variants.find(x => x.params == sub.params).measurements
            (table.cell(fn(measurements)),)
          }
        }
}

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
  [], ..data.at("distrs").map(x => x.at("sub")).flatten().map(x =>  table.cell([#x.params])),
  [$H_0$], ..data.at("distrs").map(x => x.at("sub")).flatten().map(x =>  table.cell([#strfmt("{:.2}", x.empirical_entropy)])),

),

..for alg in data.algs {
  let name = alg.name
  (table.cell(colspan: num_cols,[#set text();*#name* #if name.starts-with("Consensus") [$"max_diff"=#alg.params.max_difficulty_of_task$]] , stroke: (y: 0.5pt), fill: colors.yellow, align: left),)
   
  ([C [µs]],) + row(alg, mes => [#strfmt("{:.2}", mes.constr_time / 1000)])
  ([Q [ns]],) + row(alg, mes => [#strfmt("{:.1}", mes.query_time)\ #text(strfmt("±{:.1}", mes.query_std), fill: luma(40%))])
  ([S [bit]],) + row(alg, mes => [#strfmt("{:.2}", mes.constr_time / 1000)])
  ([O [%]],) + row(alg, mes => [#strfmt("{:.1}", mes.rel_space_overhead * 100)])
  
},


), caption: [Benchmarking results for $n=strfmt("{}", #data.n,   fmt-thousands-separator: "\u{2006}")$. C denotes construction time, Q query time, S space usage, O space overhead relative to $H_0$. All measurement values are per key.])

//#data
]
