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

import tensorflow as tf


# Workaround for num_epochs issue.
def set_up_init_ops(variables):
    init_op_list = []
    for variable in list(variables):
        if "train_input" in variable.name:
            init_op_list.append(tf.assign(variable, 1))
            variables.remove(variable)
    init_op_list.append(tf.variables_initializer(variables))
    return init_op_list


def load_model(sess, checkpoint_path):
    meta_graph_location = checkpoint_path + '.meta'

    saver = tf.train.import_meta_graph(
        meta_graph_location, clear_devices=True, import_scope='m2'
    )

    saver.restore(sess, checkpoint_path)

    sess.run(
        set_up_init_ops(tf.get_collection_ref(tf.GraphKeys.LOCAL_VARIABLES))
    )
