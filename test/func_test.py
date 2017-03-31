from FRAPanalyzer.lifproc import LIFContainer
from FRAPanalyzer.lifproc import start_bioformats
from FRAPanalyzer.lifproc import stop_bioformats

from collections import OrderedDict

from unittest import TestCase

TEST_LIF_FILE = './test_data/Experiment.lif'

TEST_LMS_FILE = './test_data/06.04.2014 3T3 HP-Btk FRAP.lsm'


class TestLifContainer(TestCase):

    def setUp(self):
        start_bioformats()

    def tearDown(self):
        stop_bioformats()

    def test_structured_annotations(self):
        lif = LIFContainer(TEST_LIF_FILE)
        structured_annotation = lif.get_structured_annotations()
        self.assertIsInstance(structured_annotation, OrderedDict)

    def test_rois_extraction(self):
        lif = LIFContainer(TEST_LMS_FILE)
        rois_structures = lif.get_rois_from_oemxml()
        self.assertIsInstance(rois_structures, dict)
