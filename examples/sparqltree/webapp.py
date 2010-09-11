from __future__ import with_statement
from time import time
import os.path as p
import mimetypes

from paste.fileapp import DataApp, FileApp
from paste.httpexceptions import HTTPNotFound

from stringtemplate3 import StringTemplateGroup

from oort.sparqltree.access.util import discover_access
from oort.sparqltree.treelens import TreeLens


class WebApp(object):
    def __init__(self, access, default_locale, basedir=""):
        self._default_locale = default_locale
        self._access = access
        self._basedir = basedir
        self._templates = templates = StringTemplateGroup("templates",
                basedir)
        templates.refreshInterval = 0 # TODO: make configurable (this is for no caching)

    def __call__(self, environ, start_response):
        handler = self._get_handler(environ)
        return handler(environ, start_response)

    def _get_handler(self, environ):
        path = environ['PATH_INFO']
        filepath = p.join(self._basedir, *path.split('/'))
        if not p.exists(filepath):
            return HTTPNotFound('The resource does not exist',
                    comment="Nothing at %r" % path).wsgi_application
        # TODO: this exposes all files; sep. query-views-tplts and static files
        if p.isfile(filepath):
            return FileApp(filepath)
        else:
            data, mimetype, encoding = self._process_view(filepath)
            headers = [
                ('Content-Type', mimetype),
                ('Content-Encoding', encoding),
            ]
            return DataApp(data, headers)

    def _process_view(self, filedir, encoding='utf-8'):
        handle_view = (self._find_handle_view(filedir)
                or self._make_handle_view(filedir))
        data, mimetype = handle_view(self, None)
        if encoding:
            data = data.encode(encoding)
        return data, mimetype, encoding

    def _find_handle_view(self, viewdir):
        viewcode = p.join(viewdir, "view.py")
        if p.exists(viewcode):
            vglobals = {}
            # TODO: really, make this use modules (and better separation?)
            execfile(viewcode, vglobals)
            viewname = 'handle_view'
            if viewname in vglobals:
                return vglobals[viewname]

    def _make_handle_view(self, filedir):
        name = p.basename(p.normpath(filedir))
        def handle_view(app, request):
            locale = app._default_locale
            with app.get_file("%s/%s.rq" % (name, name)) as f:
                query = f.read()
            tree = app.call_endpoint(query)
            lens = TreeLens(tree, locale)
            tplt = app.get_template("%s/%s-html" % (name, name))
            tplt[name] = lens[name]
            return unicode(tplt), 'text/html'
        return handle_view

    def call_endpoint(self, query):
        return self._access.run_query_to_tree(query)

    def get_file(self, filename):
        return open(p.join(self._basedir, filename))

    def get_template(self, name):
        return self._templates.getInstanceOf(name)


def serve_wsgi(app, servername='', port=None):
    port = port or 8800
    from wsgiref.simple_server import make_server
    httpd = make_server(servername, port, app)
    print "Serving HTTP on port %s..." % port
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':

    import logging
    from optparse import OptionParser

    op = OptionParser(
            "%prog [-h] [...] ENDPOINT_URL BASEDIR")
    op.add_option('-p', '--port', type=int, default=7070,
            help="Port to serve as web app.")
    op.add_option('-l', '--default-locale', default="en")
    op.add_option('-o', '--one-off-url', default=None,
            help="Process given url once and print to stdout ("
                "doesn't start server).")

    opts, args = op.parse_args()
    if len(args) != 2:
        op.print_usage()
        op.exit()

    endpoint_url = args[0]
    basedir = args[1]
    once_url = opts.one_off_url

    access = discover_access(endpoint_url)
    app = WebApp(access, opts.default_locale, basedir)

    if once_url:
        from paste.fixture import TestApp
        print TestApp(app).get(once_url)
    else:
        logging.basicConfig(level=logging.INFO)
        serve_wsgi(app, port=opts.port)


