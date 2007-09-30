# -*- coding: UTF-8 -*-
from setuptools import setup, find_packages
import oort

setup(
    name = "Oort",
    version = oort.__version__,
    description = """A WSGI-enabled toolkit for creating RDF-driven web apps.""",
    long_description = oort.__doc__,
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules"
        ],
    keywords = "toolkit rdf orm",
    author = "Niklas Lindström",
    author_email = "lindstream@gmail.com",
    license = "BSD",
    url = "http://oort.to/",
    #packages = find_packages(exclude=["*.test", "*.test.*", "test.*", "test"]),
    packages = find_packages(),
    include_package_data = True,
    zip_safe = False,
    test_suite = 'nose.collector',
    install_requires = ['rdflib >= 2.3',
                      'Genshi >= 0.4'
                      'setuptools'],
    entry_points="""
        """
    )

