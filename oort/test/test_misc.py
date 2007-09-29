# -*- coding: UTF-8 -*-
from oort.util._genshifilters import language_filtered_xml


XML = u"""
<span>XML.</span>
"""

XML_EN = u"""
<span xml:lang="en">Testing.</span>
"""

XML_SV = u"""
<span xml:lang="sv">Testar.</span>
"""

FULL_XML = u"""
<div xml:lang="en">Testing.</div>
<div xml:lang="sv">Testar.</div>
"""

WRAPPED = u"""<rdf-wrapper>
    <p><em>XML</em>.</p>
</rdf-wrapper>"""

WRAPPED_EN = u"""<rdf-wrapper xml:lang="en">
    <p>Some content.</p>
    <p>Some <em>more</em> content.</p>
</rdf-wrapper>"""

WRAPPED_SV = u"""<rdf-wrapper xml:lang="sv">
    <p>Lite inneåll.</p>
    <p>Lite <em>mer</em> innehåll.</p>
</rdf-wrapper>"""


def test_language_filtered_xml():
    for lang in 'en', 'sv':
        print "="*20, lang
        for xml in (XML, XML_EN, XML_SV, FULL_XML, WRAPPED, WRAPPED_EN, WRAPPED_SV):
            stream = language_filtered_xml(xml, lang)
            print stream.render()
    stream = language_filtered_xml([XML_EN, XML_SV], 'en')

