#=======================================================================
from oort.util.graphs import get_format, load_if_modified, OUG_NS
import os
from os.path import splitext, expanduser
#=======================================================================


DIR = "__dir"


def load_fodder(graph, basedir, errorHandler=None):
    basedir = expanduser(basedir)
    for base, fdirs, fnames in os.walk(basedir):
        formatMap = DEFAULT_FORMAT_MAP # TODO
        # TODO:
        #   - load fodder script
        #   - get settings
        #   - read children
        #   - create here
        #   - on_enter()
        #   - if ok, read children (fdirs and fnames) [with base_uri]
        #   - on_exit()
        #
        for fname in fnames:
            fpath = os.path.join(base, fname)
            format = get_format(fpath, formatMap)
            if not format:
                continue
            try:
                load_if_modified(graph, fpath, format)
            except (ValueError, KeyError), e:
                if errorHandler:
                    errorHandler(e, fpath)
                else:
                    raise e


class Config(object):
    pass # TODO


class ContentItem(object):
    def __init__(self, uri, filepath):
        self.uri = URIRef(uri)
        self.filepath = filepath
        self.readtype = None # either rdflib format or DIR

class ContentNode(ContentItem):
    def __init__(self, uri, filepath, config,
                 parent=None, children=frozenset([])):
        ContentItem.__init__(self, uri, filepath)
        self.config = config
        self.parent = parent
        self.children = children

    def run_shadowed_on_exit(self, graph):
        "Run parent's on_exit *if* self.on_exit is not the same one."
        p = self.parent
        if p and p.on_exit != self.on_exit:
            p.on_exit(graph, self)


