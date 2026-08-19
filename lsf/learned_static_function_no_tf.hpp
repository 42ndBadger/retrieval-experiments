#pragma once

// Vendored copy of upstream LearnedStaticFunction's
// include/lsf/learned_static_function.hpp (gvinciguerra/LearnedStaticFunction,
// commit-pinned via the lsf/LearnedStaticFunction submodule).
//
// Two changes from the upstream file:
//
// 1. Dropped the `#include "model_wrapper.hpp"` line. That header pulls in
//    TensorFlow Lite (`<tensorflow/lite/...>`), which requires the
//    (multi-gigabyte, hours-to-build) `lib/tensorflow` submodule that
//    upstream's own CMakeLists.txt builds unconditionally. We never
//    instantiate `LearnedStaticFunction` with the TFLite-backed
//    `ModelWrapper` model - we only use `lsf::ModelFreq` (see
//    lsf/lsf_shim.cpp), a plain frequency-table model with no ML backend -
//    so the include (and the TF/psimd submodules entirely) can be dropped
//    without losing anything we use. See lsf/CMakeLists.txt for the rest of
//    what's excluded.
//
// 2. The constructor originally hashes the dataset row *index* `i` as the
//    item's key (upstream's benchmark harness only ever queries by row
//    index into a fixed, ordered dataset - there's no separate key
//    concept). We instead ask the dataset for an explicit `get_key(i)`
//    and hash that, so `LearnedStaticFunction::query()` can be called with
//    an arbitrary caller-chosen uint64_t (in our case, a hash of the
//    original string key) rather than the row's position. `query()` itself
//    was already generic over its `key` argument - only the constructor
//    needed this change.
//
// 3. Dropped the upstream `std::cout <<` debug prints inside `build()` and
//    the `LearnedStaticFunction` constructor (construction stats, timings).
//    They ran on every single construction, which both spams stdout across
//    a benchmark sweep and adds unmeasured I/O into the very construction
//    time our benchmark harness (src/benchmark.rs) is trying to measure.
//
// Keep this in sync with upstream's learned_static_function.hpp if the
// submodule is ever updated.

#include "filter_coding.hpp"
#include "dataset_reader.hpp"

namespace lsf {


    constexpr size_t recDepth = 2;
    constexpr float slotsPerItem = 0.96;
    struct BuRRConfig
            : public ribbon::RConfig<128, 1, ribbon::ThreshMode::twobit, false, true, false, 0, uint64_t> {
        static constexpr bool kUseVLR = true;
        static constexpr Index kBucketSize = 128;
    };


    template<typename Coding>
    class FilteredLSFStorage {
        ribbon::ribbon_filter<recDepth, BuRRConfig> correctionVLSF;
        ribbon::ribbon_filter<recDepth, BuRRConfig> filterVLSF;
        Coding coder;

        size_t statistic_bits_input;
    public:

        FilteredLSFStorage() {}

        template<typename F>
        void build(size_t n, size_t classes_count, F get) {
            statistic_bits_input = 0;
            using namespace ribbon;
            IMPORT_RIBBON_CONFIG(BuRRConfig);

            auto [hashCSF, labelCSF, probabilitiesCSF] = get(0);
            // probabilitiesCSF are the relative frequencies when used as a CSF
            coder = Coding(classes_count, probabilitiesCSF);
            size_t maxlenfilter = 0;
            auto inputFilter = std::make_unique<std::pair<Key, ResultRowVLR>[]>(n);
            for (size_t i = 0; i < n; ++i) {
                auto [hash, label, probabilities] = get(i);
                auto [code, filterLength, bitsSet] = coder.encode_once_filter(probabilities, label);
                statistic_bits_input += bitsSet;
                inputFilter[i].first = hash;
                if (filterLength > maxlenfilter)
                    maxlenfilter = filterLength;
                inputFilter[i].second = static_cast<uint64_t>(code) | (uint64_t(1) << filterLength);
            }

            filterVLSF = ribbon_filter<recDepth, BuRRConfig>(slotsPerItem, 42, maxlenfilter);
            filterVLSF.AddRange(inputFilter.get(), inputFilter.get() + n, true);
            filterVLSF.BackSubst();

            size_t maxlen = 0;
            auto input = std::make_unique<std::pair<Key, ResultRowVLR>[]>(n);
            for (size_t i = 0; i < n; ++i) {
                auto [hash, label, probabilities] = get(i);
                uint64_t filterVal = filterVLSF.QueryRetrieval(hash);
                auto [code, length] = coder.encode_once_corrected_code(probabilities, label, filterVal);
                statistic_bits_input += length;
                input[i].first = hash;
                if (length > maxlen)
                    maxlen = length;
                input[i].second = static_cast<uint64_t>(code) | (uint64_t(1) << length);
            }

            correctionVLSF = ribbon_filter<recDepth, BuRRConfig>(slotsPerItem, 42, maxlen);
            correctionVLSF.AddRange(input.get(), input.get() + n);
            correctionVLSF.BackSubst();
            input.reset();
        }

        std::pair<uint64_t, uint64_t> query_storage(uint64_t hash) {
            uint64_t corrected_code = correctionVLSF.QueryRetrieval(hash);
            uint64_t filterCode = filterVLSF.QueryRetrieval(hash);
            return {corrected_code, filterCode};
        }

        uint64_t query(uint64_t hash, std::span<float> probabilities) {
            auto [corrected_code, filterCode] = query_storage(hash);
            return coder.decode_once(probabilities, corrected_code, filterCode);
        }

        size_t size_in_bytes() const {
            return filterVLSF.Size() + correctionVLSF.Size();
        }

        size_t get_statistic_bits_input() const {
            return statistic_bits_input;
        }

        static const std::string get_name() {
            return "Filtered-" + Coding::get_name();
        }
    };

    template<typename DataSet, typename Model, typename Storage>
    class LearnedStaticFunction {
        XXH3_state_t *state;
        Model &model;
        Storage storage;

    public:

        LearnedStaticFunction(const DataSet &dataset, Model &model) : model(model) {
            state = XXH3_createState();
            assert(state);
            storage = Storage();
            storage.build(
                    dataset.size(),
                    dataset.classes_count(),
                    [&](size_t i) {
                        auto example = dataset.get_example(i);
                        return std::make_tuple(hash(dataset.get_key(i), example), dataset.get_label(i), model.invoke(example));
                    });
        }

        std::span<float> query_probabilities(std::span<const float> features) {
            return model.invoke(features);
        }

        auto query_storage(uint64_t key, std::span<const float> features) {
            return storage.query_storage(hash(key, features));
        }

        uint64_t query(uint64_t key, std::span<const float> features) {
            return storage.query(hash(key, features), query_probabilities(features));
        }

        size_t model_bytes() const { return model.model_bytes(); }

        size_t storage_bytes() const { return storage.size_in_bytes(); }

        size_t size_in_bytes() const { return storage.size_in_bytes() + model.model_bytes(); }

        size_t get_statistic_bits_input() const { return storage.get_statistic_bits_input(); }

    private:

        uint64_t hash(uint64_t key, std::span<const float> features) {
            XXH3_64bits_reset(state);
            XXH3_64bits_update(state, &key, sizeof(size_t));
            //XXH3_64bits_update(state, features.data(), features.size_bytes());
            return XXH3_64bits_digest(state);
        }
    };
}
