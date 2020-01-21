# The following lines of boilerplate have to be in your project's
# CMakeLists in this exact order for cmake to work correctly
cmake_minimum_required(VERSION 3.5)

set(EXTRA_COMPONENT_DIRS ../esp-idf-lib/components)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(bme280-mqtt)

# target_add_binary_data(bme280-mqtt.elf "main/server.crt" TEXT)