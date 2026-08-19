cmake_minimum_required(VERSION 3.5)
project(caramel_ffi LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
add_subdirectory(CaramelDB EXCLUDE_FROM_ALL)

set_target_properties(caramel_lib PROPERTIES EXCLUDE_FROM_ALL FALSE)
target_sources(caramel_lib PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/caramel.cpp)

# CaramelDB's own CMakeLists.txt unconditionally links OpenMP into
# caramel_lib, which parallelizes construction across all cores by default
# (src/construct/Construct.h's `#pragma omp parallel for`, no num_threads
# clause). Consensus (pure Rust) and LSF (ips2ra's parallel mode disabled,
# see lsf/CMakeLists.txt) are both single-threaded, so left as-is,
# construction-time comparisons would partly measure "used N cores" rather
# than a purely algorithmic difference.
#
# Rather than patching CaramelDB's own CMakeLists.txt/C++ source, or
# relying on the OMP_NUM_THREADS env var at run time, strip the OpenMP
# link dependency from caramel_lib here so it's compiled without
# -fopenmp in the first place: unrecognized by the compiler at that point,
# `#pragma omp` directives are simply ignored and the loops run
# sequentially - no libgomp involved, and no runtime flag needed either.
get_target_property(CARAMEL_LIB_LINK_LIBRARIES caramel_lib LINK_LIBRARIES)
if(CARAMEL_LIB_LINK_LIBRARIES)
    list(REMOVE_ITEM CARAMEL_LIB_LINK_LIBRARIES OpenMP::OpenMP_CXX)
    set_target_properties(caramel_lib PROPERTIES LINK_LIBRARIES "${CARAMEL_LIB_LINK_LIBRARIES}")
endif()

# CaramelDB's own CARAMEL_COMPILE_OPTIONS already adds -ffast-math for
# Release builds; add -march=native too, so Caramel gets the same
# optimization level as LSF (see lsf/CMakeLists.txt) and the Rust side
# (see .cargo/config.toml) for a fair three-way comparison. Ties the
# resulting binary to this machine's CPU.
target_compile_options(caramel_lib PRIVATE -march=native)

install(TARGETS caramel_lib ARCHIVE DESTINATION lib)
