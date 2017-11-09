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
from devicehive import DeviceHive, Handler, TransportError

from audio.captor import Captor
from audio.processor import WavProcessor, format_predictions
from web.base import Server
from web.routes import routes

from log_config import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('audio_analysis.daemon')


DEFAULT_CONFIG = {
    'url': 'http://playground.dev.devicehive.com/api/rest',
    'token': '',
    'deviceid': 'audio-analysis-demo',
}


class DeviceHiveHandler(Handler):
    def __init__(self, api, deviceid):
        super(DeviceHiveHandler, self).__init__(api)
        self._device = None
        self._deviceid = deviceid

    def handle_connect(self):
        self._device = self.api.put_device(self._deviceid)
        self._device.subscribe_insert_commands()

    def handle_command_insert(self, command):
        command.status = 'accepted'
        command.save()
        # TODO: react on command somehow
        print(command)

    def send(self, data):
        if isinstance(data, str):
            notification = data
        else:
            try:
                notification = json.dumps(data)
            except TypeError:
                notification = str(data)

        self._device.send_notification(notification)


class DHStatus(object):
    _status = ''
    _error = ''

    UNKNOWN = 'unknown'
    CONNECTED = 'connected'
    DISCONNECTED = 'disconnected'
    CONNECTING = 'connecting'

    status_map = {
        CONNECTED: 'success',
        DISCONNECTED: 'error',
        CONNECTING: 'inprogress'
    }

    def __init__(self):
        self._status = self.UNKNOWN

    @property
    def status(self):
        return self._status

    @property
    def connected(self):
        return self._status == self.CONNECTED

    def set_status(self, status, error=''):
        self._status = status
        self._error = error

    def set_connected(self):
        self.set_status(self.CONNECTED)

    def set_disconnected(self, error=''):
        self.set_status(self.DISCONNECTED, error)

    def set_connecting(self):
        self.set_status(self.CONNECTING)

    @property
    def error(self):
        return self._error

    @property
    def data(self):
        return {
            'status': self.status,
            'class': self.status_map.get(self.status, ''),
            'error': self.error
        }


class Config(object):
    data_path = ''
    _data = None
    _update_callback = None

    def __init__(self, data_path, update_callback=None):
        self.data_path = data_path
        self._update_callback = update_callback
        self._data = DEFAULT_CONFIG.copy()

    def _on_update(self):
        if callable(self._update_callback):
            self._update_callback()

    @property
    def data(self):
        return self._data

    def save(self, data):
        self._data = data
        try:
            with open(self.data_path, "w") as f:
                json.dump(self._data, f, indent=4)
        except IOError:
            return False

        self._on_update()
        return True

    def load(self):
        try:
            with open(self.data_path, "r") as f:
                self._data = json.load(f)
        except IOError:
            return False

        self._on_update()
        return True


class Daemon(Server):
    _dh_thread = None
    _process_thread = None
    _web_thread = None

    _process_buf = None
    _ask_data_event = None
    _captor = None
    _sample_rate = 16000
    _processor_sleep_time = 0.01

    dh_cfg = None
    deviceHive = None
    dh_status = None
    events_queue = None

    base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'web')

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('routes', routes)
        min_time = kwargs.pop('min_capture_time', 5)
        max_time = kwargs.pop('max_capture_time', 5)
        self._save_path = kwargs.pop('max_capture_time', None)
        super(Daemon, self).__init__(*args, **kwargs)

        self.events_queue = deque(maxlen=10)

        self.dh_cfg = Config('config.json', update_callback=self._restart_dh)
        self.dh_status = DHStatus()

        self._web_thread = threading.Thread(
            target=self._web_loop, daemon=True, name='web')

        self._ask_data_event = threading.Event()
        self._process_thread = threading.Thread(
            target=self._process_loop, daemon=True, name='processor')

        self._captor = Captor(
            min_time, max_time, self._ask_data_event, self._process)

    def send_dh(self, data):
        if not self._is_dh_connected():
            logger.warning('Devicehive is not connected')
            return

        self.deviceHive.handler.send(data)

    def start(self):
        self._start_web()
        self.dh_cfg.load()  # this will start DH thread automatically
        self._start_capture()
        self._start_process()

    def _start_web(self):
        logger.info('Start server http://{}:{}'.format(*self.server_address))
        self._web_thread.start()

    def _start_dh(self):
        if self._is_dh_connected():
            logging.info('Devicehive already started')
            return

        logger.info('Start devicehive')
        self._dh_thread = threading.Thread(
            target=self._dh_loop, daemon=True, name='device_hive')
        self._dh_thread.start()

    def _stop_dh(self):
        if not self._is_dh_connected():
            logging.info('Devicehive already stopped')
            return
        self.deviceHive.transport.disconnect()

    def _restart_dh(self):
        if self._is_dh_connected():
            self._stop_dh()

        self._start_dh()

    def _is_dh_connected(self):
        return self.dh_status.connected

    def _start_capture(self):
        logger.info('Start captor')
        self._captor.start()

    def _start_process(self):
        logger.info('Start processor loop')
        self._process_thread.start()

    def _web_loop(self):
        self.serve_forever()

    def _dh_loop(self):
        self.dh_status.set_connecting()
        self.deviceHive = DeviceHive(
            DeviceHiveHandler, self.dh_cfg.data['deviceid'])
        error = ''
        try:
            self.dh_status.set_connected()
            url = self.dh_cfg.data['url']
            refresh_token = self.dh_cfg.data['token']
            self.deviceHive.connect(url, refresh_token=refresh_token)
        except TransportError as e:
            logger.exception(e)
            error = str(e)
        finally:
            self.dh_status.set_disconnected(error)
            logger.info('Stop devicehive')

    def _process(self, data):
        self._process_buf = np.frombuffer(data, dtype=np.int16)

    def _process_loop(self):
        with WavProcessor() as proc:
            self._ask_data_event.set()
            while True:
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
                logger.info(
                    'Predictions: {}'.format(formatted))

                self.events_queue.append((datetime.datetime.now(), formatted))
                self.send_dh(predictions)

                logger.info('Stop processing')
                self._process_buf = None
                self._ask_data_event.set()


def run():
    d = Daemon()
    d.start()
    while True:
        d.send_dh(input())


if __name__ == '__main__':
    run()
