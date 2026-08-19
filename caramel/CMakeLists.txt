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

# install(TARGETS caramel_lib ARCHIVE DESTINATION lib)
