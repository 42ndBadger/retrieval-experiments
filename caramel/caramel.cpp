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

void caramel_csf_u64_free(void *handle) { free_csf<uint64_t>(handle); }

} // extern "C"
