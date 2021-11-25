""" Class for classic machine learning methods """
from abc import abstractmethod, ABC

from errors import JamlError
from stats import unify_metrics, get_class_stats, get_regr_stats


class SKLearnModel(ABC):
    def __init__(self, estimator, name: str, title: str, params: dict = None):
        self.estimator = estimator
        self.name = name
        self.title = title
        self.params = params
        self.model = None

    def __str__(self):
        return self.name

    @abstractmethod
    def fit(self, X_train, y_train, cv=None, callback=None, hyper_params=None) -> dict:
        pass

    def get_metrics(self, X, y) -> dict:
        if not self.model:
            raise JamlError(f"{self.name} model needs to be fit before calculating metrics")

        if self.name.endswith('r'):
            return get_regr_stats(self.model, X, y)
        else:
            return unify_metrics(get_class_stats(self.model, X, y, self.name))


def create_model(method: str, classifier_params: dict = {}, params: dict = None) -> SKLearnModel:
    pass


METHODS = []
METHODS_NAMES = [m.name for m in METHODS]
METHODS_META = {m.name: m.title for m in METHODS}
BOOSTER_METHODS = ['xgb', 'xgbr']
