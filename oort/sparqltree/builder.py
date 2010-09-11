from itertools import chain

from oort.sparqltree.autotree import URI_KEY, BNODE_KEY
from oort.sparqltree.autotree import is_lang_node, is_datatype_node, is_resource


def to_graph(nodelens, tree):
    return GraphBuilder(nodelens).to_graph(tree)

#graphify = to_graph


class GraphBuilder(object):
    """
    This builder turns a raw SPARQL tree result (or anything isomorphic to
    such) into cyclic graphs with merged references (using``URI_KEY`` or
    ``BNODE_KEY`` to merge resource nodes).

    It can use a supplied ``nodelens`` (or uses the default BasicNodeLens)
    which is used to build up result resource objects and cast literals.

    The builder maintains a state of indexed resource nodes, which will be of
    consequence if it is reused.
    """

    def __init__(self, nodelens=None):
        # TODO: simplify by using same index and store bnodes as '_:'+bnode?
        self._uri_index = {}
        self._blank_index = {}
        self._nodelens = nodelens or BasicNodeLens

    def to_graph(self, tree):
        graph = self._make_resource(tree, None)
        self._nodelens.complete(
                chain(self._uri_index.values(), self._blank_index.values()))
        return graph

    def _process_node(self, node, via):
        if is_resource(node):
            return self._make_resource(node, via)
        elif isinstance(node, list):
            return self._cast_list(node, via)
        else:
            return self._nodelens.cast_literal(node)

    def _make_resource(self, node, via):
        newres = self._nodelens.new_resource(node)
        resource = self._to_indexed_resource(newres)
        if via:
            self._nodelens.update_via(resource, *via)
        for key, subnode in node.items():
            resource[key] = self._process_node(subnode,
                    (key, resource))
        return resource

    def _to_indexed_resource(self, resource):
        indexed = self._get_indexed_resource(resource)
        if not indexed:
            self._index_resource(resource)
            return resource
        else:
            self._nodelens.merge_resources(resource, indexed)
            return indexed

    def _get_indexed_resource(self, resource):
        return (self._uri_index.get(resource.get(URI_KEY)) or
                self._blank_index.get(resource.get(BNODE_KEY)))

    def _index_resource(self, resource):
        if URI_KEY in resource:
            uri = resource[URI_KEY]
            self._uri_index[uri] = resource
        elif BNODE_KEY in resource:
            nodeid = resource[BNODE_KEY]
            self._blank_index[nodeid] = resource

    def _cast_list(self, nodelist, via):
        return [self._process_node(node, via) for node in nodelist]


class BasicNodeLens(object):
    """
    This Basic Node Lens produces plain dict resources and does no casting of
    literals.

    Incoming "via" references are stored in the built resources with the
    ``VIA_KEY``, as a dict with referencing key as key and a list of resources.
    """

    VIA_KEY = '$via'

    def new_resource(self, node):
        return dict(node)

    def merge_resources(self, source, result):
        result.update(source)

    def update_via(self, resource, via_key, via_resource):
        via = resource.setdefault(self.VIA_KEY, self._new_via_object())
        via.setdefault(via_key, []).append(via_resource)

    def _new_via_object(self):
        return {}

    def cast_literal(self, node):
        return node

    def complete(self, resources):
        pass


class LocalizedNodeLens(BasicNodeLens):
    """
    This Node Lens uses the provided locale to turn dictionaries containing
    language tags into plain values.
    """
    def __init__(self, locale=None):
        super(LocalizedNodeLens, self).__init__()
        self._locale = locale
        self._langkey = '@' + (locale or '')

    def cast_literal(self, node):
        if is_lang_node(node):
            if node:
                return node.get(self._langkey) or node.values()[0]
            else:
                return None
        else:
            return super(LocalizedNodeLens, self).cast_literal(node)


class PlainLens(LocalizedNodeLens):
    """
    This lens creates decorated Expando objects, who:

    - expose any ``URI_KEY`` via ``PlainLens.EXPOSED_URI_KEY``
    - expose the URI leaf ("uri term") via ``PlainLens.URI_TERM_KEY``
    - expose via-references via ``PlainLens.VIA_KEY``
    """

    EXPOSED_URI_KEY = 'resource_uri'
    URI_TERM_KEY = 'uri_term'
    VIA_KEY  = 'ref_via'

    def new_resource(self, node):
        expando = Expando(super(PlainLens, self).new_resource(node))
        uri = expando.get(URI_KEY)
        if uri:
            expando[self.EXPOSED_URI_KEY] = uri
            expando[self.URI_TERM_KEY] = uri_term(uri)
        return expando

    def _new_via_object(self):
        return Expando()


class Expando(dict):
    def __getattr__(self, key):
        return self[key]


def uri_term(uri):
    if '#' in uri:
        return uri.rsplit('#', 1)[-1]
    else:
        return uri.rsplit('/', 1)[-1]

