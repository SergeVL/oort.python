#=======================================================================
from rdflib import ConjunctiveGraph
from oort.sitebase import MultiBaseResourceViewer, AspectBase
#=======================================================================


class TestResourceViewerBase:
    pass # TODO: test at least __call__- and app_factory!


def test_MultiBaseResourceViewer():
    # TODO: verify test accuracy; then remake into test generator (see nose)

    class TestViewer(MultiBaseResourceViewer):
        resourceBases = {
            'ont': ("http://example.org/rdfns/ontology#", ''),
            'ex': ("http://example.org/resources/", "/"),
            'urn': ("urn:example-org:", ":"),
        }
        defaultResource = 'http://example.org/default/resource'

    viewer = TestViewer(ConjunctiveGraph())
    def test_path(path, expected, samePath=True):
        resource = viewer.resource_from(path.split('/'))
        assert resource == expected
        path2, _success = viewer.resource_to_app_path(resource)
        assert (path == path2) is samePath

    test_path("ex/path/to/resource", "http://example.org/resources/path/to/resource")
    test_path("ex/", "http://example.org/resources/")
    test_path("ont/OneConcept", "http://example.org/rdfns/ontology#OneConcept")
    test_path("ont/someRelationTo", "http://example.org/rdfns/ontology#someRelationTo")
    test_path("bad/nothing/to/see/here", "http://example.org/default/resource", False)
    test_path("bad/", "http://example.org/default/resource", False)
    test_path("/", "http://example.org/default/resource", False)
    test_path("", "http://example.org/default/resource", False)


def test_using():
    dummy = object()
    aspect = AspectBase(None)
    assert aspect == aspect.using(item=dummy)
    assert aspect.queries['item'] == dummy


