# -*- coding: UTF-8 -*-
from __future__ import with_statement
from contextlib import closing
from rdflib.parser import Parser
from rdflib.namespace import RDF
from oort.gluon import Profile
from oort.util.deps import json
from rdflib.graph import ConjunctiveGraph
from rdflib.term import URIRef, Literal, BNode


class GluonParser(Parser):
    def __init__(self):
        super(GluonParser, self).__init__()

    def parse(self, source, sink, profile=None, **args):
        with closing(source.getByteStream()) as f:
            tree = json.load(f)
            to_rdf(tree, sink, profile)


def to_rdf(tree, graph=None, profile_source=None):
    # TODO: determine profile from profile_source, or obj or ref in tree..
    profile = Profile(profile_source or tree.get('profile'))
    lang = tree.get('lang')
    base = tree.get('base')
    all_resources = _subject_data_pairs(tree.get('linked'),
            tree.get('resources'), tree.get('nodes'))

    graph = graph or ConjunctiveGraph()
    for pfx, uri in profile.prefixes.items():
        graph.bind(pfx, uri)

    state = graph, profile, lang, base

    for s, data in all_resources:
        subject = URIRef(s, base) if s else BNode()
        _populate_graph(state, subject, data)
    return graph


def _subject_data_pairs(linked=None, *listed):
    if linked:
        for pair in linked.items():
            yield pair
    for l in listed:
        if not l:
            continue
        for data in l:
            yield data.get('$uri'), data


def _populate_graph(state, subject, data):
    graph, profile, lang, base = state
    for p, nodes in data.items():
        if p in ('$uri',):
            continue
        pred_uri = profile.uri_for_key(p)
        pred = URIRef(pred_uri)
        add_obj = lambda obj: graph.add((subject, pred, obj))
        dfn = profile.definitions.get(pred_uri)

        if not isinstance(nodes, list):
            nodes = [nodes]
        for node in nodes:
            if isinstance(node, dict) and '$list' in node:
                node = node.copy()
                pending_list = node.pop('$list')
            else:
                pending_list = None

            for obj in _generate_objects(state, dfn, node):
                add_obj(obj)

            if pending_list:
                l_subj, l_next = obj, None
                for l_node in pending_list:
                    if l_next:
                        graph.add((l_subj, RDF.rest, l_next))
                        l_subj = l_next
                    for l_obj in _generate_objects(state, None, l_node):
                        graph.add((l_subj, RDF.first, l_obj))
                        l_next = BNode()
                graph.add((l_subj, RDF.rest, RDF.nil))


def _generate_objects(state, dfn, node):
    graph, profile, lang, base = state

    if not isinstance(node, dict):
        if dfn and dfn.localized:
            node = {'@'+lang: node}
        elif dfn and dfn.datatype:
            node = {'$datatype': dfn.datatype, '$value': node}
        elif dfn and dfn.reference:
            node = {'$ref': node}
        elif dfn and dfn.symbol:
            node = {'$ref': profile.uri_for_key(node)}
        else:
            yield Literal(node)
            return

    if any(k.startswith('@') for k in node):
        for langkey, value in node.items():
            values = value if isinstance(value, list) else [value]
            for value in values:
                yield Literal(value, lang=langkey[1:])
        return

    if '$datatype' in node:
        yield Literal(node['$value'],
                datatype=profile.uri_for_key(node['$datatype']))
    elif '$ref' in node:
        yield URIRef(node['$ref'], base)
    else:
        obj = BNode()
        _populate_graph(state, obj, node)
        yield obj

