# CMakeLists.txt
# generated automatically, do not edit

cmake_minimum_required(VERSION 2.6)

project(ugens)

set(CODE_FILES ../framework/ugen.cpp ../framework/ugen.h
               osci.h osci.cpp
               decay.h decay.cpp
               add.h add.cpp
               mult.h mult.cpp
   )

include_directories(../framework)
add_library(ugens_static STATIC ${CODE_FILES})
