""" Class for classic machine learning methods """
import copy
import pickle

import numpy as np
import sklearn.svm as svm
from keras.engine.saving import model_from_json
from sklearn.base import ClassifierMixin, BaseEstimator
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.linear_model import BayesianRidge
from sklearn.model_selection import GridSearchCV
from sklearn.naive_bayes import BernoulliNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.utils import class_weight

import stats
from deep_learning import BatchLogger, model_DNN_classifier
from models import SKLearnModel


class GridSearchModel(SKLearnModel):
    """ some models get parameters to grid search over """

    def __init__(self, classifier, name: str, title: str, params: dict):
        """
        params: model parameters to fit using cross validation
        """
        SKLearnModel.__init__(self, classifier, name, title, params)
        self.grid_search = None
        self.best_parameters = None

    def fit(self, X_train, y_train, cv=None, callback=None, hyper_params=None) -> dict:
        """ performs a grid search over the model parameters """
        hyper_search = GridSearchCV(self.estimator, self.params, cv=cv,
                                    scoring=stats.regress_scoring if self.name.endswith(
                                        'r') else stats.class_scoring,
                                    refit='R2' if self.name.endswith('r') else 'AUC')

        hyper_search.fit(X_train.values if 'values' in dir(X_train) else X_train, y_train)

        self.grid_search = hyper_search
        self.model = hyper_search.best_estimator_
        self.best_parameters = hyper_search.best_params_
        print(f"Best params {hyper_search.best_params_} out of {self.params}")

        return self.get_metrics(X_train, y_train)


class CalibratedModel(SKLearnModel):
    """ some models need to be calibrated """

    def __init__(self, classifier, name: str, title: str, params: dict):
        SKLearnModel.__init__(self, classifier, name, title, params)
        self.calibrated_model = None

    def fit(self, X_train, y_train, cv=None, callback=None, hyper_params=None) -> dict:
        """ calibrate the model """
        self.model = CalibratedClassifierCV(self.estimator, cv=cv, method='isotonic').fit(
            X_train.values if 'values' in dir(X_train) else X_train, y_train)

        return self.get_metrics(X_train, y_train)


class DNNClassifier(SKLearnModel, ClassifierMixin, BaseEstimator):

    def __init__(self, name: str, title: str, params: dict = None):
        """For DL actual classifier is built later, so None is passed to the base class"""
        SKLearnModel.__init__(self, None, name, title, params)
        self.classes_ = None

    def fit(self, X, y, cv=None, callback=None, hyper_params=None) -> dict:
        from keras.callbacks import ReduceLROnPlateau, EarlyStopping

        self.classes_ = np.unique(y)

        out_batch = BatchLogger(display=5)
        reduce_lr = ReduceLROnPlateau(monitor='loss', factor=0.9, patience=50, min_lr=0.00001, verbose=1)
        stopping = EarlyStopping(monitor='loss', min_delta=0.0, patience=200, verbose=1, mode='auto')
        callbacks = [reduce_lr, stopping, out_batch]
        if callback:
            callbacks.append(callback)

        batch_size = int(y.shape[0] // 5)
        num_steps = 10001

        X_values = X.values if 'values' in dir(X) else X
        y_values = y.values if 'values' in dir(y) else y

        # calculate class imbalance
        cw_tr_dict = class_weight.compute_class_weight('balanced', classes=np.unique(y_values), y=y_values)

        params = copy.deepcopy(self.params)
        if hyper_params:
            params.update(hyper_params)

        print(f"DNNClassifier: {params}")

        self.model = model_DNN_classifier(X_values.shape[1], **params)
        self.model.fit(X_values, y_values, epochs=num_steps, callbacks=callbacks,
                       batch_size=batch_size, class_weight=cw_tr_dict, verbose=0)

        return stats.unify_metrics(stats.get_class_stats(self.model, X, y, self.name))

    def predict(self, X):
        X_values = X.values if 'values' in dir(X) else X
        y_pred = self.model.predict_classes(X_values, verbose=0)[:, 0]
        return y_pred

    def predict_proba(self, X):
        X_values = X.values if 'values' in dir(X) else X
        y_pred = self.model.predict_proba(X_values, verbose=0)[:, 0]
        return y_pred

    def __getstate__(self):
        return dict(architecture=self.model.to_json(), model=pickle.dumps(self.model.get_weights()))

    def __setstate__(self, d):
        self.model = model_from_json(d['architecture'])
        self.model.set_weights(pickle.loads(d['model']))


def create_model(method: str, classifier_params: dict = {}, params: dict = None) -> SKLearnModel:
    if method == "bnb":
        cls = BernoulliNB(**classifier_params)
        return CalibratedModel(cls, 'bnb', 'BernoulliNB', params)

    elif method == "br":
        cls = BayesianRidge(**classifier_params)
        params = params if params is not None else dict(alpha_1=[1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8],
                                                        alpha_2=[1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8],
                                                        lambda_1=[1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8],
                                                        lambda_2=[1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8])
        return GridSearchModel(cls, 'br', 'BayesianRidge', params)

    elif method == "rf":
        cls = RandomForestClassifier(class_weight='balanced', random_state=42, **classifier_params)
        params = params if params is not None else dict(n_estimators=[50, 100, 150, 200], max_depth=[5, 10, 15, 20])
        return GridSearchModel(cls, 'rf', 'RandomForestClassifier', params)

    elif method == "ada":
        cls = AdaBoostClassifier(n_estimators=200, learning_rate=0.9, random_state=42, **classifier_params)
        return CalibratedModel(cls, 'ada', 'AdaBoostClassifier', params)

    elif method == "knn":
        cls = KNeighborsClassifier(metric='jaccard', **classifier_params)
        params = params if params is not None else dict(n_neighbors=[2, 3, 4, 5, 6, 7], weights=['uniform', 'distance'])
        return GridSearchModel(cls, 'knn', 'KNeighborsClassifier', params)

    elif method == "svc":
        cls = svm.SVC(gamma='scale', probability=True, class_weight='balanced', random_state=42,
                      **classifier_params)
        params = params if params is not None else dict(kernel=['linear', 'rbf', 'poly', 'sigmoid'],
                                                        C=[0.001, 0.01, 0.1, 1, 10, 100])
        return GridSearchModel(cls, 'svc', 'SVC', params)

    elif method == "xgb":
        from xgboost import XGBClassifier
        cls = XGBClassifier(probability=True, class_weight='balanced', random_state=42, **classifier_params)
        params = params if params is not None else dict(n_estimators=[50, 100, 150, 200],
                                                        learning_rate=[0.8, 0.9, 1.0, 1.1, 1.2],
                                                        booster=['gbtree', 'gblinear', 'dart'])
        return GridSearchModel(cls, 'xgb', 'XGBClassifier', params)

    elif method == "DL":
        params = params if params is not None else dict(num_hidden=[1024, 1024, 1024],
                                                        num_labels=1, dropout=0.5, beta=0.05,
                                                        l_rate=0.01, momentum=0.9, init_mode='he_normal',
                                                        optimizer='SGD', activation='relu', activation_out='sigmoid')
        return DNNClassifier('DL', 'Deep Learning', params)

    else:
        raise NotImplementedError
