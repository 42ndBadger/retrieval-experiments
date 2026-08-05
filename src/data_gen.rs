use rand_distr::Bernoulli;
use rand_distr::Distribution as _;
use rand_distr::Geometric;
use rand_distr::Uniform;

pub enum Distribution {
    Uniform { max: u64 },
    Bernoulli { p: f64 },
    TruncatedGeometric { p: f64, max: u64 },
}

impl Distribution {
    pub fn generate_values(&self, n: usize) -> Vec<u64> {
        match self {
            Distribution::Uniform { max } => Uniform::new(0, *max)
                .unwrap()
                .sample_iter(rand::rng())
                .take(n)
                .collect(),
            Distribution::Bernoulli { p } => Bernoulli::new(*p)
                .unwrap()
                .sample_iter(rand::rng())
                .map(|b| b as u64)
                .take(n)
                .collect(),
            Distribution::TruncatedGeometric { p, max } => Geometric::new(*p)
                .unwrap()
                .sample_iter(rand::rng())
                .map(|x| x % *max)
                .take(n)
                .collect(),
        }
    }
}

pub fn string_keys(n: usize) -> Vec<String> {
    (0..n).map(|i| format!("key_{}", i)).collect()
}
