cmake_minimum_required(VERSION 3.20)
project(leetcode_lab LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

function(configure_problem_target target)
    if(MSVC)
        target_compile_options(${target} PRIVATE /W4)
    else()
        target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic)
    endif()
endfunction()

# Each problem has its own target, so multiple Solution classes never collide.
file(GLOB problem_entries CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/problems/*")
foreach(problem_dir IN LISTS problem_entries)
    if(NOT IS_DIRECTORY "${problem_dir}")
        continue()
    endif()
    get_filename_component(problem_name "${problem_dir}" NAME)
    if(NOT problem_name MATCHES "^[0-9]+-[a-z0-9-]+$")
        message(FATAL_ERROR "Use a problem folder such as 0001-two-sum: ${problem_name}")
    endif()
    set(target "problem_${problem_name}")
    if(EXISTS "${problem_dir}/cases.json")
        find_package(Python3 3.10 COMPONENTS Interpreter REQUIRED)
        add_custom_command(
            OUTPUT "${problem_dir}/cases.generated.hpp"
            COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tools/leetcode.py" driver "${problem_name}"
            DEPENDS "${problem_dir}/cases.json" "${problem_dir}/problem.json"
                    "${CMAKE_CURRENT_SOURCE_DIR}/tools/leetcode.py"
                    "${CMAKE_CURRENT_SOURCE_DIR}/tools/cpp_runner.py"
            VERBATIM
        )
        add_custom_target("generate_${target}" DEPENDS "${problem_dir}/cases.generated.hpp")
    endif()
    if(EXISTS "${problem_dir}/main.cpp")
        # main.cpp includes solution.cpp for local checks.
        add_executable(${target} "${problem_dir}/main.cpp")
    elseif(EXISTS "${problem_dir}/solution.cpp")
        # A LeetCode-only solution does not need a main() function.
        add_library(${target} OBJECT "${problem_dir}/solution.cpp")
    else()
        continue()
    endif()
    configure_problem_target(${target})
    if(TARGET "generate_${target}")
        add_dependencies(${target} "generate_${target}")
    endif()
endforeach()
