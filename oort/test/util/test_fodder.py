from rdflib import ConjunctiveGraph
from oort.test import mergepaths
from oort.util.fodder import load_fodder

CONTENT = mergepaths(__file__, 'fodder_contents/site')

graph = ConjunctiveGraph()
load_fodder(graph, CONTENT)

