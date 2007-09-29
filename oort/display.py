# -*- coding: UTF-8 -*-
"""
"""
#=======================================================================
import os.path
from rdflib import RDF, RDFS, ConjunctiveGraph
from genshi.output import DocType
from genshi.template import TemplateLoader
from oort.util import templating
from oort.util.code import contract, autosuper
__metaclass__ = autosuper
#=======================================================================
# TODO: Remove all variant handling; too much arbitrariness.
# If a need for aspect-switching on request details arise, re-invent.
# (This is reasonably done within the template system).
# TODO: use Buffet-style templating instead(?)


class DisplayBase:

    contentType = None

    def __init__(self, cfg=None):
        pass

    @contract.template_method
    def get_result_generator(self, graph, appUtil, variantArg):
        raise NotImplementedError


class Display(DisplayBase):

    # TODO: for outputEncoding, see Aspect problems below.
    #       May need to redesign to set template-speficic stuff instead.
    #       These options should be available as data too (e.g. for template
    #       output and/or encoding specific stuff..).
    outputMethod = None
    outputEncoding  = None

    templateBase = ""
    globalQueries = None
    aspects = []

    def __init__(self, cfg=None):
        self.typeAspects = {}
        self.variantAspects = {}
        cfg = cfg or {}
        cfg['templateBase'] = self.templateBase
        for aspect in self.aspects:
            aspect.post_init_setup(self.globalQueries, cfg=cfg)
            if aspect.forVariant:
                variant = self.variantAspects.setdefault(aspect.forVariant, {})
                typeDict = variant
            else:
                typeDict = self.typeAspects
            typeDict[aspect.forType] = aspect

    @contract.default_method
    def parse_variant(self, variantStr):
        return variantStr

    def get_result_generator(self, graph, appUtil, variantArg):
        variant = self.parse_variant(variantArg)
        data = self.get_extra_data(appUtil, variant) or {}
        data['app'] = appUtil
        resource, lang = appUtil.current.resource, appUtil.current.lang
        aspect = self.get_aspect(graph, resource, variant)
        generate = aspect.make_result_generator(graph, resource, lang, data)
        return generate(self.outputMethod, encoding=self.outputEncoding)

    def get_aspect(self, graph, resource, variant):
        rdfType = RDFS.Resource
        for _type in graph.objects(resource, RDF.type):
            rdfType = _type; break
        typeDict = self.typeAspects
        if variant:
            typeDict = self.variantAspects.get(variant) or self.typeAspects
        return typeDict.get(rdfType) or typeDict[RDFS.Resource]

    @contract.default_method
    def get_extra_data(self, appUtil, variant):
        "Use for further template preparation based on current request."
        return None


class KeywordVariantParser:
    pass # TODO


class SubTypeAwareDisplay(Display):

    def __init__(self, cfg=None):
        self.__super.__init__(cfg)
        self._matchGraph = None

    def get_aspect(self, graph, resource, variant):
        if not self._matchGraph:
            self._matchGraph = self.create_match_graph(graph)
        return self.__super.get_aspect(self._matchGraph, resource, variant)

    def create_match_graph(self, graph):
        """For optimization, creating a sparse graph of "best matching"
        for all resources and querying only that at runtime. """
        typeAspects = self.typeAspects
        def list_with_sub_types(rdfType):
            yield rdfType
            for subType in graph.subjects(RDFS.subClassOf, rdfType):
                if subType not in typeAspects:
                    for subSub in list_with_sub_types(subType):
                        yield subSub

        sparseGraph = ConjunctiveGraph()
        for handledType in typeAspects:
            for anySub in list_with_sub_types(handledType):
                for resource in graph.subjects(RDF.type, anySub):
                    sparseGraph.add((resource, RDF.type, handledType))

        return sparseGraph

    # TODO: Implement? Not really useful if create_match_graph is used;
    # however, this one is *much* better if resources are volatile..
    #def get_aspect(resource):
    #    for rType in graph.objects(resource, RDF.type):
    #        if rType in _mostSpecificHandled:
    #            return typeAspects.get(rType)
    #        supType = _handledSupers.get(rType)
    #        if supType:
    #            return typeAspects.get(supType)
    #    return typeDict[RDFS.Resource]


class AspectBase:

    def __init__(self, forType, queries=None, forVariant=None):
        self.forType = forType
        self.queries = queries or {}
        self.forVariant = forVariant

    @contract.state_change
    def post_init_setup(self, globalQueries, cfg=None):
        if globalQueries:
            queries = globalQueries.copy()
            queries.update(self.queries)
            self.queries = queries
        self.post_init_configure(cfg or {})

    @contract.template_method
    def post_init_configure(self, cfg):
        pass

    @contract.helper
    def generate_query_items(self, graph, resource, lang):
        """Generates key, value pairs which constitute named, run queries."""
        if self.queries:
            for name, query in self.queries.items():
                yield name, query(graph, lang, resource)

    # TODO: redesign to set (default) encoding and output(method) via cfg in Aspect#post_init_setup?
    @contract.template_method
    def make_result_generator(self, graph, resource, lang, data=None):
        """Returns a generator that takes the arguments 'encoding' and
        'output'."""
        raise NotImplementedError

    def using(self, **queries):
        self.queries = queries
        return self

class TemplateAspectBase(AspectBase):
    def __init__(self, forType, templateName, queries=None, forVariant=None):
        self.__super.__init__(forType, queries, forVariant)
        self.templateName = templateName
        self.templateBase = None

    def post_init_configure(self, cfg):
        self.templateBase = cfg.get('templateBase')

class Aspect(TemplateAspectBase):

    RELOAD_TEMPLATES = "reload_templates"

    # TODO: use coming genshi.template.plugin.MarkupTemplateEnginePlugin.doctypes
    doctypes = dict(
            (key.lower().replace('_', '-'), item)
            for key, item in DocType.__dict__.items()
            if key.isupper() and isinstance(item, tuple)
        )

    def post_init_configure(self, cfg):
        self.__super.post_init_configure(cfg)
        autoReload = str(cfg.get(self.RELOAD_TEMPLATES, False)) == str(True)
        self.loader = TemplateLoader(['.'], auto_reload=autoReload)

    def load_template(self):
        return self.loader.load(os.path.join(self.templateBase, self.templateName))

    def make_result_generator(self, graph, resource, lang, data=None):
        tplt = self.load_template()
        allData = dict( self.generate_query_items(graph, resource, lang) )
        if data: allData.update(data)
        # TODO: although genshi has a serialize (to stream) too, it doesn't
        # take encoding. Find the simplest way to get around that (without too
        # much duplicatiom of render innards..).. Or just remove this todo?
        def generator(format, encoding):
            doctype = self.doctypes.get(format)
            format = format.split('-')[0]
            yield tplt.generate(**allData).render(
                    format, doctype=doctype, encoding=encoding)
        return generator


class TpltAspect(TemplateAspectBase):

    engineManager = templating.TemplateEngineManager(None, {})

    defaultEngine = "genshi"

    def post_init_configure(self, cfg):
        self.__super.post_init_configure(cfg)
        self.engine, self.path = self.engineManager.get_engine_and_path(
                self.templateBase+'.'+self.templateName, self.defaultEngine)
        template = self.engine.load_template(self.path)
        self.template = template or None

    def make_result_generator(self, graph, resource, lang, data=None):
        allData = dict(self.generate_query_items(graph, resource, lang))
        if data:
            allData.update(data)
        engine = self.engine
        template = self.template or self.path
        # FIXME: needs to use encoding, but alas, the plugin format precludes it...
        def generator(format, encoding):
            result = engine.render(allData, format=format, template=template)
            yield result
        return generator


class RdfAspect(AspectBase):

    def __init__(self, forType, queries=None):
        self.__super.__init__(forType, queries)

    def make_result_generator(self, graph, resource, lang, data=None):
        qData = dict( self.generate_query_items(graph, resource, lang) )
        def generator(format, encoding):
            lgraph = ConjunctiveGraph()
            for key, result in qData.items():
                lgraph += result.to_graph()
            yield lgraph.serialize(format='pretty-xml')
        return generator

class JsonAspect(AspectBase):

    def __init__(self, forType, queries=None, subjectKey=False):
        self.__super.__init__(forType, queries)
        self.subjectKey = subjectKey

    def make_result_generator(self, graph, resource, lang, data=None):
        qData = dict( self.generate_query_items(graph, resource, lang) )
        def generator(format, encoding):
            # TODO: use encoding!
            yield '{\n'
            for i, (key, result) in enumerate(qData.items()):
                if i != 0: yield ","
                yield "'%s':" % key
                # TODO: a very crude way of dealing with long text..
                yield result.to_json(self.subjectKey).replace('}', '}\n')
            yield '}\n'
        return generator


