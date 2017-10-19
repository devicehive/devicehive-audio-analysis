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

import os
import posixpath
import mimetypes
import shutil
from http import HTTPStatus
from string import Template


__all__ = ['BaseController', 'Controller', 'StaticController']


class BaseController(object):
    def __init__(self, base_dir):
        self.base_dir = base_dir

    def dispatch(self, handler, *args, **kwargs):
        command = handler.command.lower()
        if not hasattr(self, command):
            raise NotImplementedError
        method = getattr(self, command)
        return method(handler, *args, **kwargs)

    def get(self, handler, *args, **kwargs):
        raise NotImplementedError

    def post(self, handler, *args, **kwargs):
        raise NotImplementedError


class Controller(BaseController):
    template_dir = 'templates'

    def get_template(self, name):
        with open(os.path.join(self.base_dir, self.template_dir, name)) as f:
            return Template(f.read())

    def render_template(self, name, **kwargs):
        return self.get_template(name).safe_substitute(**kwargs)


class StaticController(BaseController):
    static_dir = 'static'
    extensions_map = {}

    def __init__(self, *args, **kwargs):
        super(StaticController, self).__init__(*args, **kwargs)

        if not mimetypes.inited:
            mimetypes.init()

        self.extensions_map = mimetypes.types_map.copy()

    def get_file_path(self, path):
        return os.path.join(self.base_dir, self.static_dir, path)

    def guess_type(self, path):
        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        return self.extensions_map.get(ext, 'application/octet-stream')

    def get(self, handler, *args, **kwargs):
        f_name = kwargs.get('f_name')
        path = self.get_file_path(f_name)
        try:
            with open(path, 'rb') as f:
                handler.send_response(HTTPStatus.OK)
                handler.send_header('Content-type', self.guess_type(path))
                handler.end_headers()
                shutil.copyfileobj(f, handler.wfile)

        except IOError:
            handler.send_error(HTTPStatus.NOT_FOUND, 'File Not Found')
