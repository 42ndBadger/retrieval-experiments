#include <cstdint>
#include <cstdio>
#include <exception>
#include <memory>
#include <span>
#include <stdexcept>
#include <string>
#include <vector>

// Upstream's own learned_static_function.hpp doesn't include ribbon.hpp
// itself - it relies on whatever includes it first (see
// ribbon_learned_bench.cpp, which does the same). ribbon.hpp also brings in
// xxhash.h (with XXH_INLINE_ALL, so it's header-only) which we reuse below
// to hash our string keys.
#include <ribbon.hpp>

#include "model_freq.hpp"
#include "learned_static_function_no_tf.hpp"

#include "lsf_shim.h"

namespace {

// See learned_static_function_no_tf.hpp: keys are looked up by an explicit
// uint64_t `get_key(i)` rather than the row index, so we can hand it a hash
// of the original string key computed up front. `ModelFreq::invoke()`
// ignores its `example` argument entirely, so `get_example` can return an
// empty feature span.
class Dataset {
    const std::vector<uint64_t> &key_hashes_;
    const std::vector<uint16_t> &labels_;
    uint32_t classes_count_;

public:
    Dataset(const std::vector<uint64_t> &key_hashes, const std::vector<uint16_t> &labels,
            uint32_t classes_count)
        : key_hashes_(key_hashes), labels_(labels), classes_count_(classes_count) {}

    size_t size() const { return labels_.size(); }
    size_t classes_count() const { return classes_count_; }
    std::span<const float> get_example(size_t) const { return {}; }
    uint16_t get_label(size_t i) const { return labels_[i]; }
    uint64_t get_key(size_t i) const { return key_hashes_[i]; }
};

using Coding = lsf::BitWiseFilterCoding<lsf::FilterHuffmanCoderCSF>;
using Storage = lsf::FilteredLSFStorage<Coding>;
using Lsf = lsf::LearnedStaticFunction<Dataset, lsf::ModelFreq, Storage>;

struct LsfHandle {
    // Declaration order matters: `dataset`, `model` and `lsf` below hold
    // references/point into `key_hashes`/`labels`, and `lsf` holds a
    // reference to `model` - members are constructed in declaration order,
    // so those must come first, and this struct must never be moved/copied
    // (we only ever hand out a heap pointer to it, matching CsfU32/CsfU64
    // in caramel.rs).
    std::vector<uint64_t> key_hashes;
    std::vector<uint16_t> labels;
    uint32_t classes_count;
    Dataset dataset;
    lsf::ModelFreq model;
    Lsf lsf;

    LsfHandle(std::vector<uint64_t> key_hashes_in, std::vector<uint16_t> labels_in,
              uint32_t classes_count_in)
        : key_hashes(std::move(key_hashes_in)),
          labels(std::move(labels_in)),
          classes_count(classes_count_in),
          dataset(key_hashes, labels, classes_count),
          model(labels, classes_count),
          lsf(dataset, model) {}
};

} // namespace

extern "C" {

void *lsf_u32_build(const uint8_t *const *keys, const size_t *key_lens,
                     const uint32_t *values, size_t n, uint32_t classes_count,
                     char *err, size_t err_cap) {
    try {
        if (n == 0) {
            throw std::runtime_error("cannot build an empty LSF");
        }
        if (classes_count == 0) {
            throw std::runtime_error("classes_count must be > 0");
        }
        if (classes_count > 65535) {
            // lsf::ModelFreq/FilterHuffmanCoderCSF index labels as uint16_t.
            throw std::runtime_error(
                "classes_count exceeds 65535 (LSF value labels are uint16_t)");
        }

        std::vector<uint64_t> key_hashes(n);
        std::vector<uint16_t> labels(n);
        for (size_t i = 0; i < n; ++i) {
            key_hashes[i] = XXH3_64bits(keys[i], key_lens[i]);
            if (values[i] >= classes_count) {
                throw std::runtime_error("value out of range for classes_count");
            }
            labels[i] = static_cast<uint16_t>(values[i]);
        }

        auto handle = std::make_unique<LsfHandle>(std::move(key_hashes), std::move(labels),
                                                   classes_count);
        return handle.release();
    } catch (const std::exception &e) {
        if (err && err_cap > 0) {
            std::snprintf(err, err_cap, "%s", e.what());
        }
        return nullptr;
    } catch (...) {
        if (err && err_cap > 0) {
            std::snprintf(err, err_cap, "unknown error");
        }
        return nullptr;
    }
}

uint32_t lsf_u32_query(void *handle, const uint8_t *key, size_t key_len) {
    auto *h = static_cast<LsfHandle *>(handle);
    uint64_t key_hash = XXH3_64bits(key, key_len);
    return static_cast<uint32_t>(h->lsf.query(key_hash, std::span<const float>{}));
}

size_t lsf_u32_size(const void *handle) {
    const auto *h = static_cast<const LsfHandle *>(handle);
    return h->lsf.size_in_bytes();
}

void lsf_u32_free(void *handle) { delete static_cast<LsfHandle *>(handle); }

} // extern "C"
