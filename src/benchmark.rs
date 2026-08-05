use crate::instance::BenchmarkInstance;
use crate::instance::Input;

pub struct ConstructionResult {
    iteration: usize,
    time_ns: u64,
    size: usize,
}

pub fn construction_benchmark<T: BenchmarkInstance>(
    iters: usize,
    input: Input<'_>,
) -> Vec<ConstructionResult> {
    let mut results = Vec::with_capacity(iters);
    for i in 0..iters {
        let start = std::time::Instant::now();
        let t = T::create(input);
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

pub struct QueryResult {
    iteration: usize,
    size: usize,
    query_time_ns: u64,
}

pub fn query_benchmark<T: BenchmarkInstance>(iters: usize, input: Input<'_>) -> Vec<QueryResult> {
    let t = T::create(input);
    let size = t.size();
    let mut results = Vec::with_capacity(iters);
    let keys = input.iter().map(|x| x.0).cycle().take(iters);

    for (iter, key) in keys.enumerate() {
        let start = std::time::Instant::now();
        // todo batch queries for less overhead
        t.query(key);
        let took = start.elapsed();
        results.push(QueryResult {
            iteration: iter,
            size,
            query_time_ns: took.as_nanos() as u64,
        });
    }

    results
}
