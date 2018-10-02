# cmake.py - build cmake file for ugen library
#
# Roger B. Dannenberg
# Jun 2018


source_path = None
source_files = []

def set_source_path(path):
    global source_path
    source_path = path


def add_source_files(*filenames):
    global source_files
    for f in filenames:
        source_files.append(f)

def write_cmake_file():
    cmf = open(source_path + "CMakeLists.txt", "w")
    print("# CMakeLists.txt\n# generated automatically, do not edit", \
          file=cmf)
    print("\ncmake_minimum_required(VERSION 2.6)\n", file=cmf)
    print("project(ugens)\n\nset(CODE_FILES ../framework/ugen.cpp", \
          "../framework/ugen.h", file=cmf)
    for i in range(0, len(source_files), 2):
        print("              ", source_files[i], source_files[i + 1], \
              file=cmf)
    print("   )\n\ninclude_directories(../framework)", file=cmf)
    print("add_library(ugens_static STATIC ${CODE_FILES})", file=cmf)
