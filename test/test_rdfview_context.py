from rdflib import Literal
from oort.rdfview import QueryContext


from test_rdfview import T, testgraph, itemX, Item
import test_rdfview


class TypedItem(Item):
    RDF_TYPE = T.Item

def assert_item_facts(item):
    assert item.uri == itemX, \
            "Unexpected uri: %r" % item.uri
    assert item.title == Literal(u'Example Item', 'en'), \
            "Unexpected title: %r" % item.title


class TestQueryContext(object):

    def test_by_attr(self):
        context = QueryContext(testgraph, 'en', query_modules=[test_rdfview])
        item = context.Item(itemX)
        assert_item_facts(item)

    def test_find_all(self):
        context = QueryContext(testgraph, 'en', queries=[TypedItem])
        items = context.TypedItem.find_all()
        assert itemX in [item.uri for item in items]

    def test_by_find(self):
        context = QueryContext(testgraph, 'en', queries=[Item, TypedItem])
        item = context.view_for(itemX)
        assert isinstance(item, TypedItem)
        assert_item_facts(item)

    def test_by_attr_and_find_by(self):
        context = QueryContext(testgraph, 'en', queries=[Item])
        found = context.Item.find_by(name=Literal(u'Item X'))
        assert list(found)[0].uri == itemX

    def test_callable_lang(self):
        def getlang():
            return 'en'
        context = QueryContext(testgraph, getlang, queries=[Item])
        item = context.Item(itemX)
        assert_item_facts(item)


def test_context_factory():
    factory = QueryContext.context_factory(testgraph, 'en', queries=[Item])
    context = factory()
    item = context.Item(itemX)
    assert_item_facts(item)


