#!/usr/bin/env python
from __future__ import with_statement
from oort.sparqltree.ext import json
from oort.sparqltree.access.util import discover_access


if __name__ == '__main__':

    from optparse import OptionParser
    op = OptionParser("%prog [-h] [...] <endpoint-url> <query-file or '-'>")
    op.add_option("--raw",
            action='store_true', default=False,
            help="Just dump raw SPARQL, don't do any treeification.")
    op.add_option("--pprint",
            action='store_true', default=False,
            help="Pretty print tree, instead of JSON serialization.")
    op.add_option("--time",
            action='store_true', default=False,
            help="Add measured time as comments.")

    opts, args = op.parse_args()
    if len(args) < 2:
        op.print_usage()
        op.exit()

    endpoint_url = args[0]

    fpath = args[1]
    if fpath == "-":
        import sys
        query = sys.stdin.read()
    else:
        with open(fpath) as f:
            query = f.read()

    from time import time
    start = time()

    endpoint = discover_access(endpoint_url)
    if opts.raw:
        tree = endpoint.run_query(query)
    else:
        tree = endpoint.run_query_to_tree(query)

    comment_mark = '#' if opts.pprint else '//'
    if opts.time:
        print comment_mark, "Query and tree done in %f s." % (time() - start)

    if opts.pprint:
        from pprint import pprint
        pprint(tree)
    else:
        print json.dumps(tree, indent=2, separators=(',',': '), sort_keys=True,
                check_circular=False)

    if opts.time:
        print comment_mark, "Serialization done in %f s." % (time() - start)

