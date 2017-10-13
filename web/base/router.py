import re


class Router(object):

    def __init__(self, handler, routes):
        self.__routes = routes
        self.__handler = handler

    def route(self, path):
        for regexp, controller in self.__routes:
            match = re.search(regexp, path)
            if match:
                obj = controller()
                obj.dispatch(self.__handler, match.groups(), match.groupdict())
                return

        # Not found
        self.__handler.send_response(404)
        self.__handler.end_headers()
