from nose.tools import assert_equals
from rdflib import (ConjunctiveGraph as Graph, URIRef, Literal, BNode,
        Namespace, RDF)
from oort.rdfview import (RdfQuery, one, each, one_where_self_is,
        each_where_self_is, collection, localized, i18n_dict, each_localized,
        localized_xml, Sorter, Filter, run_queries, THIS_QUERY, selector)
from oort.util import queries


from oort.test.helper import siblingpath

def _create_test_graph(filename='testdata.n3'):
    testfilepath = siblingpath(__file__, filename)
    graph = Graph()
    graph.load(open(testfilepath), format='n3')
    return graph
# TODO: in a setup (but once for entire test module?)
testgraph = _create_test_graph()



def assert_all_equals(results, expected):
    assert set(unicode(v) for v in results) == set(expected)

def assert_contains(graph, query):
    for spo in query.to_graph():
        assert spo in graph


#---------------------------------------
# TODO: test some with rdflib.RDFS to make sure module namespaces work.


T = Namespace("http://example.org/oort/test#")

itemX = URIRef('tag:oort.to,2006:test:item:x')
en, sv = 'en', 'sv'


class Part(RdfQuery):
    name = one(T)

class Item(Part):
    title = localized(T)
    relations = each(T.relation) >> THIS_QUERY
    unaryRelation = one(T) >> Part
    partlist = collection(T) >> Part
    multiple_partlist = collection(multiple=True) >> Part
    xmlData = localized_xml(T)
    titleLang = i18n_dict(T['title'])
    labels = each_localized(T.label)


class TestItem:

    def setup(self):
        self.item = Item(testgraph, en, itemX)

    def test_one(self):
        assert self.item.name == u'Item X'

    def test_one_relation(self):
        assert self.item.unaryRelation.name == u'One Relation'

    def test_each(self):
        relItemNames = [item.name for item in self.item.relations]
        assert set(relItemNames) == set(["Related 1", "Related 2"])

    def test_collection(self):
        collItems = [item.name for item in self.item.partlist]
        assert set(collItems) == set(["Part 1", "Part 2"])

    def test_collection_multiple(self):
        collItems = [item.name for item in self.item.multiple_partlist]
        assert set(collItems) == set(["Part 1", "Part 2"])

    def test_i18n_dict(self):
        titleLangs = self.item.titleLang
        assert set(titleLangs.keys()) == set(['en', 'sv'])
        assert_all_equals(titleLangs.values(), [u'Example Item', u'Exempelsak'])


def test_localized():
    for l, v in [(en, u'Example Item'), (sv, u'Exempelsak')]:
        yield assert_equals, Item(testgraph, l, itemX).title, Literal(v, l)

def test_each_localized():
    assert_all_equals(Item(testgraph, en, itemX).labels, [u'En', u'eN'])
    assert_all_equals(Item(testgraph, sv, itemX).labels, [u'Sv', u'sV'])


class RichItem(Item):
    xmlData = localized_xml(T)

def test_localized_xml():
    for l, v in [(en, u'XML Data'), (sv, u'XML-data')]:
        treeData = list(RichItem(testgraph, l, itemX).xmlData)
        ok = False
        for stream in treeData:
            for item in stream:
                if v in item: ok = True
        assert ok


class Creation(RdfQuery):
    createdBy = one_where_self_is(T.creation) >> Part

def test_one_where_self_is():
    creation = Creation(testgraph, en, itemX)
    assert creation.createdBy.name == "Creator"
    assert_contains(testgraph, creation)


class Owner(RdfQuery):
    owns = each_where_self_is(T.owner) >> Part

def test_each_where_self_is():
    owner = Owner(testgraph, en, itemX)
    owned = [part.name for part in owner.owns]
    assert set(owned) == set(["Part A", "Part B"])
    assert_contains(testgraph, owner)


def test_to_json():
    json = Item(testgraph, en, itemX).to_json()
    d = eval(json)
    # TODO: inspect!


def test_to_graph():
    itemGraph = Item(testgraph, en, itemX).to_graph()
    # TODO: inspect!


class CustomItem(Item):
    @selector
    def randomRelation(self, testgraph, lang, subject):
        from random import randint
        assert isinstance(self, CustomItem)
        itemUris = [uri for uri in testgraph.subjects(RDF.type, T.Item)
                        if uri != subject]
        return Part(testgraph, lang, itemUris[randint(0, len(itemUris)-1)])

def test_selector_decorator():
    assert CustomItem(testgraph, en, itemX).randomRelation.name.startswith("Related ")


class FilteredItem(RdfQuery):
    sortedKeywords = each(T.keyword) | Sorter()
    sortedKeywordsReversed = each(T.keyword) | Sorter(reverse=True)

    sortedRelations_attr = each(T.relation) >> Item | \
            Sorter('name', reverse=True)
    sortedRelations_func = each(T.relation) >> Item |\
            Sorter(lambda r: getattr(r, 'name'), reverse=True)

    someKeywords = each(T.keyword) | Filter(lambda v: v in ('q', 'r', 'y'))

    name_upper = one(T.name) | (lambda v: unicode(v).upper())

def test_filter():
    item = FilteredItem(testgraph, en, itemX)
    yield assert_equals, item.name_upper, "ITEM X"

    def assert_sorted(item):
        keywords = "e q r t w y".split()
        assert item.sortedKeywords == keywords
        keywords.reverse()
        assert item.sortedKeywordsReversed == keywords
    yield assert_sorted, item

    def assert_sortedrels(rels):
        assert ['Related 2', 'Related 1'] == [it.name for it in rels]
    yield assert_sortedrels, item.sortedRelations_attr
    yield assert_sortedrels, item.sortedRelations_func

    def assert_some(item):
        assert set(item.someKeywords) == set(['q', 'r', 'y'])
    yield assert_some, item


def test_selector_filtered_by():

    class ItemWithSelectorAndFilter(Item):
        @selector.filtered_by(Sorter('name'), lambda l: l[0])
        def firstRelation(self, graph, lang, subject):
            return self.relations

    item = ItemWithSelectorAndFilter(testgraph, en, itemX)
    assert item.firstRelation.name == 'Related 1'


class ImplicitItem(RdfQuery):
    _rdfbase_ = T
    name = one()

def test_implicit_item():
    item = ImplicitItem(testgraph, en, itemX)
    assert item.name == "Item X"
    assert ImplicitItem.RDF_TYPE == T.ImplicitItem

class TypedImplicitItem(RdfQuery):
    _rdfbase_ = T
    RDF_TYPE = T.OtherType
    name = one()
    partlist = collection() >> Part

def test_typed_implicit_item():
    item = TypedImplicitItem(testgraph, en, itemX)
    collItems = [part.name for part in item.partlist]
    assert set(collItems) == set(["Part 1", "Part 2"])
    assert item.name == "Item X"
    assert TypedImplicitItem._rdfbase_ == T
    assert TypedImplicitItem.RDF_TYPE == T.OtherType


def test_from_dict():
    data = dict(
        name = "Item X",
        title = "Example Item",
        titleLang = { 'en': "Example Item", 'sv': "Exempelsak" },
        labels = [ "En", "eN" ],
        relations = [
                {'name': "Related 1"},
                {'name': "Related 2"},
            ],
        xmlData = "<div/>",
    )
    item = Item.from_dict(data, "en", URIRef("tag:oort.to,2006/test/item/x_fromdict"))
    # TODO: verify graph!
    item.to_graph()
    #print item.to_rdf(); raise Exception


def test_bound_with():
    bound = Item.bound_with(itemX)
    yield assert_equals, bound.query, Item
    yield assert_equals, bound.__name__, 'Item'
    yield assert_equals, bound(testgraph, en, BNode()).name,  u'Item X'
    bound = Item.bound_with(itemX, sv)
    yield assert_equals, bound(testgraph, None, BNode()).title, Literal(u'Exempelsak', sv)


def test_find_by():
    found = list(Item.find_by(testgraph, en, name=Literal(u'Item X')))
    yield assert_equals, found[0].uri, itemX
    for l, v in (en, u'Example Item'), (sv, u'Exempelsak'):
        found = Item.find_by(testgraph, l, title=Literal(v, l))
        yield assert_equals, list(found)[0].uri, itemX


#---------------------------------------

class MarkedItem(RdfQuery):
    title = localized(T)
    relations = each(T.relation) >> 'MarkedItem'
    unaryRelation = one(T) >> 'MarkedPart'
    annotated = one(T.unaryRelation) >> 'oort.util.queries:Annotated'

class MarkedPart(RdfQuery):
    name = one(T)
    related = one_where_self_is(T.unaryRelation) >> 'MarkedItem'

class TestSubQueryMarker:

    def setup(self):
        self.item = MarkedItem(testgraph, en, itemX)

    def test_self_as_named(self):
        for rel in self.item.relations:
            assert type(rel) is MarkedItem

    def test_named_following(self):
        assert type(self.item.unaryRelation) is MarkedPart

    def test_cyclic(self):
        assert type(self.item.unaryRelation.related) is MarkedItem

    def test_module_ref(self):
        assert type(self.item.annotated) is queries.Annotated


#---------------------------------------


# FIXME: test properly, with lots of reused query instances from a use with nest(l)ed references!
def test_exec_cache():
    queries = [Item, CustomItem]
    for item, query in zip(run_queries(queries, testgraph, en, itemX), queries):
        assert isinstance(item, query)
        test = TestItem()
        test.item = item
        yield test.test_one ,
        yield test.test_one_relation ,
        yield test.test_each ,
        yield test.test_collection ,
        yield test.test_collection_multiple ,
        yield test.test_i18n_dict ,


