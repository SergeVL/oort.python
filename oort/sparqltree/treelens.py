from oort.sparqltree.autotree import URI_KEY, is_lang_node
# TODO: also put values for BNODE_KEY in _index?


is_raw_node = lambda o: isinstance(o, dict) and not isinstance(o, TreeLens)


class AttrDict(dict):
    def __getattr__(self, key):
        return self[key]


class TreeLens(AttrDict):
    """
    This core tree lens processes a raw SPARQL tree result into a cyclic graph
    with merged references (using the ``URI_KEY``).

    It also uses the provided locale to turn dictionaries containing language
    tags into plain values.
    """

    def __init__(self, rawdict, locale=None, index=None, via=None):
        super(TreeLens, self).__init__(rawdict)
        if index is None:
            index = {}
        self._locale = locale
        self._langkey = '@'+locale if locale else None # TODO: + (locale or '')?
        self._index = index
        self._via = AttrDict(via or {})

        for k, v in self.items():
            self[k] = self._cast_value(v, k)
            # Replace references with indexed object
            if isinstance(v, dict) and v.get(URI_KEY) in index:
                self[k] = index[v.get(URI_KEY)]

        # NOTE: invoked last since loop above updates self, not indexed
        self._index_node()

    def _index_node(self):
        uri = self.get(URI_KEY)
        if uri:
            indexed = self._index.get(uri)
            if indexed:
                self._update_lens(indexed)
            else:
                self._index[uri] = self

    def _get_indexed_node(self, node):
        return self._index.get(node.get(URI_KEY))

    def _update_lens(self, lens):
        lens.update(self)
        via = self._via
        for key, l in lens._via.items():
            if key in via:
                l += via.pop(key) # NOTE: current lens is throw-away
        lens._via.update(via)

    def _new_lens(self, o, via_key):
        via_ref = self._get_indexed_node(self) or self
        return type(self)(o, self._locale, self._index, via={via_key: [via_ref]})

    def _cast_value(self, v, via_key):
        if is_lang_node(v):
            return v.get(self._langkey) or v.values()[0] if v else None
        elif is_raw_node(v):
            return self._new_lens(v, via_key)
        elif isinstance(v, list):
            l = []
            for o in v:
                if is_raw_node(o):
                    # casts and calls _index_node(o), which will merge
                    # any stored with o
                    o = self._new_lens(o, via_key)
                    indexed = self._get_indexed_node(o)
                    if indexed:
                        o = indexed
                l.append(o)
            return l
        else:
            return v


class PlainTreeLens(TreeLens):
    """
    A simple utility TreeLens which:

    - exposes any '$uri' key via EXPOSED_URI_KEY
    - exposes the URI leaf ("uri term") via URI_TERM_KEY
    - exposes ``_via`` via VIA_KEY
    """

    EXPOSED_URI_KEY = 'resource_uri'
    URI_TERM_KEY = 'uri_term'
    VIA_KEY  = 'ref_via'

    def __init__(self, *args, **kw):
        super(PlainTreeLens, self).__init__(*args, **kw)
        uri = self.get(URI_KEY)
        if uri:
            self[self.EXPOSED_URI_KEY] = uri
            self[self.URI_TERM_KEY] = uri_term(uri)
        self[self.VIA_KEY] = self._via


def uri_term(uri):
    if '#' in uri:
        return uri.rsplit('#', 1)[-1]
    else:
        return uri.rsplit('/', 1)[-1]


