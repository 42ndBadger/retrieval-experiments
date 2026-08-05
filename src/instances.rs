use consensus_retrieval::ConsensusRetrieval;

use crate::{
    caramel::CsfU32,
    instance::{BenchmarkInstance, Value},
};

// impl BenchmarkInstance for ConsensusRetrieval<str, u32> {
//     // ust `b` for now
//     type Params = usize;
//     fn create(input: crate::instance::Input<'_>, params: &Self::Params) -> Self {
//         let input = input.iter().map(|(k, v)| (*k, *v)).collect();
//         // ConsensusRetrieval::new_random(&input, *params)
//         todo!()
//     }

//     fn query(&self, key: &str) -> Value {
//         ConsensusRetrieval::query(self, &key)
//     }

//     fn size(&self) -> usize {
//         self.variable_part_bit_size().div_ceil(8)
//     }
// }

impl BenchmarkInstance for CsfU32 {
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
