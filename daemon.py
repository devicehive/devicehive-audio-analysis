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

import os
import time
import json
import threading
import logging.config
import datetime
import numpy as np
from collections import deque
from scipy.io import wavfile
from dh_webconfig import Server, Handler

from audio.captor import Captor
from audio.processor import WavProcessor, format_predictions
from web.routes import routes

from log_config import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('audio_analysis.daemon')


class DeviceHiveHandler(Handler):
    _device = None

    def handle_connect(self):
        self._device = self.api.put_device(self._device_id)
        super(DeviceHiveHandler, self).handle_connect()

    def send(self, data):
        if isinstance(data, str):
            notification = data
        else:
            try:
                notification = json.dumps(data)
            except TypeError:
                notification = str(data)

        self._device.send_notification(notification)


class Daemon(Server):
    _process_thread = None
    _process_buf = None
    _ask_data_event = None
    _shutdown_event = None
    _captor = None
    _sample_rate = 16000
    _processor_sleep_time = 0.01

    events_queue = None

    def __init__(self, *args, **kwargs):
        min_time = kwargs.pop('min_capture_time', 5)
        max_time = kwargs.pop('max_capture_time', 5)
        self._save_path = kwargs.pop('save_path', None)

        super(Daemon, self).__init__(*args, **kwargs)

        self.events_queue = deque(maxlen=10)
        self._ask_data_event = threading.Event()
        self._shutdown_event = threading.Event()
        self._process_thread = threading.Thread(target=self._process_loop,
                                                name='processor')
        self._process_thread.setDaemon(True)

        self._captor = Captor(min_time, max_time, self._ask_data_event,
                              self._process, self._shutdown_event)

    def _start_capture(self):
        logger.info('Start captor')
        self._captor.start()

    def _start_process(self):
        logger.info('Start processor loop')
        self._process_thread.start()

    def _process(self, data):
        self._process_buf = np.frombuffer(data, dtype=np.int16)

    def _on_startup(self):
        self._start_process()
        self._start_capture()

    def _on_shutdown(self):
        self._shutdown_event.set()

    def _process_loop(self):
        with WavProcessor() as proc:
            self._ask_data_event.set()
            while self.is_running:
                if self._process_buf is None:
                    # Waiting for data to process
                    time.sleep(self._processor_sleep_time)
                    continue

                self._ask_data_event.clear()
                if self._save_path:
                    f_path = os.path.join(
                        self._save_path, 'record_{:.0f}.wav'.format(time.time())
                    )
                    wavfile.write(f_path, self._sample_rate, self._process_buf)
                    logger.info('"{}" saved'.format(f_path))

                logger.info('Start processing')
                predictions = proc.get_predictions(
                    self._sample_rate, self._process_buf)
                formatted = format_predictions(predictions)
                logger.info('Predictions: {}'.format(formatted))

                self.events_queue.append((datetime.datetime.now(), formatted))
                self._send_dh(predictions)

                logger.info('Stop processing')
                self._process_buf = None
                self._ask_data_event.set()

    def _send_dh(self, data):
        if not self.dh_status.connected:
            logger.error('Devicehive is not connected')
            return

        self.deviceHive.handler.send(data)


if __name__ == '__main__':
    server = Daemon(DeviceHiveHandler, routes=routes)
    server.start()
