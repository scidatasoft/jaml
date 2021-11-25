import csv

from indigo import Indigo, IndigoException
from indigo.inchi import IndigoInchi

from errors import JamlError

indigo = Indigo()
indigo.setOption('ignore-stereochemistry-errors', True)
indigo.setOption('aromaticity-model', 'generic')
indigo_inchi = IndigoInchi(indigo)


class Record:
    def __init__(self, mol, props, clean=False):
        self.errors = []
        try:
            self._m = indigo.loadMolecule(mol)
            if clean:
                self._m.layout()
            self._m.dearomatize()
        except IndigoException as ex:
            self.errors.append(str(ex))

        try:
            self.inchi = indigo_inchi.getInchi(self._m)
            self.inchi_key = indigo_inchi.getInchiKey(self.inchi)
        except AttributeError or IndigoException as ex:
            self.inchi = None
            self.inchi_key = None
            self.errors.append(str(ex))

        self.props = props

    def smiles(self):
        return self._m.smiles() if self._m else None

    def mol(self):
        return self._m.molfile() if self._m else None

    def __str__(self):
        return f"InChI: {self.inchi}, InChIKey: {self.inchi_key}, SMILES: {self.smiles()}, Props: {self.props}"

    def __del__(self):
        if self._m:
            self._m.__del__()


class SdfRecords:
    def __init__(self, path):
        self._reader = indigo.iterateSDFile(path)

    def __iter__(self):
        return self

    def __next__(self):
        try:
            rec = self._reader.__next__()
            props = {prop.name(): prop.rawData().strip() for prop in rec.iterateProperties() if prop.rawData().strip()}
            return Record(rec.molfile(), props)
        except IndigoException:
            return None

    def __del__(self):
        self._reader.__del__()


class CsvRecords:
    def __init__(self, path, field='SMILES'):
        self._f = open(path, 'r')
        self._reader = csv.DictReader(self._f)
        self.field = field

    def __iter__(self):
        return self

    def __next__(self):
        props = self._reader.__next__()
        return Record(props[self.field], dict(props), clean=True)

    def __del__(self):
        self._f.close()


class XlsxRecords:
    def __init__(self, path, field='SMILES'):
        self._f = open(path, 'r')
        self._reader = csv.DictReader(self._f)
        self.field = field

    def __iter__(self):
        return self

    def __next__(self):
        props = self._reader.__next__()
        return Record(props[self.field], dict(props))

    def __del__(self):
        self._f.close()


def get_records_reader(path, name, field_name):
    lwr = name.lower() if name else path.lower()
    if lwr.endswith('.sdf'):
        return SdfRecords(path)
    if lwr.endswith('.csv'):
        return CsvRecords(path, field_name)
    if lwr.endswith('.xlsx'):
        return XlsxRecords(path, field_name)

    raise JamlError(f'Unknown file type: {path}')
