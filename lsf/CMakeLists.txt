cmake_minimum_required(VERSION 3.16)
project(lsf_ffi LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# We deliberately do NOT add_subdirectory(LearnedStaticFunction) and use its
# own top-level CMakeLists.txt: that unconditionally builds TensorFlow Lite
# from source (the `lib/tensorflow` submodule, multi-gigabyte, hours to
# build) as a hard link dependency of its `LearnedStaticFunction` target,
# even though we never use the TFLite-backed model. Instead we replicate
# just the pieces upstream's CMakeLists.txt builds for the non-ML parts of
# the pipeline: the BuRR-VLR ribbon retrieval structure (`lib/burr-vl`,
# itself a fork of https://github.com/lorenzhs/BuRR) and its `tlx`/`ips2ra`
# submodules, plus our own FFI shim. `lib/tensorflow` and `lib/psimd`
# (TFLite's SIMD polyfill) are left as uninitialized, empty submodules - see
# lsf/learned_static_function_no_tf.hpp for the corresponding header-level
# change (dropping the `model_wrapper.hpp`/TFLite include).
set(BURR_VL ${CMAKE_CURRENT_SOURCE_DIR}/LearnedStaticFunction/lib/burr-vl)

# Workaround for TLX breaking the first cmake call (same as upstream).
set(TLX_INSTALL_INCLUDE_DIR tlx CACHE PATH "Workaround for TLX breaking the first cmake call")
add_subdirectory(${BURR_VL}/tlx EXCLUDE_FROM_ALL)

# ips2ra's parallel mode requires TBB, which we don't need and may not have
# available; disable it (same as upstream).
set(IPS2RA_DISABLE_PARALLEL ON CACHE BOOL "FindTBB greps a file that does not exist in recent TBB versions" FORCE)
add_subdirectory(${BURR_VL}/ips2ra EXCLUDE_FROM_ALL)

add_library(lsf_shim STATIC
    lsf_shim.cpp
    ${BURR_VL}/sorter.cpp
)
target_compile_features(lsf_shim PRIVATE cxx_std_23)
target_include_directories(lsf_shim PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/LearnedStaticFunction/include/lsf
    ${BURR_VL}
    ${BURR_VL}/DySECT
    ${BURR_VL}/DySECT/module/xxhash
)
target_link_libraries(lsf_shim PRIVATE tlx ips2ra)

# tlx's own CMakeLists.txt (upstream) doesn't install its compiled archive,
# only headers/cmake package files, so install it here too.
install(TARGETS lsf_shim tlx ARCHIVE DESTINATION lib)
