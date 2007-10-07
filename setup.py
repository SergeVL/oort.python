# -*- coding: UTF-8 -*-
from setuptools import setup, find_packages
# Nasty hack to make e.g. setup.py register read PKG-INFO as utf-8.. {{{
import sys
reload(sys) # setdefaultencoding is deleted in site.py..
sys.setdefaultencoding('utf-8')
# }}}
import oort

setup(
    name = "Oort",
    version = oort.__version__,
    description = """A toolkit for accessing RDF graphs as plain objects.""",
    long_description = """
    %s""" % "".join(open("README.txt")),
    classifiers = [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules"
        ],
    keywords = "rdf graph toolkit database orm programming",
    platforms = ["any"],
    author = "Niklas Lindström",
    author_email = "lindstream@gmail.com",
    license = "BSD",
    url = "http://oort.to/",
    #packages = find_packages(exclude=["*.test", "*.test.*", "test.*", "test"]),
    packages = find_packages(),
    include_package_data = True,
    zip_safe = False,
    test_suite = 'nose.collector',
    install_requires = ['rdflib >= 2.4',
                        'setuptools'],
    #entry_points="""
    #    """,
    )

