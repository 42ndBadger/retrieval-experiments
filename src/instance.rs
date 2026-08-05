pub type Value = u32;
pub type Input<'a> = &'a [(&'a str, Value)];

pub trait BenchmarkInstance<'a> {
    type Params;
    fn create(input: Input<'a>, params: &Self::Params) -> Self;
    fn query(&self, key: &str) -> Value;
    // in bytes
    fn size(&self) -> usize;
}
