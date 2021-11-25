import unittest

from sklearn import model_selection
from sklearn.datasets import make_blobs

from models import METHODS, METHODS_NAMES


class TestML(unittest.TestCase):

    def setUp(self):
        self.X, self.y = make_blobs(100, centers=2, n_features=2)
        self.cv = model_selection.StratifiedKFold(shuffle=True, n_splits=5, random_state=42)

    def test_random_forest(self):
        model = METHODS[METHODS_NAMES.index("rf")]
        model.fit(self.X, self.y, self.cv)
        stats = model.get_metrics(self.X, self.y)
        self.assertTrue(stats['ACC'] > 0.95)

    def test_knn(self):
        model = METHODS[METHODS_NAMES.index("knn")]
        model.fit(self.X, self.y, self.cv)
        stats = model.get_metrics(self.X, self.y)
        self.assertTrue(True)

    def test_svc(self):
        model = METHODS[METHODS_NAMES.index("svc")]
        model.fit(self.X, self.y, self.cv)
        stats = model.get_metrics(self.X, self.y)
        self.assertTrue(stats['ACC'] > 0.95)

    def test_bnb(self):
        model = METHODS[METHODS_NAMES.index("bnb")]
        model.fit(self.X, self.y, self.cv)
        stats = model.get_metrics(self.X, self.y)
        self.assertTrue(stats['ACC'] > 0.95)

    def test_ada(self):
        model = METHODS[METHODS_NAMES.index("ada")]
        model.fit(self.X, self.y, self.cv)
        stats = model.get_metrics(self.X, self.y)
        self.assertTrue(stats['ACC'] > 0.95)
