########################################################################
autotree spec
########################################################################

Specification for the ``oort.sparqltree.autotree`` module.

Import specified code and inspection helpers::

    >>> from oort.sparqltree import autotree
    >>> from oort.sparqltree.autotree import _var_tree_model, _oneify
    >>> from pprint import pprint


Spec: ``_fill_nodes``
==========================================

Variables are combined into a tree via a tree model. This is created from the 
SPARQL variables, following the SparqlTree naming conventions, like this::

    >>> pprint(_var_tree_model([
    ...
    ... 'thing',
    ... 'org',
    ... 'org__1_name',
    ... 'org__feed', 'org__feed__1_id', 'org__feed__entry',
    ... 'org__1_comment'
    ... ]))
    ...
    {'org': (False,
             'org',
             {'comment': (True, 'org__1_comment', {}),
              'feed': (False,
                       'org__feed',
                       {'entry': (False, 'org__feed__entry', {}),
                        'id': (True, 'org__feed__1_id', {})}),
              'name': (True, 'org__1_name', {})}),
     'thing': (False, 'thing', {})}


Spec: ``_oneify``
==========================================

Sub-variables prefixed by ``1_`` are used to mark results as expecting only one 
value. If there are more than one but these are "language dictionaries" (
contains keys starting with '@'), these are combined into a single dictionary.

::

    >>> autotree.LAX_ONE = False

    >>> items = ['one']
    >>> pprint(_oneify(items))
    'one'

    >>> langitems = [{'@en': 'one'}, {'@sv': 'en'}]
    >>> pprint(_oneify(langitems))
    {'@en': 'one', '@sv': 'en'}

    >>> more = ['a', 'b']
    >>> _oneify(more)
    Traceback (most recent call last):
    ...
    CardinalityError: ['a', 'b']
    >>> autotree.LAX_ONE = True
    >>> _oneify(more)
    'a'


