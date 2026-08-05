use std::ffi::{CStr, c_char, c_int, c_void};
use std::fmt;

unsafe extern "C" {
    fn caramel_csf_u32_build(
        keys: *const *const u8,
        key_lens: *const usize,
        values: *const u32,
        n: usize,
        verbose: c_int,
        err: *mut c_char,
        err_cap: usize,
    ) -> *mut c_void;
    fn caramel_csf_u32_query(handle: *const c_void, key: *const u8, key_len: usize) -> u32;
    fn caramel_csf_u32_size(handle: *const c_void) -> usize;
    fn caramel_csf_u32_stats(handle: *const c_void, out: *mut CsfStats) -> c_int;
    fn caramel_csf_u32_free(handle: *mut c_void);

    fn caramel_csf_u64_build(
        keys: *const *const u8,
        key_lens: *const usize,
        values: *const u64,
        n: usize,
        verbose: c_int,
        err: *mut c_char,
        err_cap: usize,
    ) -> *mut c_void;
    fn caramel_csf_u64_query(handle: *const c_void, key: *const u8, key_len: usize) -> u64;
    fn caramel_csf_u64_size(handle: *const c_void) -> usize;
    fn caramel_csf_u64_stats(handle: *const c_void, out: *mut CsfStats) -> c_int;
    fn caramel_csf_u64_free(handle: *mut c_void);
}

#[repr(C)]
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct CsfStats {
    pub in_memory_bytes: usize,
    pub solution_bytes: f64,
    pub filter_bytes: f64,
    pub metadata_bytes: f64,
    pub num_buckets: usize,
    pub total_solution_bits: usize,
    pub num_unique_symbols: usize,
    pub avg_bits_per_symbol: f64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CaramelError(String);

impl CaramelError {
    fn new(msg: String) -> Self {
        Self(msg)
    }
}

impl fmt::Display for CaramelError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl std::error::Error for CaramelError {}

macro_rules! define_csf {
    ($name:ident, $value:ty, $build:ident, $query:ident, $size:ident, $stats:ident, $free:ident) => {
        pub struct $name {
            ptr: *mut c_void,
        }

        impl $name {
            pub fn new(keys: &[&[u8]], values: &[$value]) -> Result<Self, CaramelError> {
                if keys.len() != values.len() {
                    return Err(CaramelError::new(format!(
                        "key count {} does not match value count {}",
                        keys.len(),
                        values.len()
                    )));
                }
                if keys.is_empty() {
                    return Err(CaramelError::new("cannot build an empty CSF".to_string()));
                }

                let key_ptrs: Vec<*const u8> = keys.iter().map(|k| k.as_ptr()).collect();
                let key_lens: Vec<usize> = keys.iter().map(|k| k.len()).collect();

                let mut err_buf = [0u8; 512];
                let ptr = unsafe {
                    $build(
                        key_ptrs.as_ptr(),
                        key_lens.as_ptr(),
                        values.as_ptr(),
                        keys.len(),
                        false as c_int,
                        err_buf.as_mut_ptr().cast::<c_char>(),
                        err_buf.len(),
                    )
                };
                if ptr.is_null() {
                    let msg = unsafe { CStr::from_ptr(err_buf.as_ptr().cast::<c_char>()) }
                        .to_string_lossy()
                        .into_owned();
                    return Err(CaramelError::new(msg));
                }
                Ok($name { ptr })
            }

            #[inline]
            pub fn query(&self, key: &[u8]) -> $value {
                unsafe { $query(self.ptr, key.as_ptr(), key.len()) }
            }

            #[inline]
            pub fn size_bytes(&self) -> usize {
                unsafe { $size(self.ptr) }
            }

            #[inline]
            pub fn stats(&self) -> CsfStats {
                let mut out = CsfStats {
                    in_memory_bytes: 0,
                    solution_bytes: 0.0,
                    filter_bytes: 0.0,
                    metadata_bytes: 0.0,
                    num_buckets: 0,
                    total_solution_bits: 0,
                    num_unique_symbols: 0,
                    avg_bits_per_symbol: 0.0,
                };
                unsafe {
                    $stats(self.ptr, &mut out);
                }
                out
            }
        }

        impl Drop for $name {
            fn drop(&mut self) {
                unsafe { $free(self.ptr) };
            }
        }
    };
}

define_csf!(
    CsfU32,
    u32,
    caramel_csf_u32_build,
    caramel_csf_u32_query,
    caramel_csf_u32_size,
    caramel_csf_u32_stats,
    caramel_csf_u32_free
);

define_csf!(
    CsfU64,
    u64,
    caramel_csf_u64_build,
    caramel_csf_u64_query,
    caramel_csf_u64_size,
    caramel_csf_u64_stats,
    caramel_csf_u64_free
);

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn build_and_query_u32() {
        let keys: Vec<&[u8]> = vec![b"red shoes", b"black bags", b"phone case"];
        let values = [42u32, 17, 8];
        let csf = CsfU32::new(&keys, &values).unwrap();
        assert_eq!(csf.query(b"red shoes"), 42);
        assert_eq!(csf.query(b"black bags"), 17);
        assert_eq!(csf.query(b"phone case"), 8);
        assert!(csf.size_bytes() > 0);
    }

    #[test]
    fn build_and_query_u64() {
        let keys: Vec<&[u8]> = vec![b"alpha", b"beta", b"gamma"];
        let values = [1u64 << 40, 7, u64::MAX];
        let csf = CsfU64::new(&keys, &values).unwrap();
        assert_eq!(csf.query(b"alpha"), 1u64 << 40);
        assert_eq!(csf.query(b"beta"), 7);
        assert_eq!(csf.query(b"gamma"), u64::MAX);
    }

    #[test]
    fn rejects_mismatched_lengths() {
        let keys: Vec<&[u8]> = vec![b"a"];
        let values = [1u32, 2];
        assert!(CsfU32::new(&keys, &values).is_err());
    }

    #[test]
    fn stats_report_space_usage() {
        let keys: Vec<&[u8]> = vec![b"red shoes", b"black bags", b"phone case"];
        let values = [42u32, 17, 8];
        let csf = CsfU32::new(&keys, &values).unwrap();
        let stats = csf.stats();
        assert_eq!(stats.in_memory_bytes, csf.size_bytes());
        assert!(stats.in_memory_bytes > 0);
        assert!(stats.solution_bytes > 0.0);
        assert_eq!(stats.num_buckets, 1);
        assert_eq!(stats.num_unique_symbols, 3);
        assert!(stats.avg_bits_per_symbol > 0.0);
    }
}
