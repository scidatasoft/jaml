import logging as log
from typing import List

import numpy as np
from pandas import DataFrame, Series
from rdkit import Chem
from rdkit.Chem import AllChem
from sklearn.impute import SimpleImputer

from db.JamlMongo import JamlMongo
from utils.utils import custom_split


class Compound:
    def __init__(self, db_id, activity, mol):
        """
        one compound is part of a database. it contains an id, an activity, and an rdkit mol
        """
        self.db_id = db_id
        self.activity = activity
        self.mol = mol
        self.smiles = Chem.MolToSmiles(mol)


class BaseSet:
    def __init__(self, name: str, descriptors, compounds):
        self.name = name
        self.descriptors = descriptors
        self.compounds = compounds

    def get_fp(self):
        fp = []
        if not self.descriptors:
            for c in self.compounds:
                fp.append(np.zeros(64).tolist())  # fake fingerprint just for split)
        else:
            smiles = list(cmp.smiles for cmp in self.compounds)

            for d in self.descriptors:
                type = d['name'].lower()
                if type == 'ecfp' or type == 'fcfp':
                    print(f"Descriptors: {type}: {d['params']}")
                    for (i, c) in enumerate(self.compounds):
                        if i >= len(fp):
                            fp.append([])
                        fp[i].extend([int(x) for x in AllChem.GetMorganFingerprintAsBitVect(c.mol,
                                                                                            int(d['params']['Radius']),
                                                                                            int(d['params']['Bits']),
                                                                                            useFeatures=type == 'fcfp',
                                                                                            useChirality=True)])

        try:
            # Impute missing values with zeros
            imp = SimpleImputer(strategy="constant", fill_value=0)
            fp = imp.fit_transform(fp)
            imp = SimpleImputer(missing_values=None, strategy="constant", fill_value=0)
            fp = imp.fit_transform(fp)
        except ValueError:
            pass

        return fp


class DataSet(BaseSet):
    def __init__(self, ds_id, label, descriptors=None, test_set_size=None, train_indices=None, test_indices=None):
        ds = JamlMongo.get_dataset(ds_id)
        self.ds_id = ds_id
        self.label = label
        self.test_set_size = int(test_set_size) if test_set_size else 0

        super().__init__(ds.name, descriptors, [])

        # The rest is only for DataSet being created for fit or split
        if label or test_set_size:
            for c in JamlMongo.get_dataset_compounds(ds_id, label):
                try:
                    value = float(c['value']) if label == 'continuous-value' else int(c['value'])
                    m = Chem.MolFromMolBlock(c['mol'])
                    if m:
                        compound = Compound(c['db_id'], value, mol=m)
                        self.compounds.append(compound)
                except ValueError:
                    log.error(f"Skipping {c['value']}...")

            fp = self.get_fp()

            self.X = DataFrame(fp, index=[cmp.db_id for cmp in self.compounds])
            self.y = Series([cmp.activity for cmp in self.compounds], index=[cmp.db_id for cmp in self.compounds])

            if test_set_size or test_indices:
                if not train_indices or not test_indices:
                    self.X_train, self.X_test, self.y_train, self.y_test, train_indices, test_indices = \
                        custom_split(self.X, self.y, test_size=test_set_size / 100., random_state=42,
                                     stratify=None if label == 'continuous-value' else self.y)
                    self.train_indices = train_indices.tolist()
                    self.test_indices = test_indices.tolist()
                else:
                    from sklearn.utils import _safe_indexing
                    self.X_train, self.X_test = _safe_indexing(self.X, train_indices), _safe_indexing(self.X,
                                                                                                      test_indices)
                    self.y_train, self.y_test = _safe_indexing(self.y, train_indices), _safe_indexing(self.y,
                                                                                                      test_indices)
                    self.train_indices, self.test_indices = train_indices, test_indices
            else:
                self.X_train = self.X
                self.y_train = self.y
                self.X_test = None
                self.y_test = None
                self.train_indices = None
                self.test_indices = None

    def __str__(self):
        return f"{self.name} ({self.label}, {self.descriptors})"


class PredictionSet(BaseSet):
    def __init__(self, descriptors=None, name=None, compounds: List[Compound] = None):
        super().__init__(name, descriptors, compounds)

        fp = self.get_fp()

        self.X = DataFrame(fp, index=[cmp.db_id for cmp in self.compounds])
        self.y = Series([cmp.activity for cmp in self.compounds], index=[cmp.db_id for cmp in self.compounds])
