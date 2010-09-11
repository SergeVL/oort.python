from oort.sparqltree.ext import json, autosuper
from oort.sparqltree.autotree import treeify_results


__metaclass__ = autosuper # TODO: really?


class Access:
    def run_query_to_tree(self, query):
        return treeify_results(self.run_query(query))


class Endpoint(Access):
    def __init__(self, endpoint_url, supports_json=True):
        self.__super.__init__()
        self.endpoint_url = endpoint_url
        self.supports_json = supports_json
        self._wrapper = self._create_wrapper()

    def _create_wrapper(self):
        try:
            from SPARQLWrapper import SPARQLWrapper, JSON
        except ImportError:
            # TODO: if not available, fallback to httplib
            raise
        wrapper = SPARQLWrapper(self.endpoint_url)
        if self.supports_json:
            wrapper.setReturnFormat(JSON)
        else:
            raise NotImplementedError(
                    "Endpoint must support the JSON serialization format.")
            # TODO: from oort.sparqltree.access.results import xmltojsonform..
        return wrapper

    def run_query(self, query):
        wrapper = self._wrapper
        wrapper.setQuery(query)
        results = wrapper.queryAndConvert()
        return results


class GraphAccess(Access):
    def __init__(self, graph):
        self.__super.__init__()
        self._graph = graph
    def run_query(self, query):
        graph = self._graph
        # FIXME: due to serialize-impl this is excruciatingly slow (patch rdflib)
        return json.loads(graph.query(query).serialize('json'))


