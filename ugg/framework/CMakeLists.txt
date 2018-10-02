# CMakeLists.txt

cmake_minimum_required(VERSION 2.6)

project(uggtest)

set(UGG_FILES ugen.cpp ugen.h)

add_subdirectory(../code code)

if(UNIX)
  if(APPLE)
    include_directories(${CMAKE_OSX_SYSROOT}/Developer/Headers/FlatCarbon
                        src/sys/mac)
    set(FRAMEWORK_PATH ${CMAKE_OSX_SYSROOT}/System/Library/Frameworks
        CACHE INTERNAL " " FORCE)
    set(COREAUDIO_LIB "${FRAMEWORK_PATH}/CoreAudio.framework")
    set(COREFOUNDATION_LIB "${FRAMEWORK_PATH}/CoreFoundation.framework")
    set(CORESERVICES_LIB "${FRAMEWORK_PATH}/CoreServices.framework")
    set(AUDIOTOOLBOX_LIB "${FRAMEWORK_PATH}/AudioToolbox.framework")
    set(AUDIOUNIT_LIB "${FRAMEWORK_PATH}/AudioUnit.framework")
    set(EXTRA_PA_LIBS ${COREAUDIO_LIB} ${COREFOUNDATION_LIB}
                       ${CORESERVICES_LIB}
                       ${AUDIOTOOLBOX_LIB} ${AUDIOUNIT_LIB})
    add_definitions("-DPA_USE_COREAUDIO")
    add_definitions("-DCMTSTUFF")
    add_definitions("-Dmacintosh")
  else(APPLE)
    # Linux
    set(EXTRA_PA_LIBS asound pthread m)
  endif(APPLE)
endif(UNIX)

include_directories(../code
                    ../../../../nyquist/portaudio/include)
link_directories("${PROJECT_SOURCE_DIR}/code")
add_executable(uggtest uggtest.cpp ${UGG_FILES})
target_link_libraries(uggtest
        ugens_static
        /Users/rbd/nyquist/Release/libportaudio_static.a
        ${EXTRA_PA_LIBS})

