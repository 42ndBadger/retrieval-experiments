#pragma once

#include <cstddef>
#include <cstdint>

// C ABI surface for the Rust bindings in src/caramel.rs. Field order below
// must match the `#[repr(C)] CsfStats` struct on the Rust side exactly.
extern "C" {

struct CaramelCsfStats {
  size_t in_memory_bytes;
  double solution_bytes;
  double filter_bytes;
  double metadata_bytes;
  size_t num_buckets;
  size_t total_solution_bits;
  size_t num_unique_symbols;
  double avg_bits_per_symbol;
};

void *caramel_csf_u32_build(const uint8_t *const *keys, const size_t *key_lens,
                            const uint32_t *values, size_t n, int verbose,
                            char *err, size_t err_cap);
uint32_t caramel_csf_u32_query(const void *handle, const uint8_t *key,
                               size_t key_len);
size_t caramel_csf_u32_size(const void *handle);
int caramel_csf_u32_stats(const void *handle, CaramelCsfStats *out);
void caramel_csf_u32_free(void *handle);

void *caramel_csf_u64_build(const uint8_t *const *keys, const size_t *key_lens,
                            const uint64_t *values, size_t n, int verbose,
                            char *err, size_t err_cap);
uint64_t caramel_csf_u64_query(const void *handle, const uint8_t *key,
                               size_t key_len);
size_t caramel_csf_u64_size(const void *handle);
int caramel_csf_u64_stats(const void *handle, CaramelCsfStats *out);
void caramel_csf_u64_free(void *handle);

} // extern "C"
