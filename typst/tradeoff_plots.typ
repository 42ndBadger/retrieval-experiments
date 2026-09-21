#import "style.typ": *
#import "@preview/lilaq:0.6.0" as lq

#let tradeoff-plots(summary, x: "rel_space_overhead", y: "constr_time") = {
let x = "rel_space_overhead"
let y = "constr_time"


let custom_marks = ("Consensus": emoji.faith.yinyang).map(s => (mark => place(center+horizon, text(mark.fill, s))))

let colors = (blue, orange, green, yellow, black)

let fmt_disr(name, params) = {
  if name == "bernoulli" [$Ber(#params.p)$] 
  else if name == "uniform" [$Uni([#params.bound])$]
  else if name == "truncated_geometric" [$Geo(#params.p) mod #params.bound$]
  else {name}
}



let other_marks = ("o", "s", "s3", "^", "v", "<", ">", "x", "s4", "s5", "p5", "p6").map(s => lq.marks.at(s))
let alg_familys = summary.algs.map(a => a.name.split().at(0)).dedup().enumerate().map(t=>("name": t.at(1), "color": colors.at(t.at(0)), "mark": custom_marks.at(t.at(1), default: other_marks.at(t.at(0)))))

let unzip(arr) = arr.fold(((),()), (acc, tuple) => (acc.at(0) + (tuple.at(0),), acc.at(1) + (tuple.at(1),)))

let columns = 3
let plots = summary.distrs.map(d => d.sub).flatten().len()
let rows = plots /columns
let size = 10cm / columns

figure({
let n = -1
for dist in summary.distrs {
  for var in dist.sub {
  n += 1
  let alg_data = summary.algs.map(a => (name: a.name, data: a.distrs
    .find(d => d.name == dist.name).variants
    .find(v => v.params == var.params).measurements
  ))
  let xs = alg_data.map(a => a.data.at(x))
  let ys = alg_data.map(a => a.data.at(y))
  let labels = alg_data.map(a => a.name)

  lq.diagram(
    title: (fmt_disr(dist.name, var.params)),
    width: size,
    height: size,
    legend: none,
    xlabel: if n / columns >= rows - 1 {x} else {none},
    ylabel: if calc.rem(n, columns) == 0 {y} else {none},
    ..alg_familys.map(fam =>{
      let (xs, ys) = unzip(
        alg_data.filter(a => a.name.starts-with(fam.name))
        .map(a => (a.data.at(x), a.data.at(y)))
        .sorted()
      )
      lq.plot(
        xs, ys,
        label: fam.name,
        color: fam.color,
        mark: fam.mark,
       )
     })
    )
  }
}

v(1em)

align(center,table(columns: 2 * alg_familys.len(), align: center,
..alg_familys.map(fam =>
(place(dy: .3em, (fam.mark)(("fill": fam.color, "size": .5em, stroke: none))),
fam.name
)
).flatten()
)
)

},
caption: [Tradeoff plots for different distibutions, n = #summary.n. Bottom left is better. ],
kind: "diagram",
supplement: "Diagram"
)
}



