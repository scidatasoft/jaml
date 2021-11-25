#!/usr/bin/env python
import json
import logging as log
from tempfile import mkstemp
from typing import Tuple

import pandas as pd
import seaborn as sn
from bson import json_util, ObjectId
from mongoengine import DoesNotExist, Q
from rdkit import Chem
from sklearn.metrics import confusion_matrix

import config
from auth import get_user_id, can_predict, get_acl_query
from datasets import PredictionSet, Compound
from db.JamlEntities import ResultSet, ValidationStats, JobInfo, Model, ACL, Blob
from db.JamlMongo import JamlMongo
from errors import JamlError
from rabbit import RabbitMQ
from stats import unify_metrics, get_class_stats, get_regr_stats


def make_prediction_set(id_: str) -> Tuple[PredictionSet, ResultSet]:
    rs = ResultSet.objects(id=id_).first()
    if not rs:
        raise DoesNotExist(f"ResultSet[{id_}] does not exist")

    compounds = [Compound(None, None, Chem.MolFromMolBlock(r.molecule.mol)) for r in rs.records]

    return PredictionSet(rs.name, compounds), rs


def make_predictions(prediction_set: PredictionSet, rs: ResultSet, model_ids: list, average_name):
    if not model_ids:
        raise JamlError('model_ids not specified')

    result = []
    preds = {}
    try:
        binary_field = next(f['name'] for f in rs.fields_mapping if f['type'] == 'single-class-label')
        y_binary_true = [int(float(r.fields[binary_field])) if r.fields[binary_field] else 0 for r in rs.records]
    except StopIteration:
        binary_field = None
        y_binary_true = None

    try:
        cont_field = next(f['name'] for f in rs.fields_mapping if f['type'] == 'continuous-value')
        y_cont_true = [float(r.fields[cont_field]) if r.fields[cont_field] else 0 for r in rs.records]
    except StopIteration:
        cont_field = None
        y_cont_true = None

    binary = None
    for model_id in model_ids:
        model, mongo_model = JamlMongo.get_model(model_id)
        if binary is None:
            binary = not mongo_model.method_name.endswith('r')
        try:
            X_prediction = prediction_set.X

            if mongo_model.method_name != 'DL':
                y_pred = model.predict(X_prediction.values)
            else:
                y_pred = model.predict_classes(X_prediction.values, verbose=0)[:, 0]

            preds[mongo_model.method_name] = y_pred

            if binary_field:
                metrics = unify_metrics(get_class_stats(model, X_prediction, y_binary_true, mongo_model.method_name))
            elif cont_field:
                metrics = get_regr_stats(model, X_prediction, y_cont_true)
            else:
                metrics = None

            field_name = f"{mongo_model.name}/{mongo_model.method_name}"
            if not any(f['name'] == field_name for f in rs.fields_mapping):
                rs.fields_mapping.append(dict(name=field_name, type='predicted-value'))
                for r, y in zip(rs.records, y_pred):
                    if binary:
                        r.fields[field_name] = int(y)
                    else:
                        r.fields[field_name] = float(y)

            if mongo_model not in rs.models:
                rs.models.append(mongo_model)

            if binary and y_binary_true:
                add_valid_stats(rs, field_name, y_binary_true, y_pred, metrics)

        except Exception as ex:
            log.exception(ex)
            result.append(str(ex))

    if average_name and (binary and len(model_ids) > 2 or len(model_ids) > 1):
        df = pd.DataFrame.from_dict(preds)
        consensus = df.mean(1)
        if binary:
            df.loc[(consensus >= 0.5), 'avg'] = 1
            df.loc[(consensus < 0.5), 'avg'] = 0
        else:
            df.loc[:, 'avg'] = consensus

        field_name = f"{average_name}/avg"
        if not any(f['name'] == field_name for f in rs.fields_mapping):
            rs.fields_mapping.append(dict(name=field_name, type='predicted-value'))
            for r, y in zip(rs.records, df.loc[:, 'avg']):
                r.fields[field_name] = (int(y) if binary else float(y))

        if binary and y_binary_true:
            metrics = unify_metrics(get_class_stats(None, df.loc[:, 'avg'], y_binary_true, 'avg'))
            add_valid_stats(rs, field_name, y_binary_true, df.loc[:, 'avg'], metrics)
        elif not binary and y_cont_true:
            metrics = get_regr_stats(None, df.loc[:, 'avg'], y_cont_true)

    rs.save()

    return result


def add_valid_stats(rs, model, y_true, y_pred, metrics):
    valid_stats = ValidationStats(model=model, metrics=metrics)

    # add_cm(valid_stats, y_pred, y_true)

    rs.valid_stats.append(valid_stats)


def add_cm(valid_stats, y_pred, y_true):
    cm = confusion_matrix(y_true, y_pred)
    svm = sn.heatmap(cm, annot=True, cmap='Blues')
    figure = svm.get_figure()
    _, path = mkstemp('.png')
    figure.savefig(path)
    with open(path, "rb") as fd:
        img = Blob()
        img.file.put(fd)
        img.save()
        valid_stats.img_id = img.id

    # os.remove(path)


def predict(rs_ids=None, model_ids=None, average_mode=None, average_name=None, **kwargs):
    if not can_predict():
        raise JamlError('Access forbidden by ACL')

    result = []
    for rs_id in rs_ids:
        pred_set, rs = make_prediction_set(rs_id)
        if average_mode == 'individual':
            result.extend(make_predictions(pred_set, rs, model_ids, None))

        elif average_mode == 'name':
            for model_name in model_ids:
                # Classification methods
                cls_ids = [m.id for m in Model.objects(Q(name=model_name) & get_acl_query()).only('id', 'method_name')
                           if not m.method_name.endswith('r')]
                # Regression methods
                reg_ids = [m.id for m in Model.objects(Q(name=model_name) & get_acl_query()).only('id', 'method_name')
                           if m.method_name.endswith('r')]

                if cls_ids:
                    result.extend(
                        make_predictions(pred_set, rs, cls_ids, model_name if not reg_ids else f"{model_name}-cls"))
                if reg_ids:
                    result.extend(
                        make_predictions(pred_set, rs, reg_ids, model_name if not cls_ids else f"{model_name}-reg"))

        elif average_mode == 'all':
            # Classification methods
            cls_ids = []
            for model_name in model_ids:
                cls_ids.extend(
                    [m.id for m in Model.objects(Q(name=model_name) & get_acl_query()).only('id', 'method_name')
                     if not m.method_name.endswith('r')])
            if cls_ids:
                result.extend(make_predictions(pred_set, rs, cls_ids, average_name if average_name else 'all-cls'))

            # Regression methods
            reg_ids = []
            for model_name in model_ids:
                reg_ids.extend(
                    [m.id for m in Model.objects(Q(name=model_name) & get_acl_query()).only('id', 'method_name')
                     if m.method_name.endswith('r')])
            if reg_ids:
                result.extend(make_predictions(pred_set, rs, reg_ids, average_name if average_name else 'all-reg'))

    return result


def predict_structures(structures, models):
    result = []

    for model_name in models:
        if ObjectId.is_valid(model_name):
            res = make_structures_predictions(structures, [model_name])
        else:
            res = make_structures_predictions(structures, [model.id for model in Model.objects(name=model_name)])

        result.append(res)

    return result


def make_structures_predictions(structures: list, model_ids: list):
    preds = {}

    binary = None
    model_name = None
    for model_id in model_ids:
        try:
            model, mongo_model = JamlMongo.get_model(model_id)
            if not model_name:
                model_name = mongo_model.name

            prediction_set = PredictionSet(descriptors=mongo_model.descriptors,
                                           compounds=[Compound(None, None, Chem.MolFromSmiles(s)) for s in structures])

            if binary is None:
                binary = not mongo_model.method_name.endswith('r')

            X_prediction = prediction_set.X
            if mongo_model.method_name != 'DL':
                y_pred = model.predict(X_prediction.values)
            else:
                y_pred = model.predict_classes(X_prediction.values, verbose=0)[:, 0]

            preds[mongo_model.method_name] = y_pred

        except Exception as ex:
            log.error(ex)

    if len(preds.keys()) > 2:
        df = pd.DataFrame.from_dict(preds)
        consensus = df.mean(1)
        if binary:
            df.loc[(consensus >= 0.5), 'avg'] = 1
            df.loc[(consensus < 0.5), 'avg'] = 0
        else:
            df.loc[:, 'avg'] = consensus

        preds['avg'] = df.loc[:, 'avg']

    res = [
        dict(structure=s,
             predictions=[
                 dict(model=model_name,
                      method=k,
                      value=float(v[i]))
                 for k, v in preds.items()
             ])
        for (i, s) in enumerate(structures)
    ]

    return res


def schedule_predict(rs_ids, model_ids, average_mode, average_name):
    with RabbitMQ(host=config.RABBIT_HOST, username=config.RABBIT_USERNAME,
                  password=config.RABBIT_PASSWORD) as rabbit:

        params = dict(job_type='predict', rs_ids=rs_ids, model_ids=model_ids, average_mode=average_mode,
                      average_name=average_name)
        acl = ACL(access='private', owner=str(get_user_id()))
        job = JobInfo(job_type='predict', params=params, status='Created', acl=acl)
        job.save()

        try:
            params['job_id'] = json.loads(json_util.dumps(job.id))['$oid']
            rabbit.publish('predict', params)
            return params
        except:
            job.delete()
            raise
