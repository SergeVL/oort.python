========================================================================
Oort
========================================================================


Oort is a a Python_-based toolkit for accessing RDF_ graphs as plain objects.

It uses RDFLib_ for the heavy lifting.

.. _RDF: http://www.rdfabout.net
.. _Python: http://python.org
.. _RDFLib: http://rdflib.net


Overview
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``oort.gluon``
    An implementation of the Gluon JSON format for RDF.

``oort.sparqltree``
    Automatic treeification of SPARQL query results.

``oort.rdfview``
    Contains classes and functions used for defining RDF queries and selectors, 
    i.e. declarations used to pick properties and associated sub-queries from a
    chosen resource (similar to how many ORM-toolkits work).

``oort.util.queries``
    Some basic base ``RdfQuery`` subtypes for common use (e.g. getting at 
    localized annotation properties such as ``rdfs:label`` and similar).

``oort.util.graphs``
    A collection of basic "filesystem-to-graph" utilities.


Modules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Gluon
------------------------------------------------------------------------

See the `Oort website`_ for specification and examples.


SparqlTree
------------------------------------------------------------------------

An implementation of the SparqlTree mechanism for writing and digesting
SPARQL queries into JSON.

A "SPARQL tree" is a processed SPARQL query result which combines bound
variables into trees of data. It uses regular SPARQL queries with variables
named according to a special convention.


RDFView
------------------------------------------------------------------------

By subclassing ``oort.rdfview.RdfQuery`` and adding attributes which are 
instances of one of the Selector subclasses from that package, you define a set 
of rdf properties which are to be retrieved about a given subject (from a given 
graph, in a given language). The selectors are given a ``URIRef`` which 
determines the property. Or a ``Namespace``, in which case the name of the 
attribute will be used.

These are some of the predefined classes from ``oort.util.queries``::

    class Typed(RdfQuery):
        rdfType = one(RDF.type)

    class Labelled(RdfQuery):
        label = localized(RDFS)

    class Annotated(Labelled):
        comment = localized(RDFS)

    class Resource(Annotated, Typed):
        pass

Selectors can also be given ``RdfQuery`` types (or names of types, to enable 
e.g. cyclic references) which are used to describe their selected resources 
recursively. Use like this::

    SIOC = Namespace("http://rdfs.org/sioc/ns#")

    class Item(Annotated):
        _rdfbase_ = SIOC # sets default namespace base for this RdfQuery
        name = localized()
        description = localized()
        seeAlso = each(RDFS) >> Annotated

The overloaded ``>>`` is just sugar for::

        seeAlso = each(RDFS).viewed_as(Annotated)

Predefined selectors in ``oort.rdfview`` are: ``one``, ``each``, 
``one_where_self_is``, ``each_where_self_is``, ``collection``, ``localized``, 
``i18n_dict``, ``each_localized`` and ``localized_xml``.

RdfQueries are either directly instantiated with an RDFLib ``Graph`` instance, 
language (string) and ``URIRef`` instance, or used via ``QueryContext``, which 
facilitates this and other things.


More
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Se more examples (and test source code) at the `Oort website`_.

.. _`Oort website`: http://oort.to

The latest development version can be installed from the
`Oort SVN Trunk <http://oort.googlecode.com/svn/Oort/trunk#egg=Oort-dev>`_.


