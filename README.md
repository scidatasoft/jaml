# Just Another Machine Learner (JAML)

## TLDR

JAML is a simple Python-based framework supporting full cycle of QSAR model development.


## List of supported Machine Learning methods

* Naive Bayes classifier
* Bayesian regression
* Random Forest classifier
* AdaBoost
* k-NN classifier
* SVM classifier
* Deep Learning

## JAML workflow

JAML workflow consists of the following steps:

* File submission
* Dataset creation
* Model training
* Prediction

## Datamodel objects

* Files - submitted as SDF or CSV.
* Datasets - created from files by assigning semantic columns values (e.g. record id, continuous value, etc). All structures in datasets are standardized using one of the chosen standardizers. 
* Models - trained from datasets by selecting the field (binary or continuous), descriptors and ML method(s).
* Resultsets (predictions) - similar to datasets, but result in predictions are attached as additional columns.

## Running

### API

```shell
python app.py
```

### UI

For UI configuration and running please see [UI README](jaml_ui/README.md)