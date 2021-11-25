import sys

from indigo import Indigo, IndigoException, IndigoObject
from indigo.inchi import IndigoInchi


class StdizerResult:
    def __init__(self, indigo_inchi: IndigoInchi):
        self.indigo_inchi = indigo_inchi
        self._success = False
        self._m_org = None
        self._m_std = None
        self.issues = []

    def add_issue(self, severity: str, message: str):
        self.issues.append([severity, message])

    def inchi(self, original=False):
        try:
            inchi = self.indigo_inchi.getInchi(self._m_org if original else self._m_std)
            inchi_key = self.indigo_inchi.getInchiKey(inchi)
            return inchi, inchi_key
        except IndigoException as ex:
            print(str(ex), file=sys.stderr)
            return None, None

    def mol(self, original=False):
        try:
            m = self._m_org if original else self._m_std
            return m.molfile()
        except IndigoException:
            return None

    def smiles(self, original=False):
        try:
            m = self._m_org if original else self._m_std
            return m.smiles()
        except IndigoException:
            return None

    def changed(self):
        return self.inchi(original=True)[1] != self.inchi()[1]

    def __str__(self):
        conv = f"{self._m_org.smiles()} => {self._m_std.smiles()}" if self.changed() else ''
        issues = self.issues if self.issues else ''
        return f"{self._success} {conv} {issues}"

    def __bool__(self):
        return self._success


# https://lifescience.opensource.epam.com/indigo/options/standardize.html
std_options_1 = [
    ['standardize-remove-single-atoms', True],
]

std_options_2 = [
    # ['standardize-stereo', True],
    ['standardize-clear-enhanced-stereo', True],
    ['standardize-clear-unknown-stereo', True],
    ['standardize-clear-unknown-atom-stereo', True],
    ['standardize-clear-unknown-bond-stereo', True],
    # ['standardize-reposition-stereo-bonds', True],
    # ['standardize-fix-direction-wedge-bonds', True],

    # ['standardize-charges', True],

    ['standardize-keep-largest', True],

    ['standardize-clear-unusual-valences', True],
    ['standardize-clear-isotopes', True],
    ['standardize-clear-dative-bonds', True],
    ['standardize-clear-hydrogen-bonds', True],
]


class SimpleStdizer:

    def __init__(self):
        self.indigo = Indigo()
        self.indigo.setOption('ignore-stereochemistry-errors', True)
        self.indigo.setOption('aromaticity-model', 'generic')
        self.indigo_inchi = IndigoInchi(self.indigo)
        self.maxC_rule = False

    def set_options(self, options: list):
        for (k, v) in options:
            self.indigo.setOption(k, v)

    @staticmethod
    def neutralize(m: IndigoObject):
        for atom in m.iterateAtoms():
            if atom.symbol() == 'O' and atom.degree() == 1 and atom.charge() == -1:
                nei = atom.iterateNeighbors().next()
                if nei.symbol() == 'C' or nei.symbol() == 'S':
                    atom.resetCharge()

    def standardize(self, mol: str) -> StdizerResult:
        result = StdizerResult(self.indigo_inchi)
        try:
            result._m_org = self.indigo.loadMolecule(mol)
            result._m_org.dearomatize()
            result._m_std = result._m_org.clone()
        except IndigoException as ex:
            result.add_issue('Error', str(ex))
            return result

        try:
            maxC = 0
            for component in result._m_std.iterateComponents():
                nC = 0
                for atom in component.iterateAtoms():
                    if atom.symbol() == 'C':
                        nC += 1

                if nC > maxC:
                    maxC = nC

            if not maxC:
                result.add_issue('Error', 'Inorganic')
                return result

            if self.maxC_rule and maxC < 2:
                result.add_issue('Error', 'Not enough carbon atoms')
                return result

        except IndigoException as ex:
            result.add_issue('Error', str(ex))
            return result

        try:
            self.set_options(std_options_1)
            result._m_std.standardize()
            if result._m_std.countComponents() == 0:
                result.add_issue('Error', 'Empty chemical')
                return result
            elif result._m_std.countComponents() > 1:
                result.add_issue('Error', 'Multi-component chemical')
                return result
        except IndigoException as ex:
            result.add_issue('Error', str(ex))
            return result

        try:
            self.set_options(std_options_2)
            result._m_std.standardize()
            self.neutralize(result._m_std)
            result._success = True
        except IndigoException as ex:
            result.add_issue('Error', str(ex))
            return result

        return result
