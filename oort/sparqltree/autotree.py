from itertools import groupby


# TODO: BNODE_KEY used to be '$bnode', but this *should* be more compliant with
# "de-facto json-with-refs"(?). All that is left is to "stdize" uri, lang and
# datatype..
URI_KEY = '$uri'
BNODE_KEY = '$id'
DATATYPE_KEY = '$datatype'
VALUE_KEY = '$value'
LANG_TAG = '@'

LAX_ONE = True


XSD = "http://www.w3.org/2001/XMLSchema#"
# NOTE: Only convert deterministically..
TYPE_CONVERSION = {
    XSD+'boolean': lambda v: (v != "false" and v == "true"),
    XSD+'integer': int,
    XSD+'float': float,
}


def treeify_results(results, root={}):
    """
    Takes an object isomorphic to a parsed SPARQL JSON result and creates a
    tree object (suitable for JSON serialization).
    """
    varmodel = _var_tree_model(results['head']['vars'])
    bindings = results["results"]["bindings"]
    root = root or {}
    _fill_nodes(varmodel, root, bindings)
    return root


def _var_tree_model(rqvars, sep="__"):
    vartree = {}
    for var in sorted(rqvars):
        currtree = vartree
        for key in var.split(sep):
            use_one = False
            if key.startswith('1_'):
                use_one = True
                key = key[2:]
            currtree = currtree.setdefault(key, (use_one, var, {}))[-1]
    return vartree


def _fill_nodes(varmodel, tree, bindings):
    """Computing a tree model from var names following a given convention."""
    for key, namedmodel in varmodel.items():
        use_one, varname, subvarmodel = namedmodel
        nodes = [] #tree.setdefault(key, [])
        for keybinding, gbindings in groupby(bindings, lambda b: b.get(varname)):
            if not keybinding:
                continue
            node = _make_node(keybinding)
            # TODO:Ok? Duplicates (due to join combinations) may occur in res,
            # but should be filtered here by not continuing if keyed value
            # exists in an already added node..
            if any(n for n in nodes if n == node or
                    isinstance(node, dict) and isinstance(n, dict) and
                    [n.get(k) for k in node] == node.values()):
                continue
            nodes.append(node)
            # NOTE: if node is "literal", subvarmodel should be falsy
            if subvarmodel:
                _fill_nodes(subvarmodel, node, list(gbindings))
        tree[key] = _oneify(nodes) if use_one else nodes
    return tree


def _make_node(binding):
    node = {}
    vtype = binding['type']
    value = binding['value']
    if vtype == 'uri':
        node[URI_KEY] = value
    elif vtype == 'bnode':
        node[BNODE_KEY] = value
    elif vtype == 'literal':
        lang = binding.get('xml:lang')
        if lang:
            node[LANG_TAG+lang] = value
        else:
            node = value
    elif vtype == 'typed-literal':
        datatype = binding.get('datatype')
        converter = TYPE_CONVERSION.get(datatype)
        if converter:
            node = converter(value)
        else:
            node[VALUE_KEY] = value
            node[DATATYPE_KEY] = datatype
    else:
        raise TypeError("Unknown value type: %s" % vtype)
    return node


def _oneify(nodes, lax_one=None):
    if lax_one is None:
        lax_one = LAX_ONE
    if not nodes:
        return None
    first = nodes[0]
    if is_lang_node(first):
        # TODO: warn if a node isn't a dict:
        # "value was expected to be a lang dict but was %r."
        first = dict(
                node.items()[0] if isinstance(node, dict) else ('', node)
                for node in nodes if node
            )
    elif not lax_one and len(nodes) > 1:
        raise CardinalityError(nodes)
    return first


def is_lang_node(obj):
    return isinstance(obj, dict) and any(
                key.startswith(LANG_TAG) for key in obj)

def is_datatype_node(obj):
    return isinstance(obj, dict) and DATATYPE_KEY in obj

def is_literal(obj):
    return not isinstance(obj, dict) or is_datatype_node(obj) or is_lang_node(obj)

def is_resource(obj):
    #return isinstance(obj, dict) and (URI_KEY in obj or BNODE_KEY in obj)
    # FIXME: currently we do allow for "pure" anonymous nodes (w/o BNODE_KEY:s)
    # but this check is expensive(!):
    return not is_literal(obj)


class CardinalityError(ValueError):
    pass


