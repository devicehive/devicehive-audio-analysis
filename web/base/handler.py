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

from urllib.parse import parse_qs
from cgi import parse_header, parse_multipart
from http.server import BaseHTTPRequestHandler

from .router import Router


__all__ = ['RoutedHandler']


class RoutedHandler(BaseHTTPRequestHandler):
    _post_vars = None

    def __init__(self, request, client_address, server):
        self.__router = Router(self, server.routes)
        super(RoutedHandler, self).__init__(request, client_address, server)

    def do_GET(self):
        self.__router.route(self.path)

    def do_POST(self):
        self.__router.route(self.path)

    @property
    def post_vars(self):
        if self._post_vars is None:
            ctype, pdict = parse_header(self.headers['content-type'])
            post_vars = {}
            if ctype == 'multipart/form-data':
                post_vars = parse_multipart(self.rfile, pdict)
            elif ctype == 'application/x-www-form-urlencoded':
                length = int(self.headers['content-length'])
                post_vars = parse_qs(
                    self.rfile.read(length).decode(), keep_blank_values=True
                )

            self._post_vars = post_vars

        return self._post_vars
