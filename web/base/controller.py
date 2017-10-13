import os
import inspect
from string import Template


class Controller(object):
    template_dir = 'templates'


    def get_template(self, name):
        class_path = inspect.getfile(self.__class__)
        file_path = os.path.dirname(os.path.realpath(class_path))
        with open(os.path.join(file_path, self.template_dir, name)) as f:
            return Template(f.read())

    def render_template(self, name, **kwargs):
        return self.get_template(name).substitute(**kwargs).encode()

    def dispatch(self, handler, *args, **kwargs):
        raise NotImplementedError
