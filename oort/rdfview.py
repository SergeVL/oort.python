# -*- coding: UTF-8 -*-
"""This module contains a system for creating rdf query classes in a mainly 
declarative manner. These are built by subclassing ``RdfQuery`` and creating 
class attributes by using ``Selector``:s. There are several selectors provided 
in this module to cover all regular cases of data acquisition.
"""
#=======================================================================
from itertools import chain
from types import ModuleType
import warnings
from rdflib import RDF, RDFS, Namespace, URIRef, BNode, Literal
from rdflib import ConjunctiveGraph
try: import simplejson
except ImportError: simplejson = None
from oort.util.code import contract
#=======================================================================


# TODO: deprecate THIS_QUERY and then remove this?
THIS_QUERY = object()

MODULE_SEP = ':'


#-----------------------------------------------------------------------


class Selector(object):
    __slots__ = ('predicate', '_namespace', 'filters',
                 '_subQueryMarker', '_finalSubQuery',
                 '_name', '_queryClass')

    def __init__(self, predBase=None, subQuery=None):
        self.predicate = None
        self._namespace = None
        if isinstance(predBase, Namespace) or isinstance(predBase, ModuleType):
            self._namespace = predBase
        elif isinstance(predBase, URIRef):
            self.predicate = predBase
        self._subQueryMarker = subQuery
        self._finalSubQuery = False
        self.filters = []

    @contract.state_change
    def hook_into_rdf_query(self, name, queryClass):
        self._name = name
        self._queryClass = queryClass
        if not self._namespace:
            self._namespace = queryClass._namespace
        if not self.predicate and self._namespace:
            if isinstance(self._namespace, ModuleType):
                self.predicate = getattr(self._namespace, name)
            else:
                self.predicate = self._namespace[name]
        # TODO: not used since e.g. the selector decorator uses no predicate
        #if not self.predicate:
        #    raise ValueError(
        #            "Could not determine predicate for Selector %s" % self)

    def get_sub_query(self):
        final = self._finalSubQuery
        if final is False:
            marker = self._subQueryMarker
            final = marker
            if isinstance(marker, basestring):
                if MODULE_SEP in marker:
                    module, marker = marker.split(MODULE_SEP)
                else:
                    module = self._queryClass.__module__
                final = __import__(module, fromlist=['']).__dict__[marker]
            elif marker is THIS_QUERY:
                final = self._queryClass
            self._finalSubQuery = final
        return final

    def __get__(self, rdfQueryInstance, rdfQueryOwnerClass=None):
        if not rdfQueryInstance:
            return self
        prep = rdfQueryInstance._preparedSelects[self._name]
        if not prep.hasRun:
            result = self.retreive_result(rdfQueryInstance, prep.selectArgs)
            for fltr in self.filters:
                result = fltr(result)
            prep.hasRun = True
            prep.result = result
        return prep.result

    @contract.default_method
    def retreive_result(self, rdfQueryInstance, selectArgs):
        result = self._process_for_subqueries(
                rdfQueryInstance,
                self.select(*selectArgs),
                *selectArgs[:2]
            )
        return result

    def _process_for_subqueries(self, rdfQueryInstance,
            rawresults, graph, lang):
        returnList = isinstance(rawresults, list)
        if not rawresults:
            if returnList: return []
            else: return None

        subQuery = self.get_sub_query()
        if not subQuery:
            return rawresults
        else:
            # TODO: using THIS_QUERY (and no execCache?) may currently cause
            # infinite loops..? But things are more lazy now; perhaps not..
            run_query = query_or_cached(subQuery, rdfQueryInstance._execCache)
            if returnList:
                return [run_query(graph, lang, uri) for uri in rawresults]
            else:
                return run_query(graph, lang, rawresults)

    @contract.template_method
    def select(self, graph, lang, subject):
        raise NotImplementedError
        return None or []

    @contract.default_method
    def back_to_graph(self, graph, subject, value):
        pass

    def viewed_as(self, subQuery):
        self._subQueryMarker = subQuery
        return self

    def __rshift__(self, subQuery):
        return self.viewed_as(subQuery)

    def add_filter(self, fltr):
        self.filters.append(fltr)

    def __or__(self, fltr):
        self.add_filter(fltr)
        return self

    def __set__(self, rdfQueryInstance, value):
        prep = rdfQueryInstance._preparedSelects[self._name]
        lang = rdfQueryInstance._lang
        sub = self.get_sub_query()
        if isinstance(value, list):
            value = [self.type_raw_value(val, lang) for val in value]
        else:
            value = self.type_raw_value(value, lang)
        if sub:
            if isinstance(value, list):
                prep.result = [sub.from_dict(val, lang, BNode())
                                for val in value]
            else:
                prep.result = sub.from_dict(value, lang, BNode())
        else:
            prep.result = value
            prep.hasRun = True

    @contract.default_method
    def type_raw_value(self, value, lang):
        # TODO: need more clever type mapping. also, allow {'_uri': ".." } to be resource?
        if isinstance(value, basestring):
            value = Literal(value)
        return value


class PreparedSelect(object):
    __slots__ = ('selectArgs', 'result', 'hasRun')
    def __init__(self, graph, lang, subject):
        self.selectArgs = (graph, lang, subject)
        self.result = None
        self.hasRun = False # TODO: make configurable?


class _rdf_query_meta(type):
    def __init__(cls, clsName, bases, clsDict):
        super(_rdf_query_meta, cls).__init__(clsName, bases, clsDict)

        cls._selectors = selectors = {}
        for base in bases:
            if hasattr(base, '_selectors'):
                selectors.update(base._selectors)

        rdfBase = clsDict.get('_rdfbase_')
        if not rdfBase:
            for base in bases:
                if hasattr(base, '_rdfbase_'):
                    rdfBase = base._rdfbase_
                    break
        if isinstance(rdfBase, Namespace):
            cls._namespace = rdfBase
            if not clsDict.get('RDF_TYPE'):
                cls.RDF_TYPE = rdfBase[clsName]
        else:
            cls._namespace = None # TODO: pick from type?

        for key, value in clsDict.items():
            if isinstance(value, Selector):
                value.hook_into_rdf_query(key, cls)
                selectors[key] = value


class RdfQuery(object):
    __metaclass__ = _rdf_query_meta

    RDF_TYPE = RDFS.Resource

    # TODO: test use of execCache propertly (it seems to work though)

    def __init__(self, graph, lang, subject, execCache=None):
        self._graph = graph
        self._subject = subject
        self._lang = lang
        self._preparedSelects = self._make_prepare_selects()
        self._execCache = execCache

    def _make_prepare_selects(self):
        prepareds = {}
        graph, lang, subject = self._graph, self._lang, self._subject
        for name, selector in self._selectors.items():
            if not subject:
                # FIXME: happens when subject is a string/Literal - wrong in 
                # itself! Remove or signal error? As it is, it leads to 
                # illegible errors further down!
                # Also, why not: if subject == u'':
                #setattr(self, name, None) # TODO:removed; see this fixme
                continue
            prep = PreparedSelect(graph, lang, subject)
            prepareds[name] = prep
        return prepareds

    def __str__(self):
        return str(self._subject)

    def __eq__(self, other):
        if isinstance(other, RdfQuery):
            return self._subject == other._subject
        else:
            return self._subject == other

    @classmethod
    def bound_with(cls, subject, lang=None):
        def bound_query(graph, _lang, _subject):
            return cls(graph, lang or _lang, subject)
        bound_query.query = cls
        bound_query.__name__ = cls.__name__
        return bound_query

    @classmethod
    def from_dict(cls, data, lang, subject):
        graph = ConjunctiveGraph()
        query = cls(graph, lang, subject)
        for k, v in data.items():
            setattr(query, k, v)
        return query

    @classmethod
    def find_by(cls, graph, lang, execCache=None, **kwargs):
        assert len(kwargs) == 1
        name, value = kwargs.items()[0]
        predicate = cls._selectors[name].predicate
        for subject in graph.subjects(predicate, value):
            yield query_or_cached(cls, execCache)(graph, lang, subject)

    @property
    def uri(self):
        return self._subject

    def get_selected_value(self, name):
        return self._preparedSelects[name].result

    def to_graph(self, lgraph=None):
        subject = self._subject or BNode() # FIXME: is this ok?
        if not subject: return # FIXME, see fixme in __init__

        lgraph = lgraph or ConjunctiveGraph()

        for t in self._graph.objects(subject, RDF.type):
            lgraph.add((subject, RDF.type, t))

        for selector in self._selectors.values():
            value = selector.__get__(self)
            if not value:
                continue
            selector.back_to_graph(lgraph, subject, value)

        # FIXME: why is this happening; how can we prevent it?
        for t in lgraph:
            if None in t: lgraph.remove(t)
        return lgraph

    def to_rdf(self):
        return self.to_graph().serialize(format='pretty-xml')

    def to_dict(self, keepSubject=False):
        d = {}
        if keepSubject:
            # TODO: sync with new property 'uri'
            subjectKey = isinstance(keepSubject, str) and keepSubject or 'resource'
            subj = self._subject
            if subj and not isinstance(subj, BNode):
                d[subjectKey] = self._subject

        for selector in self._selectors.values():
            name = selector._name
            value = selector.__get__(self)
            if not value:
                continue
            if isinstance(value, dict):
                d[name] = dict([(key, self.__dict_convert(val, keepSubject))
                            for key, val in value.items()])
            elif hasattr(value, '__iter__'):
                d[name] = [self.__dict_convert(val, keepSubject)
                            for val in value]
            else:
                d[name] = self.__dict_convert(value, keepSubject)
            # TODO: handle xml literals
        return d

    def __dict_convert(self, value, keepSubject):
        if isinstance(value, RdfQuery):
            return value.to_dict(keepSubject)
        else:
            return unicode(value) # TODO: simple type conversions?

    def to_json(self, keepSubject=False):
        if simplejson:
            return simplejson.dumps(self.to_dict(keepSubject))
        else:
            raise NotImplementedError


#-----------------------------------------------------------------------


# Is the use of weakref fine enough (reasonably needed to avoid cyclic
# references and hence possible memory leaks)?
# See: <http://docs.python.org/lib/module-weakref.html>
from weakref import WeakValueDictionary

class ExecCache(object):
    """
    This is a query execution cache which reuses results for the same query,
    subject and language, avoiding multiple instances of the same query when
    given the same subject and lang.
    """
    def __init__(self):
        self.cache = WeakValueDictionary()
    def __call__(self, query, graph, lang, subject):
        cache = self.cache
        key = (id(query), unicode(subject), lang)
        #key = (query, subject, lang)
        result = cache.get(key)
        if not result:
            result = query(graph, lang, subject, self)
            cache[key] = result
        return result


def query_or_cached(rdfQuery, execCache):
    if execCache:
        def run_query(graph, lang, uri):
            return execCache(rdfQuery, graph, lang, uri)
        return run_query
    else:
        return rdfQuery


def run_queries(queries, graph, lang, subject):
    execCache = ExecCache()
    for query in queries:
        yield execCache(query, graph, lang, subject)


#-----------------------------------------------------------------------


class Filter(object):
    def __init__(self, func):
        self.func = func
    def __call__(self, items):
        return filter(self.func, items)


class Sorter(object):
    def __init__(self, obj=None, reverse=False, ignoreCase=False):
        if callable(obj):
            self.attr = None
            self.func = obj
        else:
            self.attr = obj
            self.func = None
        self.reverse = reverse
        self.ignoreCase = ignoreCase
    def __call__(self, items):
        copy = items[:]
        copy.sort(self.sort)
        if self.reverse:
            copy.reverse()
        return copy
    def sort(self, r1, r2):
        attr = self.attr
        func = self.func
        if attr:
            v1, v2 = getattr(r1, attr, r1), getattr(r2, attr, r2)
        elif func:
            v1, v2 = func(r1), func(r2)
        else:
            v1, v2 = r1, r2
        if self.ignoreCase:
            v1, v2 = v1.lower(), v2.lower()
        return cmp(v1, v2)


#-----------------------------------------------------------------------


# TODO: totally untested!
#   - use: TypeSwitch(persons=Person, values=Literal)
#   - a subclass of RdfQuery? Or affect selector..? Reasonably yes..
#   - should adapt to if stuff is a list or one thing (one or each)
#       - how about localized?
#   - also should be used as list *or*:
#       - obj.switchedstuff.persons
#def type_switch(typeSelectors, default):
#    rdfType = graph.value(resource, RDF.type, None, any=True)
#    def select(graph, lang, resource, **kwargs):
#        query = typeSelectors.get(rdfType, default)
#        return query(graph, lang, resource, **kwargs)
#    return select



def back_from_value(graph, subject, predicate, value):
        if isinstance(value, RdfQuery):
            graph.add((subject, predicate, value._subject))
            value.to_graph(graph)
        else:
            if not isinstance(value, list): # TODO: fix this
                graph.add((subject, predicate, value))


class UnarySelector(Selector):
    def back_to_graph(self, graph, subject, value):
        back_from_value(graph, subject, self.predicate, value)

class EachSelector(Selector):
    def back_to_graph(self, graph, subject, values):
        for value in values:
            back_from_value(graph, subject, self.predicate, value)


class one(UnarySelector):
    def select(self, graph, lang, subject):
        return graph.value(subject, self.predicate, None, any=True)


class each(EachSelector):
    def select(self, graph, lang, subject):
        return list(graph.objects(subject, self.predicate))


class one_where_self_is(Selector):
    def select(self, graph, lang, subject):
        return graph.value(None, self.predicate, subject, any=True)

    def back_to_graph(self, graph, subject, value):
        back_from_value(graph, value._subject, self.predicate, subject)


class each_where_self_is(Selector):
    def select(self, graph, lang, subject):
        return list(graph.subjects(self.predicate, subject))

    def back_to_graph(self, graph, subject, values):
        for value in values:
            back_from_value(graph, value._subject, self.predicate, subject)


class collection(Selector):
    def __init__(self, predBase=None, subQuery=None, multiple=False):
        Selector.__init__(self, predBase, subQuery)
        self.multiple = multiple

    def select(self, graph, lang, subject):
        if self.multiple:
            allItems = [graph.items(res)
                        for res in graph.objects(subject, self.predicate)]
            return list(chain(*allItems))
        else:
            return list(graph.items(
                    graph.value(subject, self.predicate, None, any=True)
                ))

    def back_to_graph(self, graph, subject, values):
        if not values:
            graph.add((subject, self.predicate, RDF.nil))
            return
        bnode = BNode()
        graph.add((subject, self.predicate, bnode))
        for value in values:
            back_from_value(graph, bnode, RDF.first, value)
            newBnode = BNode()
            graph.add((bnode, RDF.rest, newBnode))
            bnode = newBnode
        graph.add((bnode, RDF.rest, RDF.nil))


class TypeLocalized(Selector):
    def type_raw_value(self, value, lang):
        if isinstance(value, basestring):
            value = Literal(value, lang)
        return value

class localized(TypeLocalized, UnarySelector):
    def select(self, graph, lang, subject):
        first = None
        for value in graph.objects(subject, self.predicate):
            if not first: first = value
            if getattr(value, 'language', None) == lang:
                return value
        return first


# TODO: This is a hackish solution; see also below (transparently using datatype).
#       It also reduces the literal, making it irreversible (should store original value!).
try:
    from oort.util._genshifilters import language_filtered_xml
except ImportError, e:
    warnings.warn("Could not import _genshifilters. Error was: %r. The selector 'localized_xml' will not be available." % e)
else:
    class localized_xml(UnarySelector):
        """This selector removes any elements with an xml:lang other than the 
        current language. It also supports the never standardized 'rdf-wrapper' in 
        XML Literals, who are removed from the output.

        Important! This is currently tied to the Genshi Templating System, and may 
        not work as expected in all cases."""

        def select(self, graph, lang, subject):
            return language_filtered_xml(
                    graph.objects(subject, self.predicate), lang)

        def type_raw_value(self, value, lang):
            if isinstance(value, basestring):
                value = Literal(value, datatype=RDF.XMLLiteral)
            return value

class i18n_dict(Selector):
    def select(self, graph, lang, subject):
        valueDict = {}
        for value in graph.objects(subject, self.predicate):
            valueDict[value.language] = value
        return valueDict

    def back_to_graph(self, graph, subject, value):
        for lang, text in value.items():
            graph.add((subject, self.predicate, Literal(text, lang=lang)))


class each_localized(TypeLocalized, EachSelector):
    def select(self, graph, lang, subject):
        return [ value for value in graph.objects(subject, self.predicate)
                 if value.language == lang ]


#-----------------------------------------------------------------------


# TODO: Though "widely used" (by me), I think this was a little premature.
# There seems little use for this that a regular property can't do (getting the
# graph, lang and subject from self -- where needed). Perhaps I should include
# a memoized codeutil so it's easy to create lazily calculated bigger things.
#
# Even worse, this "utility" bypasses _process_for_subqueries, which is
# intricate and very close to the implementation. And this is the only reason
# retreive_result is marked as a "default_method"; it should reasonably be
# private.
#
class selector(Selector):
    "Use as decorator for methods of an RdfQuery subclass to convert them to selectors."
    def __init__(self, func):
        super(selector, self).__init__(None)
        self.func = func
    def retreive_result(self, rdfQueryInstance, selectArgs):
        return self.func(rdfQueryInstance, *selectArgs)
    @classmethod
    def filtered_by(cls, *filters):
        def decorator(func):
            sel = cls(func)
            for fltr in filters:
                sel.add_filter(fltr)
            return sel
        return decorator


#-----------------------------------------------------------------------
# TODO: consider returning ElementTree data for XML Literals. And if so, also
# filtered on u'{http://www.w3.org/XML/1998/namespace}lang' (keep if none) for localized.

# TODO: also consider checking datatype and coercing (at least) these:
# Use: rdflib.Literal.castPythonToLiteral
# See: rdflib.sparql.sparqlOperators.getLiteralValue(v)
# See: <http://en.wikipedia.org/wiki/RDFLib#RDF_Literal_Support>
# - NOTE: Isn't this done automatically by rdflib now? I believe so.


#-----------------------------------------------------------------------


class QueryContext(object):
    """
    A query context, used to provide a managed context for query execution.

    Initalized with:

    -   graph
    -   language or getter for language
    -   a set of queries or a modules containing queries
        Accessible as attributes on the context or via view_for using RDF_TYPE

    """

    def __init__(self, graph, langobj, queries=None, query_modules=None):
        self._graph = graph
        self._execCache = ExecCache()

        if callable(langobj):
            get_lang = langobj
        else:
            def get_lang(): return langobj
        self._get_lang = get_lang

        self._querydict = querydict = {}
        if queries:
            for query in queries:
                querydict[query.__name__] = query
        if query_modules:
            for module in query_modules:
                for name, obj in module.__dict__.items():
                    if isinstance(obj, type) and issubclass(obj, RdfQuery):
                        querydict[name] = obj

        self._queryTypeMap = {}
        for query in querydict.values():
            self._queryTypeMap[query.RDF_TYPE] = query

    def __getattr__(self, name):
        try:
            query = self._querydict[name]
            return self._prepared_query(query)
        except KeyError:
            raise AttributeError("%s has no attribute '%s'" % (self, name))

    def view_for(self, uriref):
        for typeref in self._graph.objects(uriref, RDF.type):
            query = self._queryTypeMap.get(typeref)
            if query:
                return self._prepared_query(query)(uriref)
        raise KeyError("%s has no query for type '%s'" % (self, uriref))

    def _prepared_query(self, query):
        return self.PreparedQuery(self, query)

    class PreparedQuery(object):
        __slots__ = ('query', 'context')

        def __init__(self, context, query):
            self.context = context
            self.query = query

        def __call__(self, subject):
            cx = self.context
            return cx._execCache(self.query, cx._graph, cx._get_lang(), subject)

        def find_all(self):
            cx = self.context
            for subject in cx._graph.subjects(RDF.type, self.query.RDF_TYPE):
                yield cx.view_for(subject)

        def find_by(self, **kwargs):
            cx = self.context
            return self.query.find_by(cx._graph, cx._get_lang(),
                    execCache=cx._execCache, **kwargs)


