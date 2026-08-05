pub type Value = u32;
pub type Input<'a> = &'a [(&'a str, Value)];

pub trait BenchmarkInstance {
    fn create(input: Input<'_>) -> Self;
    fn query(&self, key: &str) -> Value;
    fn size(&self) -> usize;
}
