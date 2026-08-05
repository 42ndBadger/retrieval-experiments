// #include <cstddef>
#include <cstdint>
#include <cstdio>
#include <exception>
#include <memory>
#include <string>
#include <vector>

#include <src/construct/Construct.h>
#include <src/construct/Csf.h>

#include "caramel.h"

namespace {

template <typename T> struct CsfHandle {
  caramel::CsfPtr<T> csf;
};

template <typename T>
int build_csf(const uint8_t *const *keys, const size_t *key_lens,
              const T *values, size_t n, int verbose, void **out, char *err,
              size_t err_cap) {
  try {
    std::vector<std::string> cpp_keys;
    cpp_keys.reserve(n);
    for (size_t i = 0; i < n; i++) {
      cpp_keys.emplace_back(reinterpret_cast<const char *>(keys[i]),
                            key_lens[i]);
    }
    std::vector<T> cpp_values(values, values + n);
    auto csf =
        caramel::constructCsf<T>(cpp_keys, cpp_values, nullptr, verbose != 0);
    *out = new CsfHandle<T>{std::move(csf)};
    return 0;
  } catch (const std::exception &e) {
    if (err && err_cap > 0) {
      std::snprintf(err, err_cap, "%s", e.what());
    }
    return -1;
  } catch (...) {
    if (err && err_cap > 0) {
      std::snprintf(err, err_cap, "unknown error");
    }
    return -1;
  }
}

template <typename T> void free_csf(void *handle) {
  delete static_cast<CsfHandle<T> *>(handle);
}

template <typename T>
T query_csf(const void *handle, const uint8_t *key, size_t key_len) {
  const auto *h = static_cast<const CsfHandle<T> *>(handle);
  return h->csf->query(reinterpret_cast<const char *>(key), key_len);
}

template <typename T> size_t size_csf(const void *handle) {
  const auto *h = static_cast<const CsfHandle<T> *>(handle);
  return h->csf->getStats().in_memory_bytes;
}

template <typename T>
int stats_csf(const void *handle, CaramelCsfStats *out) {
  try {
    const auto *h = static_cast<const CsfHandle<T> *>(handle);
    auto stats = h->csf->getStats();
    out->in_memory_bytes = stats.in_memory_bytes;
    out->solution_bytes = stats.solution_bytes;
    out->filter_bytes = stats.filter_bytes;
    out->metadata_bytes = stats.metadata_bytes;
    out->num_buckets = stats.bucket_stats.num_buckets;
    out->total_solution_bits = stats.bucket_stats.total_solution_bits;
    out->num_unique_symbols = stats.huffman_stats.num_unique_symbols;
    out->avg_bits_per_symbol = stats.huffman_stats.avg_bits_per_symbol;
    return 0;
  } catch (...) {
    return -1;
  }
}

} // namespace

extern "C" {

void *caramel_csf_u32_build(const uint8_t *const *keys, const size_t *key_lens,
                            const uint32_t *values, size_t n, int verbose,
                            char *err, size_t err_cap) {
  void *out = nullptr;
  if (build_csf<uint32_t>(keys, key_lens, values, n, verbose, &out, err,
                          err_cap) != 0) {
    return nullptr;
  }
  return out;
}

uint32_t caramel_csf_u32_query(const void *handle, const uint8_t *key,
                               size_t key_len) {
  return query_csf<uint32_t>(handle, key, key_len);
}

size_t caramel_csf_u32_size(const void *handle) {
  return size_csf<uint32_t>(handle);
}

int caramel_csf_u32_stats(const void *handle, CaramelCsfStats *out) {
  return stats_csf<uint32_t>(handle, out);
}

void caramel_csf_u32_free(void *handle) { free_csf<uint32_t>(handle); }

void *caramel_csf_u64_build(const uint8_t *const *keys, const size_t *key_lens,
                            const uint64_t *values, size_t n, int verbose,
                            char *err, size_t err_cap) {
  void *out = nullptr;
  if (build_csf<uint64_t>(keys, key_lens, values, n, verbose, &out, err,
                          err_cap) != 0) {
    return nullptr;
  }
  return out;
}

uint64_t caramel_csf_u64_query(const void *handle, const uint8_t *key,
                               size_t key_len) {
  return query_csf<uint64_t>(handle, key, key_len);
}

size_t caramel_csf_u64_size(const void *handle) {
  return size_csf<uint64_t>(handle);
}

int caramel_csf_u64_stats(const void *handle, CaramelCsfStats *out) {
  return stats_csf<uint64_t>(handle, out);
}

void caramel_csf_u64_free(void *handle) { free_csf<uint64_t>(handle); }

} // extern "C"
