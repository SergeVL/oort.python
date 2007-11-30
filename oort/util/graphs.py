# -*- coding: UTF-8 -*-
#=======================================================================
import os
from os.path import dirname, join, splitext, expanduser
from StringIO import StringIO
import logging
from rdflib import Literal, URIRef, Namespace, ConjunctiveGraph, RDFS
#=======================================================================

_logger = logging.getLogger(name=__name__)


def get_ext(fpath, lower=True):
    """Gets the file extension from a file(path); stripped of leading '.' and in
    lower case. Examples:

        >>> get_ext("path/to/file.txt")
        'txt'
        >>> get_ext("OTHER.PDF")
        'pdf'
        >>> get_ext("noext")
        ''

    """
    ext = splitext(fpath)[-1]
    if lower:
        ext = ext.lower()
    if ext.startswith('.'):
        ext = ext[1:]
    return ext


DEFAULT_FORMAT_MAP = {
        'rdf': 'xml',
        'rdfs': 'xml',
        'owl': 'xml',
        'n3': 'n3',
        'ttl': 'n3',
        'nt': 'nt',
        'trix': 'trix',
        'xhtml': 'rdfa',
        'html': 'rdfa',
    }

def get_format(fpath, fmap=None):
    """Guess RDF serialization based on file suffix. Uses
    ``DEFAULT_FORMAT_MAP`` unless ``fmap`` is provided. Examples:

        >>> get_format('path/to/file.rdf')
        'xml'
        >>> get_format('path/to/file.owl')
        'xml'
        >>> get_format('path/to/file.ttl')
        'n3'
        >>> get_format('path/to/file.xhtml')
        'rdfa'
        >>> get_format('path/to/file.xhtml', {'xhtml': 'grddl'})
        'grddl'

    """
    fmap = fmap or DEFAULT_FORMAT_MAP
    ext = splitext(fpath)[-1][1:]
    return fmap.get(ext)


def get_uri_leaf(uri):
    """Get the "leaf" - fragment id or last segment - of a URI. Examples:

        >>> get_uri_leaf('http://example.org/ns/things#item')
        u'item'
        >>> get_uri_leaf('http://example.org/ns/stuff/item')
        u'item'
        >>> get_uri_leaf('http://example.org/ns/stuff/')
        u''
    """
    return unicode(uri).split('/')[-1].split('#')[-1]


#-----------------------------------------------------------------------


def collect_dir(basedir, loader,
        accept=None, getFormat=get_format, errorHandler=None):
    for base, fdirs, fnames in os.walk(basedir):
        for fname in fnames:
            fpath = join(base, fname)
            if accept and not accept(fpath):
                continue
            format = getFormat(get_ext(fpath))
            if not format:
                continue
            try:
                loader(fpath, format)
            except Exception, e:
                if errorHandler:
                    errorHandler(e, fpath)
                else:
                    raise


# TODO: Brittle? Only fixes non-posix fpaths (unix fpaths work anyway), and
# only on non-posix systems. Is the "fix" good enough?
def fix_nonposix_path(fpath, sep=os.path.sep):
    if sep != '/':
        fpath =  "file:///" + "/".join(fpath.split(os.path.sep))
    return fpath


#-----------------------------------------------------------------------


def dir_to_graph(basedir, graph=None):
    """
    Recursively loads file system directory into the given (or an in-memory)
    graph. Returns the graph.
    """
    graph = graph or ConjunctiveGraph()
    allowedExts = DEFAULT_FORMAT_MAP.keys()
    def accept(fpath):
        ext = get_ext(fpath)
        return ext in allowedExts
    def loader(fpath, format):
        fpath = fix_nonposix_path(fpath)
        _logger.info("Loading: <%s>" % fpath)
        graph.load(fpath, format=format)
    collect_dir(basedir, loader, accept)
    return graph


def loader(graph, basedir=None, formatMap=None):
    if basedir:
        basedir = expanduser(basedir)
    def load_data(fpath):
        if basedir:
            fpath = join(basedir, fpath)
        load_if_modified(graph, fpath, format=get_format(fpath, formatMap))
    return load_data


#-----------------------------------------------------------------------
# TODO: hook-in for basic inference? (subClassOf/subPropertyOf; with FuXi..)


OUG_NS = Namespace('tag:oort.to,2006:system/util/graphs#')
LAST_MOD = OUG_NS.lastmodified


def load_if_modified(graph, fpath, format='xml', contextUri=None):
    """
    Loads the given file (with optional given ``format``) into the ``graph``,
    using timestamps and named subgraphs to manage updates.

    The file will *only* be loaded if it has been changed since last load (if
    any). If loaded it will end up in a subgraph named by the contextUri, and
    the last modified time will be added for that context.

    If the contextUri exists in the graph and the stored timestamp is older
    than the file timestamp, the subgraph in that context will be removed and
    the file will be reloaded.

    ``contextUri``
        an optional context uri to be used. If not supplied,
        graph.absolutize(filepath) will be used.
    """
    modTime = os.stat(fpath).st_mtime
    fpath = fix_nonposix_path(fpath)
    contextUri = contextUri or graph.absolutize(fpath)
    try:
        loadedModValue = graph.value(contextUri, LAST_MOD)
        loadedModTime = float(loadedModValue)
    except TypeError:
        loadedModTime = -1
    if modTime > loadedModTime:
        graph.remove((contextUri, LAST_MOD, loadedModValue))
        graph.remove_context(graph.context_id(contextUri))
        _logger.info('Loading <%s> into <%s>' % (fpath, contextUri))
        graph.load(fpath, publicID=contextUri, format=format)
        graph.add((contextUri, LAST_MOD, Literal(modTime)))


def load_dir_if_modified(graph, basedir,
        accept=None, getFormat=None, errorHandler=None,
        computeContextUri=None):
    """
    Loads a file system directory into the given graph.

    ``accept``
        an optional callable returning wether a given file should be loaded.

    ``computeContextUri``
        an optional callable returning the context uri to be used. It's given
        the arguments (graph, filepath). If not supplied, the default method of
        ``load_if_modified`` will be used.
    """
    basedir = expanduser(basedir)
    def loader(fpath, format):
        print "DEBUG:", format
        if computeContextUri:
            contextUri = computeContextUri(graph, fpath)
        else:
            contextUri = None
        load_if_modified(graph, fpath, format, contextUri)
    collect_dir(basedir, loader, accept, getFormat, errorHandler)


# TODO: backwards-compat; deprecate?
def load_dir(graph, basedir, formatMap=None, errorHandler=None):
    formatMap = formatMap or DEFAULT_FORMAT_MAP
    load_dir_if_modified(
            graph, basedir, None, formatMap.get, errorHandler)


#-----------------------------------------------------------------------


def replace_uri(graph, old, new, predicates=False):
    newGraph = ConjunctiveGraph()
    for pfx, ns in graph.namespace_manager.namespaces():
        newGraph.namespace_manager.bind(pfx, ns)
    for s, p, o in graph:
        s = _change_uri(s, old, new)
        if predicates:
            p = _change_uri(p, old, new)
        if isinstance(o, URIRef):
            o = _change_uri(o, old, new)
        newGraph.add((s, p, o))
    return newGraph

def _change_uri(uri, old, new):
    uri = uri.replace(old, new, 1)
    return URIRef(uri)


