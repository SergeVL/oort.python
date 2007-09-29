# -*- coding: UTF-8 -*-
#--------------------------------------------------------------------------------
# The Oort BSD-style License
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#     * Neither the name of Oort nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#--------------------------------------------------------------------------------
"""
========================================================================
Oort
========================================================================

Oort is a toolkit for creating RDF_-driven WSGI_-compliant web applications.

The purpose of this is to make it easy to create web views of RDF Graphs by 
using some declarative python programming.

Oort uses RDFLib_, Paste_ and Genshi_ for the heaving lifting. (Initial but 
rudimentary support for `Template Plugins`_ alá Buffet and TurboGears is also 
included.)

.. _RDF: http://www.rdfabout.net
.. _WSGI: http://wsgi.org
.. _RDFLib: http://rdflib.net
.. _Paste: http://pythonpaste.org
.. _Genshi: http://genshi.edgewall.org/
.. _`Template Plugins`: http://www.turbogears.org/docs/plugins/template.html

Overview
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These are the main packages:

``oort.sitebase``
    Contains classes used for declarative definitions of *displays*, used for 
    matching resources and rendering a particular output (html, json etc.). By 
    defining *aspects*, the type (or super-type) of a selected resource is 
    mapped to a particular RdfQuery and an associated template.

    One or more displays are put in the context of a *resource viewer*, which 
    becomes a WSGI application ready to mount in your WSGI environment.

``oort.rdfview``
    Contains classes and functions used for defining RDF queries and selectors, 
    i.e. declarations used to pick properties and associated sub-queries from a
    chosen resource (similar to how many ORM-toolkits work).

How?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Loads of RDF data like::

    <site/main> a :SiteNode;
        dc:title "Main Page"@en, "Huvudsida"@sv;
        dc:altTitle "Main", "Hem"@sv;
        :relations (
            <site/faq>
            <site/about>
        );
        :nodeContent '''<h1 xml:lang="en">Welcome</h1>'''^^rdfs:XMLLiteral,
                     '''<h1 xml:lang="sv">V&#195;&#164;lkommen</h1>'''^^rdfs:XMLLiteral .

    <persons/someone> a foaf:Person;
        foaf:name "Some One";
        foaf:knows <otherone> .

A couple of RdfQuerys::

    from oort.rdfview import *
    from myapp.ns import SITE # your own..

    class Titled(RdfQuery):
        title = localized(DC)
        altTitle = localized(DC.alternative)

    class SiteNode(Titled):
        relations = collection(SITE) >> Titled
        nodeContent = localized_xml(SITE)

    class Person(RdfQuery):
        name = one(FOAF)
        knows = each(FOAF) >> THIS_QUERY

And a web application::

    from oort.sitebase import *
    from myapp import queries
    from myapp.ns import SITE

    class ExampleViewer(ResourceViewer):

        resourceBase = "http://example.org/oort/"
        langOrder = 'en', 'sv'

        class PlainWebDisplay(Display):
            name = "main"
            default = True
            outputMethod = 'xhtml'
            outputEncoding  = 'iso-8859-1'
            templateBase = "view/mainweb"
            globalQueries = {'languages': queries.sitelabels }
            aspects = [
                    Aspect(SITE.SiteNode, "sitenode.xhtml",
                            {'node': queries.SiteNode}) ,
                    Aspect(FOAF.Person, "person.xhtml",
                            {'person': queries.Person}) ,
                    Aspect(RDFS.Resource, "not_found.xhtml")
                ]

        class JsonDisplay(Display):
            name = "json"
            contentType = 'application/x-javascript'
            aspects = [
                    JsonAspect(SITE.SiteNode, {'node': queries.SiteNode})
                ]

But wait, there's more..

Paste!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Makes WSGI go down smoothly. ResourceViewers take RDFLib ``Graph`` instances in 
their constructors and become callables adhering to the spec.

To get started quickly, run::

    $ paster create -t oort_app
    ... fill in desired values in the dialogue
    $ cd myapp/
    $ vim # edit and test..
    $ chmod u+x webapp.ini
    $ ./webapp.ini

Why?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Because RDF is a formidable technology that could revolutionize the way 
information is treated and shared. Python and WSGI are exemplary technologies 
to use when building applications dealing with such data.

Why *Oort*?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* The Oort Cloud is a fascinating, alien phenomenon in a region *less 
  travelled*..
* Imagine all the BNodes in that cloud just waiting for an URI on the Web..
* "Output-Oriented RDF Toolkit"!
* a Dutch surname, so the way may be obvious to Oort..

--------------------------------------------------------------------------------

Copyright (c) 2006, 2007 Niklas Lindström <lindstream@gmail.com>.
All rights reserved.

License: BSD-style <http://opensource.org/licenses/bsd-license>.

"""

__docformat__ = 'reStructuredText en'
__author__ = "Niklas Lindström"
__version__ = "0.3.3"

