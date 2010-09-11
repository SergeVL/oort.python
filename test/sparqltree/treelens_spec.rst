########################################################################
Tree Lens Specification
########################################################################

Specification for the ``oort.sparqltree.treelens`` module.

Import specified code and inspection helpers::

    >>> from oort.sparqltree.treelens import TreeLens
    >>> from pprint import pprint


Example of Localized, Cyclic Graph
==========================================

Given the following plain tree::

    >>> onto_tree = { "ontology": {
    ...   "$uri": "tag:example.org,2009:model#",
    ...   "label": {"@en": "The Model"},
    ...   "rclass": [
    ...     { "$uri": "tag:example.org,2009:model#Item",
    ...       "isDefinedBy": { "$uri": "tag:example.org,2009:model#" },
    ...       "subClassOf": [],
    ...     },
    ...     { "$uri": "tag:example.org,2009:model#SubItem",
    ...       "isDefinedBy": {
    ...         "$uri": "tag:example.org,2009:model#",
    ...         "comment": {"@en": "Yet another model."}
    ...       },
    ...       "subClassOf": [
    ...         { "$uri": "tag:example.org,2009:model#Item" }
    ...       ],
    ...     }
    ...   ]
    ... } }
    >>>

We can create a tree lens like::

    >>> lens = TreeLens(onto_tree, 'en')

Cyclic references are merged::

    >>> lens.ontology.rclass[0].isDefinedBy is lens.ontology
    True
    >>> lens.ontology.rclass is lens.ontology.rclass[0].isDefinedBy.rclass
    True

References with additional data updates merged reference::

    >>> lens.ontology.label
    'The Model'
    >>> lens.ontology.comment
    'Yet another model.'


Core of Reverse References
==========================================

Stores all ``_via`` references::

  >>> tree = {'things': [
  ...   { "name": "Owner",
  ...       "$uri": "tag:example.org,2009:thing:1",
  ...       "owns": [
  ...         {"$uri": "tag:example.org,2009:item:1", "name": "Item 1"}
  ...       ]
  ...   },
  ...   { "name": "Borrower 1",
  ...       "$uri": "tag:example.org,2009:thing:2",
  ...       "borrows": [
  ...         {"$uri": "tag:example.org,2009:item:1", "b1": "v1"}
  ...       ]
  ...   },
  ...   { "name": "Borrower 2",
  ...       "borrows": [
  ...         {"$uri": "tag:example.org,2009:item:1", "b2": "v2"}
  ...       ]
  ...   }
  ... ] }
  >>> lens = TreeLens(tree, 'en')
  >>> item = lens.things[0].owns[0]
  >>> item is lens.things[1].borrows[0]
  True
  >>> lens.things[1].borrows[0]._via['owns'][0] is lens.things[0]
  True
  >>> [(key, [ref.name for ref in refs])
  ...   for (key, refs) in item._via.items()]
  [('borrows', ['Borrower 1', 'Borrower 2']), ('owns', ['Owner'])]



The PlainTreeLens Utility Class
==========================================

Import it::
  >>> from oort.sparqltree.treelens import PlainTreeLens

Example of flat via-references::

  >>> lens = PlainTreeLens(tree, 'en')
  >>> item = lens.things[0].owns[0]
  >>> item.ref_via.owns[0].name
  'Owner'
  >>> [it.name for it in item.ref_via.borrows]
  ['Borrower 1', 'Borrower 2']

