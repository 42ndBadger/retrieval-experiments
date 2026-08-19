use consensus_retrieval::{ConsensusRetrieval, parameters::Parameters};

use crate::{
    caramel::CsfU32,
    instance::{BenchmarkInstance, Value},
    lsf::LsfU32,
};

impl<'a> BenchmarkInstance<'a> for ConsensusRetrieval<&'a str, u32> {
    // ust `b` for now
    type Params = Parameters;
    fn create(input: crate::instance::Input<'a>, params: &Self::Params) -> Self {
        let input: std::collections::HashMap<&str, u32, ahash::RandomState> =
            input.iter().map(|(k, v)| (*k, *v)).collect();
        ConsensusRetrieval::new_with_parameters(&input, *params, ahash::RandomState::new())
    }

    fn query(&self, key: &str) -> Value {
        ConsensusRetrieval::query(self, &key)
    }

    fn size(&self) -> usize {
        self.variable_part_bit_size().div_ceil(8)
    }
}

impl<'a> BenchmarkInstance<'a> for CsfU32 {
    type Params = ();

    fn create(input: crate::instance::Input<'_>, params: &Self::Params) -> Self {
        let (keys, values): (Vec<_>, Vec<_>) = input.iter().map(|(k, v)| (k.as_bytes(), v)).unzip();
        let csf = CsfU32::new(&keys, &values).expect("valid");
        csf
    }

    fn query(&self, key: &str) -> Value {
        CsfU32::query(self, key.as_bytes())
    }

    fn size(&self) -> usize {
        self.size_bytes()
    }
}

impl<'a> BenchmarkInstance<'a> for LsfU32 {
    type Params = ();

    fn create(input: crate::instance::Input<'_>, _params: &Self::Params) -> Self {
        let (keys, values): (Vec<_>, Vec<_>) = input.iter().map(|(k, v)| (k.as_bytes(), v)).unzip();
        LsfU32::new(&keys, &values).expect("valid")
    }

    fn query(&self, key: &str) -> Value {
        LsfU32::query(self, key.as_bytes())
    }

    fn size(&self) -> usize {
        self.size_bytes()
    }
}
