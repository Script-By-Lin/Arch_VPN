cmake_minimum_required(VERSION 3.18.1)
project(tunexec C)

add_library(tunexec SHARED tunexec.c)
target_compile_options(tunexec PRIVATE -O2 -Wall -Wextra)
