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

import json
from io import StringIO
from http import HTTPStatus

from web.base import BaseController, Controller


class Config(Controller):

    def get(self, handler, *args, **kwargs):
        response = self.render_template('index.html', **handler.server.cfg.data)

        handler.send_response(HTTPStatus.OK)
        handler.send_header('Content-type', 'text/html')
        handler.end_headers()
        handler.wfile.write(response.encode())

    def post(self, handler, *args, **kwargs):
        data = handler.post_vars
        new_data = {
            'url': data.get("url")[0],
            'token': data.get("token")[0],
            'deviceid': data.get("deviceid")[0],
        }
        handler.server.cfg.save(new_data)

        self.get(handler)


class DHStatusUpdate(BaseController):
    def get(self, handler, *args, **kwargs):
        response = json.dumps(handler.server.dh_status.data)

        handler.send_response(HTTPStatus.OK)
        handler.send_header('Content-type', 'application/json')
        handler.end_headers()
        handler.wfile.write(response.encode())


class Events(Controller):
    def get(self, handler, *args, **kwargs):
        response = self.render_template('events.html')

        handler.send_response(HTTPStatus.OK)
        handler.send_header('Content-type', 'text/html')
        handler.end_headers()
        handler.wfile.write(response.encode())


class EventsUpdate(Controller):
    def get(self, handler, *args, **kwargs):
        with StringIO() as f:
            for timestamp, predictions in handler.server.events_queue:
                data = {
                    'timestamp': '{:%Y-%m-%d %H:%M:%S}'.format(timestamp),
                    'predictions': predictions
                }
                f.writelines(self.render_template('event.html', **data))

            response = f.getvalue()

        handler.send_response(HTTPStatus.OK)
        handler.send_header('Content-type', 'text/html')
        handler.end_headers()
        handler.wfile.write(response.encode())
