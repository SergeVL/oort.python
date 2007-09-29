#=======================================================================
from rdflib import URIRef, RDF, RDFS
from oort.rdfview import RdfQuery, one, localized, i18n_dict
from oort.util.code import SlotStruct
#=======================================================================

class Typed(RdfQuery):
    rdfType = one(RDF.type)

class Labelled(RdfQuery):
    label = localized(RDFS)

class Annotated(Labelled):
    comment = localized(RDFS)

class Resource(Annotated, Typed):
    pass

#-----------------------------------------------------------------------

class HasLabel(RdfQuery):
    label = localized(RDFS.RDFSNS)

def make_label_query(uriBase, *uriTails):
    def labels(graph, lang, resource, **kwargs):
        labelBase = uriBase + "%s"
        class Labels(SlotStruct):
            __slots__ = uriTails
        return Labels(
                *[HasLabel(graph, lang, URIRef(labelBase % tail)).label
                        for tail in Labels.__slots__] )
    return labels

class Lang(RdfQuery):
    value = one(RDF.RDFNS)
    label = i18n_dict(RDFS.RDFSNS)

