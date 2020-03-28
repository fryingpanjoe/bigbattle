#
# Copyright Tristam Macdonald 2008.
#
# Distributed under the Boost Software License, Version 1.0
# (see http://www.boost.org/LICENSE_1_0.txt)
#

from pyglet.gl import *
from ctypes import create_string_buffer, cast, pointer, POINTER, c_char, c_int, byref


def compile_shader(shader_type, shader_source):
    shader_name = glCreateShader(shader_type)
    src_buffer = create_string_buffer(shader_source.encode('utf-8'))
    buf_pointer = cast(pointer(pointer(src_buffer)), POINTER(POINTER(c_char)))
    length = c_int(len(shader_source) + 1)
    glShaderSource(shader_name, 1, buf_pointer, byref(length))
    glCompileShader(shader_name)

    compile_status = c_int(0)
    glGetShaderiv(shader_name, GL_COMPILE_STATUS, byref(compile_status))

    if not compile_status:
        info_log_length = c_int(0)
        glGetShaderiv(shader_name, GL_INFO_LOG_LENGTH, byref(info_log_length))

        compilation_log = create_string_buffer(info_log_length.value)
        glGetShaderInfoLog(shader_name, info_log_length, None, compilation_log)

        print(compilation_log.value)
        raise RuntimeError('shader compilation error: ' + compilation_log.value)

    return shader_name


class Shader(object):
    def __init__(self, vertex_shader_source = '', fragment_shader_source = ''):
        self.handle = glCreateProgram()

        glAttachShader(self.handle, compile_shader(GL_VERTEX_SHADER, vertex_shader_source))
        glAttachShader(self.handle, compile_shader(GL_FRAGMENT_SHADER, fragment_shader_source))

        glLinkProgram(self.handle)

        link_status = c_int(0)
        glGetProgramiv(self.handle, GL_LINK_STATUS, byref(link_status))

        if not link_status:
            info_log_length = c_int(0)
            glGetProgramiv(self.handle, GL_INFO_LOG_LENGTH, byref(info_log_length))

            link_log = create_string_buffer(info_log_length.value)
            glGetProgramInfoLog(self.handle, info_log_length, None, link_log)

            print(link_log.value)
            raise RuntimeError('shader link error: ' + link_log.value)

    def bind(self):
        glUseProgram(self.handle)

    def unbind(self):
        glUseProgram(0)

    # upload a floating point uniform
    # this program must be currently bound
    def uniformf(self, name, *vals):
        # check there are 1-4 values
        if len(vals) in range(1, 5):
            # select the correct function
            { 1 : glUniform1f,
                2 : glUniform2f,
                3 : glUniform3f,
                4 : glUniform4f
                # retrieve the uniform location, and set
            }[len(vals)](glGetUniformLocation(self.handle, name), *vals)

    # upload an integer uniform
    # this program must be currently bound
    def uniformi(self, name, *vals):
        # check there are 1-4 values
        if len(vals) in range(1, 5):
            # select the correct function
            { 1 : glUniform1i,
                2 : glUniform2i,
                3 : glUniform3i,
                4 : glUniform4i
                # retrieve the uniform location, and set
            }[len(vals)](glGetUniformLocation(self.handle, name), *vals)

    # upload a uniform matrix
    # works with matrices stored as lists,
    # as well as euclid matrices
    def uniform_matrixf(self, name, mat):
        # obtian the uniform location
        loc = glGetUniformLocation(self.Handle, name)
        # uplaod the 4x4 floating point matrix
        glUniformMatrix4fv(loc, 1, False, (c_float * 16)(*mat))
