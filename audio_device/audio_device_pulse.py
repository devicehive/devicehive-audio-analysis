# Copyright (C) 2016 DataArt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import atexit
import ctypes
import logging


class _struct_pa_sample_spec(ctypes.Structure):
    _fields_ = [('format', ctypes.c_int),
                ('rate', ctypes.c_uint32),
                ('channels', ctypes.c_uint8)]


_PA_STREAM_PLAYBACK = 1
_PA_STREAM_RECORD = 2
_PA_SAMPLE_S16LE = 3


def init():
    global pa, in_stream, out_stream, error
    error = ctypes.c_int(0)
    pa = ctypes.cdll.LoadLibrary('libpulse-simple.so.0')
    pa.strerror.restype = ctypes.c_char_p
    ss = _struct_pa_sample_spec(_PA_SAMPLE_S16LE, 16000, 1)

    out_stream = ctypes.c_void_p(pa.pa_simple_new(
        None, 'Alexa'.encode('ascii'), _PA_STREAM_PLAYBACK, None,
        'Alexa voice'.encode('ascii'), ctypes.byref(ss), None, None,
        ctypes.byref(error)
    ))
    if not out_stream:
        raise IOError('Could not create pulse audio output stream: %s' % str(
            pa.strerror(error), 'ascii'))

    in_stream = ctypes.c_void_p(pa.pa_simple_new(
        None, 'Alexa'.encode('ascii'), _PA_STREAM_RECORD, None,
        'Alexa mic'.encode('ascii'), ctypes.byref(ss), None, None,
        ctypes.byref(error)
    ))
    if not in_stream:
        raise IOError('Could not create pulse audio input stream: %s' % str(
            pa.strerror(error), 'ascii'))

    logging.info('PulseAudio is initialized.')


def deinit():
    pa.pa_simple_free(in_stream)
    pa.pa_simple_free(out_stream)


class AudioDevice(object):
    def __init__(self):
        pa.pa_simple_flush(in_stream)
        pa.pa_simple_flush(out_stream)

    def close(self):
        pa.pa_simple_flush(in_stream)
        pa.pa_simple_flush(out_stream)

    def write(self, b):
        return pa.pa_simple_write(out_stream, b, len(b), ctypes.byref(error))

    def flush(self):
        pa.pa_simple_flush(out_stream)

    def read(self, n):
        data = ctypes.create_string_buffer(n)
        pa.pa_simple_read(in_stream, data, n, ctypes.byref(error))
        return data.raw


init()
atexit.register(deinit)
