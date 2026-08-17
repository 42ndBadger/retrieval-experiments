use serde::Serialize;

use crate::instance::BenchmarkInstance;
use crate::instance::Input;

#[derive(Debug, Serialize)]
pub struct ConstructionResult {
    iteration: usize,
    time_ns: u64,
    size: usize,
}

pub fn construction_benchmark<'a, T: BenchmarkInstance<'a>>(
    iters: usize,
    input: Input<'a>,
    param: &T::Params,
) -> Vec<ConstructionResult> {
    let mut results = Vec::with_capacity(iters);
    for i in 0..iters {
        let start = std::time::Instant::now();
        let t = T::create(input, param);
        let took = start.elapsed();
        let size = t.size();
        results.push(ConstructionResult {
            iteration: i,
            time_ns: took.as_nanos() as u64,
            size,
        });
    }
    results
}

#[derive(Debug, Serialize)]
pub struct QueryResult {
    iteration: usize,
    size: usize,
    query_time_ns: u64,
}

pub fn query_benchmark<'a, T: BenchmarkInstance<'a>>(
    iters: usize,
    input: Input<'a>,
    param: &T::Params,
) -> Vec<QueryResult> {
    let t = T::create(input, param);
    let size = t.size();
    let mut results = Vec::with_capacity(iters);
    let chunk = 100;
    let keys = input
        .chunks_exact(chunk)
        .map(|x| x.iter().map(|x| x.0))
        .cycle()
        .take(iters);

    for (iter, keys) in keys.enumerate() {
        // todo batch queries for less overhead
        let num_keys = keys.len();
        let start = std::time::Instant::now();
        for key in keys {
            t.query(key);
        }
        let took = start.elapsed() / num_keys as u32;
        results.push(QueryResult {
            iteration: iter,
            size,
            query_time_ns: took.as_nanos() as u64,
        });
    }

    results
}
