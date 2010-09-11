# -*- coding: UTF-8 -*-
from rdflib.serializer import Serializer
from rdflib.namespace import RDF, XSD
from oort.gluon import Profile
from oort.util.deps import json
from rdflib.term import URIRef, Literal, BNode


PLAIN_LITERAL_TYPES = set(
        [XSD.integer, XSD.float, XSD.boolean])


class GluonSerializer(Serializer):
    def __init__(self, store):
        super(GluonSerializer, self).__init__(store)

    def serialize(self, stream, base=None, encoding=None, **args):
        raise NotImplementedError # TODO (+ profile kw..)


class State(object):
    def __init__(self, graph, profile, lang, base, token_for_uri):
        self.graph = graph
        self.profile = profile
        self.lang = lang
        self.base = base
        self.token_for_uri = token_for_uri


# TODO: reuse rdflib things, e.g. RecursiveSerializer, used-qname-checking..
def to_tree(graph, profile=None, lang=None, base=None):

    # FIXME: make sure to use/update prefixes for created curies!
    # .. that is, reasonably(?) create profile if none exists (from graph
    # prefixes), and extend(?) token_for_uri to handle qnames (skip _qname)..
    # .. and also, check which prefixes are actually used..
    if not profile:
        prefixes = dict((pfx, text(ns))
                for (pfx, ns) in graph.namespaces() if pfx)
        profile_data = {'prefix': prefixes}
        token_for_uri = lambda uri: _qname(graph, uri)
    else:
        profile_data = profile.source
        token_for_uri = lambda uri: profile.token_for_uri(text(uri)) or (
                _qname(graph, uri))

    tree = {'profile': profile_data}
    if lang: tree['lang'] = lang
    if base: tree['base'] = base

    # TODO: Switch to "resources" if configured or non-reffed bnodes occur?
    #   TODO: PROPOSAL: use a profile config for identifier key representation:
    #       - "profile":{"identifier": ..., ...}
    #       - AS_KEY (use linked), PFX:"$", PFX:"_"
    #       - what about "reference":true vs. special "ref" (opt. prefixes as per above..)
    # The "resources" or "linked"+(opt)"nodes" needs to be specified..
    linked = {}
    nodes = []
    use_linked_and_nodes = profile and profile.definitions

    state = State(graph, profile, lang, base, token_for_uri)

    for s in set(graph.subjects()):
        current = _subject_to_node(state, s)
        s_value = resolve(text(s), base)
        if isinstance(s, URIRef):
            if use_linked_and_nodes:
                linked[s_value] = current
            else:
                current['$uri'] = s_value
                nodes.append(current)
        else: # only unreferenced..
            if not any(graph.subjects(None, s)):
                nodes.append(current)

    if use_linked_and_nodes:
        tree['linked'] = linked
        if nodes:
            tree['nodes'] = nodes
    else:
        tree['resources'] = nodes

    return tree

def _subject_to_node(state, s):
    current = {}
    p_objs = {}
    for p, o in state.graph.predicate_objects(s):
        objs = p_objs.setdefault(p, [])
        objs.append(o)
    for p, objs in p_objs.items():
        p_key, node = _key_and_node(state, p, objs)
        current[p_key] = node

    return current

def _key_and_node(state, p, objs):
    p_key, many, repr_value = _handles_for_property(state, p, objs)
    node = None
    if _has_lang_literal(objs):
        node = {}
        lang_many = False
        for o in objs:
            if not isinstance(o, Literal) or not o.language:
                node = None
                break
            lang_key = '@'+o.language
            if lang_key in node:
                lang_many = True
            v = repr_value(o)
            if isinstance(v, dict):
                if lang_many:
                    cur_v = node.get(lang_key) or []
                    if not isinstance(cur_v, list):
                        node[lang_key] = cur_v = [cur_v]
                    cur_v.append(v[lang_key])
                else:
                    node.update(v)
    if not node:
        if not many:
            node = repr_value(objs[0])
        else:
            node = [repr_value(o) for o in objs]
    return p_key, node

def _handles_for_property(state, p, objs):
    repr_value = lambda o: _to_raw_value(state, o)
    dfn = state.profile.definitions.get(text(p)) if state.profile else None
    if dfn:
        p_key = dfn.token
        if dfn.many is None:
            many = not _has_one_literal(objs)
        else:
            many = dfn.many

        if dfn.reference:
            repr_value = lambda o: resolve(text(o), state.base)
        elif dfn.symbol:
            repr_value = lambda o: state.token_for_uri(o)
        elif dfn.localized:
            repr_value = (lambda o:
                    text(o) if o.language == state.lang
                    else _to_raw_value(state, o))
        elif dfn.datatype:
            repr_value = (lambda o:
                    text(o)
                    if text(o.datatype) == dfn.datatype_uri
                    else _to_raw_value(state, o))
    else:
        p_key = state.token_for_uri(p)
        many = not _has_one_literal(objs)

    return p_key, many, repr_value


def _to_raw_value(state, o):
    coll = _to_collection(state, o)
    if coll:
        return coll
    elif isinstance(o, BNode):
        return _subject_to_node(state, o)
    elif isinstance(o, URIRef):
        return {'$ref': resolve(text(o), state.base)}
    else:
        v = text(o)
        if o.language:
            return {'@'+o.language: v}
        elif o.datatype:
            if o.datatype in PLAIN_LITERAL_TYPES:
                return o.toPython()
            return {'$datatype': state.token_for_uri(o.datatype), '$value': v}
        else:
            return v

def _to_collection(state, subj):
    graph = state.graph
    node = None
    #from rdflib.graph import Seq
    #rtypes = list(graph.objects(subj, RDF.type))
    #if any(t in rtypes for t in (RDF.Seq, RDF.Bag, RDF.Alt)):
    #    node = dict([_key_and_node(state, RDF.type, rtypes)])
    #    node['$list'] = list(Seq(graph, subj))
    #else:
    if (subj, RDF.first, None) in graph:
        node = {'$list': list(_to_raw_value(state, o)
                                for o in graph.items(subj))}
    return node


def _qname(graph, uri):
    pfx, ns, lname = graph.compute_qname(uri)
    return "%s:%s" % (pfx, lname)

def _has_lang_literal(items):
    return any(item.language for item in items if isinstance(item, Literal))

def _has_one_literal(items):
    return (len(items) == 1 and isinstance(items[0], Literal))


def text(value, encoding='utf-8'):
    return value.encode(encoding)

def resolve(uri, base):
    return uri[len(base):] if base and uri.startswith(base) else uri

