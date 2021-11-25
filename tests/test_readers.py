from unittest import TestCase

from chem.readers import SdfRecords, CsvRecords


class TestRecsIters(TestCase):
    def test_SdfRecords(self):
        for r in SdfRecords('small.sdf'):
            print(r)

    def test_CsvRecords(self):
        for r in CsvRecords('small.csv'):
            print(r)
