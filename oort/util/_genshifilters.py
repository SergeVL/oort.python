# TODO: rewrite using only elementtree..(?)
# TODO: cannot handle ordered fallbacks (will filter all others or none)
#        - solutions may have to expand all literals, store their language and
#          fallback accordingly, or use a rather complex simultaneous iteraror
#          loop on all values.

from genshi import XML
from genshi.core import Stream

START, END = Stream.START, Stream.END
XML_LANG = u'{http://www.w3.org/XML/1998/namespace}lang'
RDF_WRAPPER = u'rdf-wrapper'

def language_filtered_xml(valueOrList, lang, fragment=True, encoding=None):
    if isinstance(valueOrList, unicode):
        return langXML(valueOrList, lang, fragment, encoding)
    else:
        # TODO: use flattened iterator instead..(?)
        events = []
        for value in valueOrList:
            if value:
                events.extend( langXML(value, lang, fragment, encoding).events )
        return Stream(events)

def langXML(text, lang, fragment=True, encoding=None):
    if text.startswith('<?xml ') or text.startswith('<!DOCTYPE '):
        fragment = False
    if fragment:
        text = '<xml>%s</xml>' % text
    if isinstance(text, unicode):
        encoding = 'utf-16'
        text = text.encode(encoding)
    stream = XML(text)
    lang_filter = filter_language(lang)
    if fragment:
        return stream | skip_outer | lang_filter
    else:
        return stream | lang_filter

def skip_outer(stream):
    """A filter that doesn't actually do anything with the stream."""
    istream = iter(stream)
    istream.next()
    last = None
    for content in istream:
        if last: yield last
        last = content

def filter_language(lang):
    def filter_lang(stream):
        depth = 0
        eating = False
        for kind, data, pos in stream:
            if kind == START and lang:
                elemLang = get_elem_lang(data)
                if elemLang:
                    # TODO: remove? remove_lang_attrib(data)
                    if elemLang != lang:
                        eating = True
            if eating == True:
                if kind == START:
                    depth += 1
                elif kind == END:
                    depth -= 1
                    if depth == 0: eating = False
                continue

            if kind == START and data[0] == RDF_WRAPPER:
                continue
            elif kind == END and data == RDF_WRAPPER:
                continue
            else:
                yield kind, data, pos

    return filter_lang

def get_elem_lang(data):
    # FIXME: Remove 'lang', it's a temporary solution due
    # to rdflib xml/rdf XMLLiteral with embedded xml:lang
    # parsing problems..
    for name, value in data[1]:
        if name in (XML_LANG, 'lang'):
            return value


