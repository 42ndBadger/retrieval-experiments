use std::ffi::{CStr, c_char, c_void};
use std::fmt;

unsafe extern "C" {
    fn lsf_u32_build(
        keys: *const *const u8,
        key_lens: *const usize,
        values: *const u32,
        n: usize,
        classes_count: u32,
        err: *mut c_char,
        err_cap: usize,
    ) -> *mut c_void;
    fn lsf_u32_query(handle: *mut c_void, key: *const u8, key_len: usize) -> u32;
    fn lsf_u32_size(handle: *const c_void) -> usize;
    fn lsf_u32_free(handle: *mut c_void);
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LsfError(String);

impl LsfError {
    fn new(msg: String) -> Self {
        Self(msg)
    }
}

impl fmt::Display for LsfError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl std::error::Error for LsfError {}

/// A learned static function (gvinciguerra/LearnedStaticFunction) mapping
/// byte-string keys to u32 values, backed by a frequency-table model
/// (`lsf::ModelFreq` - no ML/TFLite involved, see lsf/lsf_shim.cpp) and a
/// BuRR-VLR ribbon retrieval structure. Values must be small, dense
/// non-negative class ids: `classes_count` (one more than the largest value
/// present) becomes the model's output alphabet size, and construction
/// fails if it exceeds 65535 (LSF labels are stored as `uint16_t`).
pub struct LsfU32 {
    ptr: *mut c_void,
}

impl LsfU32 {
    pub fn new(keys: &[&[u8]], values: &[u32]) -> Result<Self, LsfError> {
        if keys.len() != values.len() {
            return Err(LsfError::new(format!(
                "key count {} does not match value count {}",
                keys.len(),
                values.len()
            )));
        }
        if keys.is_empty() {
            return Err(LsfError::new("cannot build an empty LSF".to_string()));
        }

        let classes_count = values.iter().copied().max().unwrap() + 1;

        let key_ptrs: Vec<*const u8> = keys.iter().map(|k| k.as_ptr()).collect();
        let key_lens: Vec<usize> = keys.iter().map(|k| k.len()).collect();

        let mut err_buf = [0u8; 512];
        let ptr = unsafe {
            lsf_u32_build(
                key_ptrs.as_ptr(),
                key_lens.as_ptr(),
                values.as_ptr(),
                keys.len(),
                classes_count,
                err_buf.as_mut_ptr().cast::<c_char>(),
                err_buf.len(),
            )
        };
        if ptr.is_null() {
            let msg = unsafe { CStr::from_ptr(err_buf.as_ptr().cast::<c_char>()) }
                .to_string_lossy()
                .into_owned();
            return Err(LsfError::new(msg));
        }
        Ok(LsfU32 { ptr })
    }

    #[inline]
    pub fn query(&self, key: &[u8]) -> u32 {
        unsafe { lsf_u32_query(self.ptr, key.as_ptr(), key.len()) }
    }

    #[inline]
    pub fn size_bytes(&self) -> usize {
        unsafe { lsf_u32_size(self.ptr) }
    }
}

impl Drop for LsfU32 {
    fn drop(&mut self) {
        unsafe { lsf_u32_free(self.ptr) };
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn build_and_query() {
        let keys: Vec<&[u8]> = vec![b"red shoes", b"black bags", b"phone case"];
        let values = [2u32, 1, 0];
        let lsf = LsfU32::new(&keys, &values).unwrap();
        assert_eq!(lsf.query(b"red shoes"), 2);
        assert_eq!(lsf.query(b"black bags"), 1);
        assert_eq!(lsf.query(b"phone case"), 0);
        assert!(lsf.size_bytes() > 0);
    }

    #[test]
    fn rejects_mismatched_lengths() {
        let keys: Vec<&[u8]> = vec![b"a"];
        let values = [1u32, 2];
        assert!(LsfU32::new(&keys, &values).is_err());
    }

    #[test]
    fn single_class() {
        let keys: Vec<&[u8]> = vec![b"a", b"b", b"c"];
        let values = [0u32, 0, 0];
        let lsf = LsfU32::new(&keys, &values).unwrap();
        assert_eq!(lsf.query(b"a"), 0);
        assert_eq!(lsf.query(b"b"), 0);
        assert_eq!(lsf.query(b"c"), 0);
    }
}
