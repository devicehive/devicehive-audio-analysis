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

from http.server import HTTPServer

from .handler import RoutedHandler


__all__ = ['Server']


class Server(HTTPServer):
    _routes = None

    def __init__(self, *args, **kwargs):
        self._routes = kwargs.pop('routes', [])

        kwargs.setdefault('server_address', ('0.0.0.0', 8000))
        kwargs.setdefault('RequestHandlerClass', RoutedHandler)

        super(Server, self).__init__(*args, **kwargs)

    @property
    def routes(self):
        return self._routes
