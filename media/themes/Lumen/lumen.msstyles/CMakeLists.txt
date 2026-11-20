file(GLOB_RECURSE lumen_rc_deps ${CMAKE_CURRENT_BINARY_DIR}/bitmaps/* ${CMAKE_CURRENT_BINARY_DIR}/lang/* ${CMAKE_CURRENT_BINARY_DIR}/textfiles/*)
add_rc_deps(lumen.rc ${lumen_rc_deps})

list(APPEND TEXTFILES
    textfiles/Light/ExtraLargeLight.INI
    textfiles/Light/LargeFontsLight.INI
    textfiles/Light/RegularLight.INI
    textfiles/Dark/ExtraLargeDark.INI
    textfiles/Dark/LargeFontsDark.INI
    textfiles/Dark/RegularDark.INI)

file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/textfiles)
foreach(_file ${TEXTFILES})
    get_filename_component(_file_name ${_file} NAME_WE)
    get_filename_component(_subdir ${_file} DIRECTORY)
    file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/${_subdir})
    set(_converted_file ${CMAKE_CURRENT_BINARY_DIR}/${_subdir}/${_file_name}_utf16.INI)
    utf16le_convert(${CMAKE_CURRENT_SOURCE_DIR}/${_file} ${_converted_file})
    list(APPEND _converted_files ${_converted_file})
endforeach()

set_source_files_properties(lumen.rc PROPERTIES OBJECT_DEPENDS "${_converted_files}")
add_library(lumen.msstyles MODULE lumen.rc)
set_module_type(lumen.msstyles module)
add_dependencies(lumen.msstyles xdk)
set_target_properties(lumen.msstyles PROPERTIES SUFFIX "")
add_cd_file(TARGET lumen.msstyles DESTINATION reactos/Resources/Themes/Lumen FOR all)
