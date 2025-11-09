cmake_minimum_required(VERSION 3.10)
project(stats_verify_project C)

# enable verbose output (optional)
set(CMAKE_VERBOSE_MAKEFILE ON)

# source files
set(BASE_DIR ${CMAKE_CURRENT_SOURCE_DIR})

set(DEPS
    ${BASE_DIR}/utils.c
    ${BASE_DIR}/gpu-utilization/utils.c
    ${BASE_DIR}/powerdraw/utils.c
    ${BASE_DIR}/vram/utils.c
)

# main
add_executable(stats_verify
    stats_verify.c
    ${DEPS}
)

# get GSL via pkg-config
find_package(PkgConfig REQUIRED)
pkg_check_modules(GSL REQUIRED gsl)

# include links
target_include_directories(stats_verify PRIVATE ${GSL_INCLUDE_DIRS})
target_link_directories(stats_verify PRIVATE ${GSL_LIBRARY_DIRS})
target_link_libraries(stats_verify PRIVATE ${GSL_LIBRARIES})

# add compiler flags from pkg-config
target_compile_options(stats_verify PRIVATE ${GSL_CFLAGS_OTHER})

# more install rules
install(TARGETS stats_verify DESTINATION bin)