from http.server import BaseHTTPRequestHandler

from .router import Router


class RoutedHandler(BaseHTTPRequestHandler):

    def __init__(self, request, client_address, server):
        self.__router = Router(self, server.routes)
        super(RoutedHandler, self).__init__(request, client_address, server)


    def do_GET(self):
        self.__router.route(self.path)
