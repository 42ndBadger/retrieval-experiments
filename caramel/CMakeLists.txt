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

# CaramelDB's own CARAMEL_COMPILE_OPTIONS already adds -ffast-math for
# Release builds; add -march=native too, so Caramel gets the same
# optimization level as LSF (see lsf/CMakeLists.txt) and the Rust side
# (see .cargo/config.toml) for a fair three-way comparison. Ties the
# resulting binary to this machine's CPU.
target_compile_options(caramel_lib PRIVATE -march=native)

install(TARGETS caramel_lib ARCHIVE DESTINATION lib)
