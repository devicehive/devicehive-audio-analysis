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

import time
import argparse
import logging
import numpy as np

from utils import general

CAPTURE_RATE = 16000  # do not change

parser = argparse.ArgumentParser(description='Capture and process audio')
parser.add_argument('-p', '--capture_period', type=int, min=1, max=10,
                    default=5, action=general.MinMaxAction, metavar='PERIOD',
                    help='Capture period in seconds')
parser.add_argument('-c', '--cycles', type=int, min=1, default=None,
                    action=general.MinMaxAction, metavar='CYCLES',
                    help='Number of capture cycles (infinite by default)')


logger = logging.getLogger('audio_analysis')
logger.setLevel('DEBUG')


def is_capture_timeout(start, period):
    current = time.time()
    return current-start > period


def capture(capture_period, cycles):
    # local import to reduce start-up time
    from audio_device import AudioDevice
    from process import WavProcessor

    ad = AudioDevice()
    counter = 0

    with WavProcessor() as proc:
        while True:
            if cycles and counter >= cycles:
                break

            process_buf = np.empty(0)
            start_time = time.time()
            logger.info('Start recording cycle.')
            while not is_capture_timeout(start_time, capture_period):
                buf = ad.read(CAPTURE_RATE)
                if buf is None:
                    logger.debug('Buffer is empty.')
                    return

                process_buf = np.append(
                    process_buf, np.frombuffer(buf, dtype=np.int16))

            logger.info('Stop recording cycle.')

            predictions = proc.get_predictions(
                CAPTURE_RATE, process_buf, format=True)
            logger.info('Predictions: {}'.format(predictions))

            counter += 1


if __name__ == '__main__':
    args = parser.parse_args()
    capture(**vars(args))
