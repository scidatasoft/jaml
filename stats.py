import logging as log
from math import sqrt

import numpy
from sklearn import utils
from sklearn.metrics import cohen_kappa_score, matthews_corrcoef, precision_score, recall_score, confusion_matrix, \
    mean_squared_error, mean_poisson_deviance, mean_gamma_deviance, explained_variance_score, d2_tweedie_score
from sklearn.metrics import make_scorer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.metrics import roc_auc_score, roc_curve, auc, f1_score, accuracy_score


def std_metric_name(name: str) -> str:
    if name == 'Cohen\'s Kappa':
        return 'cohens_kappa'
    elif name == 'F1-Score':
        return 'f1score'
    else:
        return name.lower()


def unify_metrics(stats_dic) -> dict:
    return {std_metric_name(k): v for (k, v) in stats_dic.items()}


def cw_to_dict(y_class):
    """
    input: 1D array, labels
    output: balanced class weight dictionary
    """
    cw = utils.compute_class_weight('balanced', [0, 1], y_class)  # compute class weight
    cw_dict = {}
    for idx in range(len(cw)):
        cw_dict[idx] = cw[idx]
    return cw_dict


def get_class_stats(estimator, X, y_true, method_name=None):
    if not estimator:
        predicted_classes = X
        predicted_probas = X
    else:
        if 'predict_classes' in dir(estimator):
            predicted_classes = estimator.predict_classes(X.values if 'values' in dir(X) else X, verbose=0)[:, 0]
            predicted_probas = estimator.predict_proba(X.values if 'values' in dir(X) else X, verbose=0)[:, 0]
        else:
            predict = getattr(estimator, "predict", None)
            predict_proba = getattr(estimator, "predict_proba", None)
            predicted_classes, predicted_probas = None, None
            if callable(predict):
                predicted_classes = estimator.predict(X.values if 'values' in dir(X) else X)
            if callable(predict_proba):
                probas = estimator.predict_proba(X.values if 'values' in dir(X) else X)
                if method_name != "tsvc":
                    predicted_probas = probas[:, 1]
                else:
                    # Silly ThunderSVM issue of calculating probas
                    predicted_probas_0 = probas[:, 0]
                    roc_auc0, _, _ = auc_fpr_tpr(y_true, predicted_probas_0)
                    predicted_probas_1 = probas[:, 1]
                    roc_auc1, _, _ = auc_fpr_tpr(y_true, predicted_probas_1)
                    predicted_probas = predicted_probas_0 if roc_auc0 > roc_auc1 else predicted_probas_1

    acc, f1, roc_auc, cohen_kappa, matthews_corr, precision, recall, specificity, ba, fpr, tpr = \
        None, None, None, None, None, None, None, None, None, None, None

    if predicted_classes is not None:
        acc = accuracy_score(y_true, predicted_classes)
        f1 = f1_score(y_true, predicted_classes)
        cohen_kappa = cohen_kappa_score(y_true, predicted_classes)
        matthews_corr = matthews_corrcoef(y_true, predicted_classes)
        precision = precision_score(y_true, predicted_classes)
        recall = recall_score(y_true, predicted_classes)
        tn, fp, fn, tp = confusion_matrix(y_true, predicted_classes).ravel()
        specificity = tn / (tn + fp)
        ba = (recall + specificity) / 2

    if predicted_probas is not None:
        roc_auc, fpr, tpr = auc_fpr_tpr(y_true, predicted_probas)

    return {'ACC': acc, 'F1-Score': f1, 'AUC': roc_auc, 'Cohen\'s Kappa': cohen_kappa,
            'MCC': matthews_corr, 'Precision': precision,
            'Recall': recall, 'Specificity': specificity, 'BA': ba,
            'fpr': fpr.tolist() if fpr is not None else None,
            'tpr': tpr.tolist() if tpr is not None else None}


def auc_fpr_tpr(y_true, predicted_probas):
    # Sometimes SVM spits out probabilities with of inf so set them as 1
    predicted_probas[predicted_probas == numpy.inf] = 1
    try:
        fpr, tpr, _ = roc_curve(y_true, predicted_probas)
        roc_auc = auc(fpr, tpr)
        return roc_auc, fpr, tpr

    except ValueError as ex:
        log.error(ex)

    return None, None, None


def mpd(y_true, y_pred):
    try:
        return mean_poisson_deviance(y_true, y_pred)
    except ValueError as ex:
        log.warning(ex)
        return None


def mgd(y_true, y_pred):
    try:
        return mean_gamma_deviance(y_true, y_pred)
    except ValueError as ex:
        log.warning(ex)
        return None


def get_regr_stats(estimator, X, y_true):
    y_pred = estimator.predict(X.values if 'values' in dir(X) else X) if estimator else X
    metrics = dict(mae=mean_absolute_error(y_true, y_pred),
                   rmse=sqrt(mean_squared_error(y_true, y_pred)),
                   r2=r2_score(y_true, y_pred),
                   mpd=mpd(y_true, y_pred),
                   mgd=mgd(y_true, y_pred),
                   explained_variance=explained_variance_score(y_true, y_pred),
                   d2_tweedie_score=d2_tweedie_score(y_true, y_pred))
    return metrics


# scoring dictionary, just a dictionary containing the evaluation metrics passed through a make_scorer()
# fx, necessary for use in GridSearchCV

class_scoring = {'ACC': make_scorer(accuracy_score),
                 'F1-Score': make_scorer(f1_score),
                 'AUC': make_scorer(roc_auc_score),
                 'Cohen\'s Kappa': make_scorer(cohen_kappa_score),
                 'MCC': make_scorer(matthews_corrcoef),
                 'Precision': make_scorer(precision_score),
                 'Recall': make_scorer(recall_score)}

regress_scoring = {'MAE': make_scorer(mean_absolute_error),
                   'MSE': make_scorer(mean_squared_error),
                   'R2': make_scorer(r2_score)}
