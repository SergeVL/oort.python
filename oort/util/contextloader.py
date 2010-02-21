# -*- coding: UTF-8 -*-
#=======================================================================
__metaclass__ = type
import os
from os.path import dirname, join, splitext, expanduser
from StringIO import StringIO
import logging
from rdflib import Literal, URIRef, Namespace, ConjunctiveGraph, RDFS
from oort.util.ns import DCT, FOAF
#=======================================================================


class ContextLoader:
    """
    This is a purer form of ``load_dir_if_modified``. It adds RDF contents
    from read files to separate contexts. Then one statement is added to relate
    the context to the source file, and one statement about the file's
    modification time. The pattern will be::

        <.../file.rdf#context> :source <.../file.rdf> .
        <.../file.rdf> dct:modified "2007-12-06 23:16:22.00"^^xsd:dateTime .

    The context will be replaced only if the file hasn't been read since last
    modified.

    ``symbase``
        The symbolic base prefix. If given, it will be used to conceal real file
        path, by replacing basedir (including trailing slash) with it.

    ``contextgraph``
        If given, all computed statements (about files and contexts) will be
        added to this graph instead of the ``graph`` into which read content is
        added.

    ``guessPrimaryTopic``
        TODO:
        Defaults to ``False``. If ``True`` each context will be scanned to
        determine a ``foaf:primaryTopic`` for it. That is, every subject which
        is a proper ``URIRef`` will be collected.

        If there is only one such subject, it will be used.

        Otherwise, for each of these, any one which is also an object of
        another statement will be listed as a non-suitable candidate.
        If after that any subject not also being an object remains, it will be
        used.

        If not, if only one such object remains, that will be used. Otherwise,
        for each such object, if the subjects of statements about it are
        ``BNode``:s, or there are no additional statements about them, these
        subjects are candidates. If there is more than one such candidate, no
        primaryTopic will be used.

        Failing this, each subject will be compared to the actual file path,
        according to this simple heuristic:

        1. TODO: trail segment, sans-suffix, more-than-one: step up each
           segment..


    ``purgeRemovedFiles``
        TODO: if True, should collect all visited files(!) and compare with all
        contexts. If a context exsists for a non-existing file, it will be
        removed.

    """

    def __init__(self,
            accept=None, getFormat=None, errorHandler=None,
            guessPrimaryTopic=False,
            purgeRemovedFiles=False):
        raise NotImplementedError # TODO

    def load(self, graph, basedir, symbase=None, contextgraph=None):
        raise NotImplementedError # TODO


class FolderContextLoader:
    """
     TODO: same as ContextLoader, but will treat each (customizably
     detected) directory as a separate context.

       <.../dir/#context> a :FolderContext .
       <.../dir/#context> :folder <.../dir/> .

     All RDF sources will be added as::

       <.../dir/#context> dc:source <.../dir/file_1.rdf> .

     In addition, if addFiles is set, will add each non-rdf file with::

        TODO:
        dct:hasFormat? Or <.../dir/> ..contains ..?
        <.../dir/#context> dct:hasFormat <.../dir/file_1.pdf> .
        TODO: how to differentiate alternate and enclosure?

     For all recognised files (RDF sources and optionally the rest), statements
     will be made about modification time and mime-type::

        <.../file.pdf> a foaf:Document;
            dct:modified "2007-12-06 23:16:22.00"^^xsd:dateTime;
            dc:format "application/pdf" .

     TODO: also dct:modified for <.../dir/>?

     TODO: also take "match_language_version" as dct:hasVersion?

     TODO: primaryTopicFrom... (file like "entry.rdf"?)
    """
    pass


def guess_primary_topic(graph):
    raise NotImplementedError # TODO


