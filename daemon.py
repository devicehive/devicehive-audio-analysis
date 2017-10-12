import os
import json
import uuid
import threading
from string import Template
from urllib.parse import parse_qs
from cgi import parse_header, parse_multipart
from http.server import HTTPServer, BaseHTTPRequestHandler

from devicehive import DeviceHive, Handler


DEFAULT_CONFIG = {
    'url': 'http://playground.devicehive.com/api/rest',
    'token': '',
    'deviceid': 'lora_gateway_{}'.format(str(uuid.uuid4())[:8]),
    'frequency': 868000000
}


class DeviceHiveHandler(Handler):
    def __init__(self, api, deviceid):
        super(DeviceHiveHandler, self).__init__(api)
        self._device = None
        self._deviceid = deviceid

    def handle_connect(self):
        self._device = self.api.put_device(self._deviceid)
        self._device.subscribe_insert_commands()

    def handle_command_insert(self, command):
        print(command)


class Config(object):
    data_path = ''
    _data = None
    _update_callback = None

    def __init__(self, data_path, update_callback=None):
        self.data_path = data_path
        self._update_callback = update_callback
        self._data = DEFAULT_CONFIG.copy()

    def _on_update(self):
        if callable(self._update_callback):
            self._update_callback()

    @property
    def data(self):
        return self._data

    def save(self, data):
        self._data = data
        try:
            with open(self.data_path, "w") as f:
                json.dump(self._data, f, indent=4)
        except IOError:
            return False

        self._on_update()
        return True

    def load(self):
        try:
            with open(self.data_path, "r") as f:
                self._data = json.load(f)
        except IOError:
            return False

        self._on_update()
        return True


class ConfigHandler(BaseHTTPRequestHandler):
    template_dir = 'templates'

    def get_template(self, template_name):
        with open(os.path.join(self.template_dir, template_name)) as f:
            return Template(f.read())

    def do_GET(self):
        response = None

        if self.path == '/':
            template = self.get_template('index.html')
            response = template.substitute(**self.server.cfg.data)

        if response is not None:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')

    def do_POST(self):
        ctype, pdict = parse_header(self.headers['content-type'])
        postvars = {}
        if ctype == 'multipart/form-data':
            postvars = parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers['content-length'])
            postvars = parse_qs(
                self.rfile.read(length).decode(), keep_blank_values=True)

        try:
            new_data = {
                'url': postvars.get("url")[0],
                'token': postvars.get("token")[0],
                'deviceid': postvars.get("deviceid")[0],
                'frequency': int(postvars.get("frequency")[0])
            }
            err = not self.server.cfg.save(new_data)
        except IOError:
            err = True

        if err:
            code = 500
            t_name = 'error.html'
        else:
            code = 200
            t_name = 'success.html'

        template = self.get_template(t_name)
        response = template.substitute()

        self.send_response(code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(response.encode())


class Daemon(HTTPServer):
    _loop_thread = None
    _dh_thread = None
    deviceHive = None

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('server_address', ('0.0.0.0', 8000))
        kwargs.setdefault('RequestHandlerClass', ConfigHandler)

        super(Daemon, self).__init__(*args, **kwargs)

        self._loop_thread = threading.Thread(target=self._loop, daemon=True)
        self.cfg = Config('config.json', update_callback=self.restart_dh)
        self.cfg.load()

    def start(self):
        self._loop_thread.start()

    def start_dh(self):
        self._dh_thread = threading.Thread(target=self._dh, daemon=True)
        self._dh_thread.start()

    def restart_dh(self):
        self.stop_dh()
        self.start_dh()

    def stop_dh(self):
        if self.deviceHive is not None and self.deviceHive._transport.connected:
            self.deviceHive._transport.disconnect()

    def _dh(self):
        self.deviceHive = DeviceHive(
            DeviceHiveHandler, self.cfg.data['deviceid'])
        self.deviceHive.connect(
            self.cfg.data['url'], refresh_token=self.cfg.data['token'])

    def _loop(self):
        self.serve_forever()

    def stop(self):
        self.shutdown()

    def send(self, str):
        pass # TODO self.deviceHive


def run():
    d = Daemon()
    d.start()
    while True:
        d.send(input())


if __name__ == '__main__':
    run()
