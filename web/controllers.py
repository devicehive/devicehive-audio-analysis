from web.base.controller import Controller


class SimpleController(Controller):

    def dispatch(self, handler, *args, **kwargs):
        handler.send_response(200)
        handler.send_header('Content-type', 'text/html')
        handler.end_headers()
        handler.wfile.write(self.render_template('success.html'))
