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

import os
import time
import argparse
import threading
import numpy as np
import logging.config
from scipy.io import wavfile


parser = argparse.ArgumentParser(description='Capture and process audio')
parser.add_argument('--min_time', type=float, default=5, metavar='SECONDS',
                    help='Minimum capture time')
parser.add_argument('--max_time', type=float, default=7, metavar='SECONDS',
                    help='Maximum capture time')
parser.add_argument('-s', '--save_path', type=str, metavar='PATH',
                    help='Save captured audio samples to provided path')


LOGGING = {
    'version': 1,
    'formatters': {
        'simple': {
            'format': '[%(levelname)s] %(asctime)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'audio_analysis': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
}

logging.config.dictConfig(LOGGING)


logger = logging.getLogger('audio_analysis')


class Capture(object):
    _sample_rate = 16000
    _capture_rate = _sample_rate*2  # bytes per second

    _processor_ready = False
    _processor_sleep_time = 0.01
    _processor_thread = None
    _process_buf = None

    def __init__(self, min_time=5, max_time=7, save_path=None):
        """
        Init capture class
        :param min_time: Minimum capture time to process (seconds)
        :param max_time: Maximum capture time to process (seconds)
        :param save_path: Path to save recorded samples
        """
        self._min_time = min_time
        self._max_time = max_time
        self._save_path = save_path

        self._min_data = self._min_time*self._capture_rate
        self._max_data = self._max_time*self._capture_rate

        self._processor_thread = threading.Thread(
            target=self._process_loop, daemon=True)
        self._processor_thread.start()

    def start(self):
        # TODO: pulseaudio init stream globally and start write data to it
        # right after init process is completed.
        # So we need to move stream init or keep this import here to avoid
        # buffer overflow
        from audio_device import AudioDevice

        ad = AudioDevice()
        capture_buf = bytes()

        logger.info('Start recording cycle.')
        while True:
            if self._processor_ready and len(capture_buf) >= self._min_data:
                logger.info('Stop recording cycle.')
                self._process(capture_buf)
                capture_buf = bytes()
                logger.info('Start recording cycle.')

            buf = ad.read(self._sample_rate)
            if buf is None:
                logger.debug('Buffer is empty.')
                return
            capture_buf += buf

            overflow = len(capture_buf) - self._max_data
            if overflow > 0:
                logger.info('Buffer overflow, truncate {}b.'.format(overflow))
                capture_buf = capture_buf[overflow:]

    def _process(self, buf):
        self._process_buf = np.frombuffer(buf, dtype=np.int16)
        self._processor_ready = False

    def _process_loop(self):
        # local import to reduce start-up time
        from process import WavProcessor

        with WavProcessor() as proc:
            self._processor_ready = True
            while True:
                if self._process_buf is None:
                    # Waiting for data to process
                    time.sleep(self._processor_sleep_time)
                    continue

                if self._save_path:
                    f_path = os.path.join(
                        self._save_path, 'record_{:.0f}.wav'.format(time.time())
                    )
                    wavfile.write(f_path, self._sample_rate, self._process_buf)
                    logger.info('"{}" saved.'.format(f_path))

                logger.info('Start processing.')
                predictions = proc.get_predictions(
                    self._sample_rate, self._process_buf, format=True)
                logger.info('Predictions: {}'.format(predictions))
                logger.info('Stop processing.')
                self._process_buf = None
                self._processor_ready = True


if __name__ == '__main__':
    args = parser.parse_args()

    path = args.save_path
    if path and not os.path.exists(path):
        parser.error('"{}" doesn\'t exist'.format(path))
    if path and not os.path.isdir(path):
        parser.error('"{}" isn\'t a directory'.format(path))

    if args.min_time > args.max_time:
        parser.error('min_time is grater than max_time')

    Capture(**vars(args)).start()
