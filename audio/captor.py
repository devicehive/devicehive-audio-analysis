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

import threading
import logging.config

from .device import AudioDevice


__all__ = ['Captor']

logger = logging.getLogger('audio_analysis.captor')


class Captor(object):
    """
    Non-blocking class to capture data from mic
    It waiting till "ask_data_event" is set and then call "callback" as soon as
    data ready
    """
    _sample_rate = 16000
    _capture_rate = _sample_rate*2  # bytes per second
    _ask_data_event = None
    _shutdown_event = None
    _capture_thread = None

    def __init__(self, min_time, max_time, ask_data_event, callback,
                 shutdown_event=None):
        """
        Init capture class
        :param min_time: Minimum capture time to process (seconds)
        :param max_time: Maximum capture time to process (seconds)
        :param ask_data_event: Event to wait data call
        :param callback: Callable that will called with data
        :param shutdown_event: Event to shutdown
        """

        if min_time > max_time:
            raise ValueError('"min_time" is grater than "max_time"')

        if not callable(callback):
            raise TypeError('"callback" is not callable')

        if shutdown_event is None:
            shutdown_event = threading.Event()

        self._min_time = min_time
        self._max_time = max_time
        self._ask_data_event = ask_data_event
        self._shutdown_event = shutdown_event
        self._callback = callback

        self._min_data = self._min_time*self._capture_rate
        self._max_data = self._max_time*self._capture_rate

        self._capture_thread = threading.Thread(target=self._capture,
                                                name='captor')
        self._capture_thread.setDaemon(True)

    def start(self):
        """
        Start capture loop
        :return:
        """
        self._capture_thread.start()

    def _capture(self):
        """
        Capture loop
        :return:
        """
        ad = AudioDevice()
        capture_buf = bytes()

        logger.info('Start recording.')
        while not self._shutdown_event.is_set():
            if self._ask_data_event.is_set() \
                    and len(capture_buf) >= self._min_data:
                self._callback(capture_buf)
                capture_buf = bytes()

            buf = ad.read(self._sample_rate)
            if buf is None:
                logger.debug('Buffer is empty.')
                return
            capture_buf += buf

            overflow = len(capture_buf) - self._max_data
            if overflow > 0:
                logger.info('Buffer overflow, truncate {}b.'.format(overflow))
                capture_buf = capture_buf[overflow:]
