import warnings
from unittest import TestCase

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn import datasets
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier

sns.set()
warnings.filterwarnings('ignore')


class TestCurves(TestCase):
    def test_roc(self):
        data = datasets.load_breast_cancer()

        X = data.data
        y = data.target

        X_train, X_test, y_train, y_test = train_test_split(X, y,
                                                            test_size=.25,
                                                            random_state=1234)

        # Instantiate the classfiers and make a list
        classifiers = [LogisticRegression(random_state=1234),
                       GaussianNB(),
                       KNeighborsClassifier(),
                       DecisionTreeClassifier(random_state=1234),
                       RandomForestClassifier(random_state=1234)]

        # Define a result table as a DataFrame
        result_table = pd.DataFrame(columns=['classifiers', 'fpr', 'tpr', 'auc'])

        # Train the models and record the results
        for cls in classifiers:
            model = cls.fit(X_train, y_train)
            pp = model.predict_proba(X_test)
            yproba = pp[::, 1]

            fpr, tpr, _ = roc_curve(y_test, yproba)
            auc = roc_auc_score(y_test, yproba)

            result_table = result_table.append({'classifiers': cls.__class__.__name__,
                                                'fpr': fpr,
                                                'tpr': tpr,
                                                'auc': auc}, ignore_index=True)

        # Set name of the classifiers as index labels
        result_table.set_index('classifiers', inplace=True)

        fig = plt.figure(figsize=(8, 6))

        for i in result_table.index:
            plt.plot(result_table.loc[i]['fpr'],
                     result_table.loc[i]['tpr'],
                     label="{}, AUC={:.3f}".format(i, result_table.loc[i]['auc']))

        plt.plot([0, 1], [0, 1], color='orange', linestyle='--')

        plt.xticks(np.arange(0.0, 1.1, step=0.1))
        plt.xlabel("Flase Positive Rate", fontsize=15)

        plt.yticks(np.arange(0.0, 1.1, step=0.1))
        plt.ylabel("True Positive Rate", fontsize=15)

        plt.title('ROC Curve Analysis', fontweight='bold', fontsize=15)
        plt.legend(prop={'size': 13}, loc='lower right')

        plt.show()

        fig.savefig('multiple_roc_curve.png')
