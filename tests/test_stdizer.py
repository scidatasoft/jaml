from unittest import TestCase

from chem.SimpleStdizer import SimpleStdizer
from chem.readers import SdfRecords, CsvRecords


class TestStdizer(TestCase):
    def test_badMoles_KM20210211(self):
        stdizer = SimpleStdizer()
        for (i, r) in enumerate(SdfRecords('badMoles_KM20210211.sdf')):
            r = stdizer.standardize(r.mol())
            if not r or r.changed():
                print(f"{i}: {r}")

    def test_on_sdf(self):
        stdizer = SimpleStdizer()
        for (i, r) in enumerate(SdfRecords('small.sdf')):
            r = stdizer.standardize(r.mol())
            if not r or r.changed():
                print(f"{i}: {r}")

    def test_on_csv(self):
        stdizer = SimpleStdizer()
        for (i, r) in enumerate(CsvRecords('small.csv')):
            r = stdizer.standardize(r.mol())
            if not r or r.changed():
                print(f"{i}: {r}")

    def test_on_csv_200(self):
        stdizer = SimpleStdizer()
        for (i, r) in enumerate(CsvRecords('CHEMBL348_P-aeruginosa_34848MICs_200.csv')):
            r = stdizer.standardize(r.mol())
            if not r or r.changed():
                print(f"{i}: {r}")
