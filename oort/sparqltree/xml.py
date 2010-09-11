# -*- coding: UTF-8 -*-
try:
    from xml.etree import cElementTree as ElementTree
except ImportError:
    from xml.etree import ElementTree
#from lxml import etree as ElementTree


def to_elementtree(tree, ET=ElementTree):
    root = ET.Element("tree")
    for k, v in tree.items():
        _add_et_node(ET, root, k, v)
    return ET.ElementTree(root)

def _add_et_node(ET, elem, key, obj):
    if key == '$uri':
        elem.set('about', obj)
    elif key == '$id':
        elem.set('nodeID', obj)
    elif isinstance(obj, list):
        for o in obj:
            _add_et_node(ET, elem, key, o)
    else:
        if isinstance(obj, basestring):
            sub = ET.SubElement(elem, key)
            sub.text = obj
        elif isinstance(obj, dict):
            if any(key.startswith('@') for key in obj):
                for k, v in obj.items():
                    sub = ET.SubElement(elem, key)
                    sub.set('xml:lang', k[1:])
                    sub.text = v
            else:
                sub = ET.SubElement(elem, key)
                for k, v in obj.items():
                    _add_et_node(ET, sub, k, v)


if __name__ == '__main__':
    person_tree = {
        "person": [
            {
                "$uri": "http://purl.org/NET/dust/foaf#self",
                "name": u"Niklas Lindström",
                "givenName": None, "surname": None,
                "comment": {"@en": "Does stuff with RDF.", "@sv": u"Gör saker med RDF."},
                "interest": [
                    {
                    "$uri": "http://en.wikipedia.org/wiki/Resource_Description_Framework",
                    "title": {"@en": "Resource Description Framework"}
                    },
                    {
                    "$uri": "http://python.org/",
                    "title": {"@en": "Python Programming Language"}
                    }
                ]
            }
        ]
    }
    import sys
    to_elementtree(person_tree).write(sys.stdout)

