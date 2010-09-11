
from oort.sparqltree.access import Endpoint, GraphAccess


def discover_access(data_location):
    start = data_location.startswith
    if start("http:") or start("https:"):
        return Endpoint(data_location)
    else:
        return GraphAccess(directory_to_graph(data_location))

def directory_to_graph(dirpath):
    # TODO: major external oort dependency; rfdlib-2.5+ to the rescue. And/or
    # sparqltree will go into oort proper. (I *shall* do this!)
    from oort.util.graphs import dir_to_graph
    return dir_to_graph(dirpath)


