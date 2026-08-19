#pragma once

#include <stddef.h>
#include <stdint.h>

// C ABI surface for the Rust bindings in src/lsf.rs.
//
// This wraps gvinciguerra/LearnedStaticFunction's `LearnedStaticFunction`
// instantiated with the (TFLite-free) `ModelFreq` model - see
// lsf/learned_static_function_no_tf.hpp for why, and lsf/lsf_shim.cpp for
// the instantiation. `ModelFreq` predicts the same global value-frequency
// distribution for every key (it ignores per-key features entirely), so it
// needs no trained model file and no per-key feature vectors - it is
// exactly the "no side information beyond the value distribution" baseline,
// which is what our synthetic key/value distributions (uniform, bernoulli,
// truncated-geometric) actually offer. Values must therefore be small,
// dense, non-negative class ids (fits our data_gen distributions, which are
// already bounded by construction); `classes_count` is the number of
// distinct value classes.

#ifdef __cplusplus
extern "C" {
#endif

void *lsf_u32_build(const uint8_t *const *keys, const size_t *key_lens,
                     const uint32_t *values, size_t n, uint32_t classes_count,
                     char *err, size_t err_cap);
// Not `const void *`: LearnedStaticFunction::query() mutates an internal
// XXH3 hash-state scratch buffer, so it isn't a const method upstream.
uint32_t lsf_u32_query(void *handle, const uint8_t *key, size_t key_len);
size_t lsf_u32_size(const void *handle);
void lsf_u32_free(void *handle);

#ifdef __cplusplus
}
#endif
