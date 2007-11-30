#=======================================================================
__metaclass__ = type
import os
import shutil
import tempfile
import time
from rdflib import RDF, URIRef, Literal, ConjunctiveGraph
from oort.util.graphs import *
from nose.tools import assert_equals
#=======================================================================


class LoadDirBase:

    def setup(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown(self):
        shutil.rmtree(self.temp_dir)

    def fpath(self, fname):
        return os.path.join(self.temp_dir, fname)

    def write_file(self, fname, data):
        fpath = self.fpath(fname)
        f = open(fpath, 'w')
        f.write(data)
        f.close()


class TestLoaders(LoadDirBase):

    def setup(self):
        LoadDirBase.setup(self)
        self.graph = ConjunctiveGraph()


    def test_load_if_modified(self):
        fname = "file1.n3"
        s = "urn:s1"
        for o in ["urn:T1", "urn:T2"]:
            self.write_file(fname, "<%s> a <%s> ." % (s, o))
            load_if_modified(
                    self.graph, self.fpath(fname), 'n3')
            time.sleep(1.0)
            assert_equals(self.graph.value(URIRef(s), RDF.type, any=False), URIRef(o))


    def test_load_dir(self):
        fnames = ["file-%s.n3"%i for i in range(4)]
        t1 = "urn:T1"
        t2 = "urn:T2"

        for fname in fnames:
            self.write_file(fname, "<urn:%s> a <%s> ." % (fname, t1))
        load_dir(self.graph, self.temp_dir)
        time.sleep(1.0)

        file0 = fnames[0]
        self.write_file(file0, "<urn:%s> a <%s> ." % (file0, t2))
        load_dir(self.graph, self.temp_dir)
        assert_equals(
                self.graph.value(URIRef("urn:%s"%file0), RDF.type, any=False),
                URIRef(t2))


    def test_loader(self):
        fname = "file1.n3"
        s = "urn:s1"
        load = loader(self.graph, self.temp_dir+'/')
        for o in ["urn:T1", "urn:T2"]:
            self.write_file(fname, "<%s> a <%s> ." % (s, o))
            load(fname)
            time.sleep(1.0)
            assert_equals(self.graph.value(URIRef(s), RDF.type, any=False), URIRef(o))


