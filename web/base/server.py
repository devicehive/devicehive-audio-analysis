from http.server import HTTPServer

from .handler import RoutedHandler


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
