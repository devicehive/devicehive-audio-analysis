# Copyright (C) 2017 DataArt
#
# Based on
#
# Copyright 2016 Google Inc. All Rights Reserved.
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

import numpy as np


def resize(data, axis, new_size):
    shape = list(data.shape)

    pad_shape = shape[:]
    pad_shape[axis] = np.maximum(0, new_size - shape[axis])

    shape[axis] = np.minimum(shape[axis], new_size)
    shape = np.stack(shape)

    slices = [slice(0, s) for s in shape]

    resized = np.concatenate([
      data[slices],
      np.zeros(np.stack(pad_shape))
    ], axis)

    # Update shape.
    new_shape = list(data.shape)
    new_shape[axis] = new_size
    resized.reshape(new_shape)
    return resized
