CLASS_LABELS = ['single-class-label', 'multi-class-label']

VALUE_LABELS = ['continuous-value']

SPLIT_ON_VALUE_LABELS = ['split-on-value']

ALL_LABELS = CLASS_LABELS + VALUE_LABELS + SPLIT_ON_VALUE_LABELS

json_constant_map = {
    '-Infinity': float('-Infinity'),
    'Infinity': float('Infinity'),
    'NaN': None,
}

METRICS = {
    'auc': 'AUC',
    'f1score': 'F1 Score',
    'precision': 'Precision',
    'recall': 'Recall',
    'acc': 'Accuracy',
    'specificity': 'Specificity',
    'cohens_kappa': "Cohen's Kappa",
    'mcc': 'MCC'
}

METRICS_EXT = {
    'auc_ext': 'AUC *',
    'f1score_ext': 'F1 Score *',
    'precision_ext': 'Precision *',
    'recall_ext': 'Recall *',
    'acc_ext': 'Accuracy *',
    'specificity_ext': 'Specificity *',
    'cohens_kappa_ext': "Cohen's Kappa *",
    'mcc_ext': 'MCC *'
}

PRIVILEGES = [
    dict(name='admin', description='Administrator'),
    dict(name='train', description='Train models'),
    dict(name='create', description='Create objects'),
    dict(name='predict', description='Predict'),
]
