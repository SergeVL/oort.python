from rdflib.graph import ConjunctiveGraph
from oort.util.deps import json
from oort.gluon import Profile
from oort.gluon.parser import to_rdf
from oort.gluon.serializer import to_tree


if __name__ == '__main__':
    from sys import argv, stdin
    args = argv[1:]
    fname = args.pop(0) if args else ""
    profile_fname = args.pop(0) if args else None
    lang = args.pop(0) if args else None

    if not fname or fname.endswith('.json'):
        infile = open(fname) if fname else stdin
        tree = json.loads(
                "".join(l for l in infile if not l.strip().startswith('//')))
        graph = to_rdf(tree)
        print graph.serialize(format="n3")
    else:
        graph = ConjunctiveGraph()
        from rdfextras.tools.pathutils import guess_format
        graph.parse(fname, format=guess_format(fname))
        profile = Profile(json.load(open(profile_fname))
                ) if profile_fname else None
        tree = to_tree(graph, profile, lang)
        print json.dumps(tree, indent=4, separators=(',',': '), sort_keys=True,
                check_circular=False)

