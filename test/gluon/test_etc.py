from __future__ import with_statement
import os
from os import path as p
import glob
from rdflib.graph import ConjunctiveGraph
from rdflib.compare import isomorphic
from oort.util.deps import json
from oort.gluon import Profile
from oort.gluon.parser import to_rdf
from oort.gluon.serializer import to_tree


etc_dir = glob.glob(p.join(p.dirname(__file__), '..','..', '..','..','*', 'etc','gluon'))[0]


def test_etc_files():
    assert p.exists(etc_dir)
    for root, dirs, fnames in os.walk(etc_dir):
        for fname in fnames:
            name, ext = p.splitext(fname)
            if ext != '.n3':
                continue
            n3_fpath = p.join(root, fname)
            expected_graph = ConjunctiveGraph()
            expected_graph.parse(n3_fpath, format='n3')
            for json_fpath in glob.glob(p.join(root, name+"*.json")):
                yield _run_case, json_fpath, expected_graph

def _run_case(json_fpath=None, expected_graph=None):
    with open(json_fpath) as f:
        json_data = json.load(f)

    graph = to_rdf(json_data)
    assert isomorphic(graph, expected_graph), "unexpected graph from <%s>" % json_fpath

    # TODO: comp. to json, with resp. without profile..
    # .. and compare with automade profile from serializer for at least "full"
    source_profile = Profile(json_data['profile'])
    lang = json_data.get('lang')
    base = json_data.get('base')

    result_tree = to_tree(graph, source_profile, lang, base)
    # TODO: where to handle the unordered nature of multiple props as JSON?
    _sort_lists(json_data)
    _sort_lists(result_tree)
    expected = _to_json(json_data)
    result = _to_json(result_tree)
    assert expected == result, "Expected:\n%s\ngot:\n %s" % (expected, result)

def _sort_lists(obj):
    if not isinstance(obj, dict):
        return
    for v in obj.values():
        if isinstance(v, list):
            # need type in key for combinations of bool, int, float..
            v.sort(key=lambda x: (x, type(x).__name__))
            for lv in v:
                _sort_lists(lv)
        else:
            _sort_lists(v)

def _to_json(tree):
    return json.dumps(tree,
            indent=4, separators=(',',': '),
            sort_keys=True, check_circular=False)

