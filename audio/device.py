# Copyright (C) 2017 DataArt
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

import pyaudio


__all__ = ['AudioDevice']


class AudioDevice(object):
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.in_stream = self.pa.open(format=pyaudio.paInt16, channels=1,
                                      rate=16000, input=True)
        self.in_stream.start_stream()
        self.out_stream = self.pa.open(format=pyaudio.paInt16, channels=1,
                                       rate=16000, output=True)
        self.out_stream.start_stream()

    def close(self):
        self.in_stream.close()
        self.out_stream.close()
        self.pa.terminate()

    def write(self, b):
        return self.out_stream.write(b)

    def read(self, n):
        return self.in_stream.read(n)

    def flush(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()
