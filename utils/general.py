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
import argparse


class MinMaxAction(argparse.Action):

    def __init__(self, *args, **kwargs):
        self.min = kwargs.pop('min', None)
        self.max = kwargs.pop('max', None)

        super(MinMaxAction, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):

        if self.min is not None and values < self.min:
            parser.error(
                'Minimum value for "{}" is {}'.format(option_string, self.min))

        if self.max is not None and values > self.max:
            parser.error(
                'Maximum value for "{}" is {}'.format(option_string, self.max))

        setattr(namespace, self.dest, values)


class PathExistsAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not os.path.exists(values):
            parser.error('"{}" doesn\'t exist'.format(values))
        if not os.path.isdir(values):
            parser.error('"{}" isn\'t a directory'.format(values))

        setattr(namespace, self.dest, values)
