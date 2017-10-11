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
import logging.config
import numpy as np
from scipy.io import wavfile

from utils import general

CAPTURE_RATE = 16000  # do not change

parser = argparse.ArgumentParser(description='Capture and process audio')
parser.add_argument('-p', '--capture_period', type=int, min=1, max=10,
                    default=5, action=general.MinMaxAction, metavar='PERIOD',
                    help='Capture period in seconds')
parser.add_argument('-c', '--cycles', type=int, min=1,
                    action=general.MinMaxAction, metavar='CYCLES',
                    help='Number of capture cycles (infinite by default)')
parser.add_argument('-s', '--save_path', type=str,
                    action=general.PathExistsAction,
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


def is_capture_timeout(start, period):
    current = time.time()
    return current-start > period


def capture(capture_period, cycles, save_path):
    # local import to reduce start-up time
    from process import WavProcessor

    with WavProcessor() as proc:
        # TODO: pulseaudio init stream globally and start write data to it
        # right after init process is completed.
        # So we need to move stream init or keep this import here to avoid data
        # in stream while tensorflow init process.
        from audio_device import AudioDevice

        ad = AudioDevice()
        count = 0

        while True:
            if cycles and count >= cycles:
                break

            capture_buf = bytes()
            start_time = time.time()
            logger.info('Start recording cycle.')
            while not is_capture_timeout(start_time, capture_period):
                buf = ad.read(CAPTURE_RATE)
                if buf is None:
                    logger.debug('Buffer is empty.')
                    return

                capture_buf += buf
            logger.info('Stop recording cycle.')

            logger.info('Start processing.')
            process_buf = np.frombuffer(capture_buf, dtype=np.int16)
            predictions = proc.get_predictions(
                CAPTURE_RATE, process_buf, format=True)
            logger.info('Predictions: {}'.format(predictions))
            logger.info('Stop processing.')

            if save_path:
                f_path = os.path.join(save_path, 'record_{}.wav'.format(count))
                wavfile.write(f_path, CAPTURE_RATE, process_buf)
                logger.info('"{}" saved.'.format(f_path))

            count += 1


if __name__ == '__main__':
    args = parser.parse_args()
    capture(**vars(args))
