import logging as log
import multiprocessing

from flask import abort

from basic.auth import USERS
from datasets import DataSet
from db.JamlEntities import Model
from errors import JamlError
from jobs import MLJob
from utils.preps import select_gpu
from utils.utils import mongo_to_object, xstr


def train_models(models_spec):
    def fp_suffix(descrs, test_set_size):
        res = '-'.join(f"{d['name']}{int(d['params']['Radius']) * 2}-{d['params']['Bits']}" for d in descrs)
        if test_set_size:
            res = f"{res}-{test_set_size}"
        return res

    if len(models_spec['ds_ids']) == 0:
        raise JamlError('No datasets')

    if len(models_spec['ds_ids']) > 1:
        models_spec['name'] = None

    try:
        results = []
        for ds_id in models_spec['ds_ids']:
            dataset = None

            for method in models_spec['methods']:
                for label in models_spec['label_fields']:
                    if label == 'single-class-label' and method.endswith('r') or \
                            label == 'continuous-value' and not method.endswith('r'):
                        continue

                    if not dataset:
                        dataset = DataSet(ds_id, label, test_set_size=models_spec['test_set_size'])
                        # assign it afterwards to avoid descriptors generation at dataset creation
                        dataset.descriptors = models_spec['descriptors']

                    if models_spec['name']:
                        model_name = models_spec['name']
                    else:
                        model_name = f"{xstr(models_spec['prefix'])}{dataset.name}{xstr(models_spec['suffix'])}"
                        if models_spec['auto_name']:
                            model_name = f"{model_name}-{fp_suffix(models_spec['descriptors'], models_spec['test_set_size'])}"

                    if models_spec['force']:
                        for m in Model.objects(name=model_name):
                            m.delete()

                    res = MLJob.schedule(dataset, method, model_name, models_spec.get('hyper_params', None))
                    results.append(res)

        return results

    except JamlError as ex:
        log.error(ex)
        abort(400, description=str(ex))


def train_models_sync(models_spec):
    try:
        select_gpu()
        results = []
        jobs = []
        for ds_id in models_spec['ds_ids']:
            for method in models_spec['methods']:
                for label in models_spec['label_fields']:
                    process = multiprocessing.Process(target=run_training,
                                                      args=(ds_id, label, method, models_spec, results))
                    jobs.append(process)

        for j in jobs:
            j.start()

        for j in jobs:
            j.join()

        return results

    except JamlError as ex:
        log.error(ex)
        abort(400, description=str(ex))


def run_training(ds_id, label, method, models_spec, results):
    job = MLJob(ds_id, method, label, models_spec['descriptors'], models_spec['name'], models_spec['force'],
                models_spec['test_set_size'])
    try:
        job.run()
    except Exception as ex:
        log.error(str(ex))
        results.append(str(ex))

    results.append(job.result)


def get_users():
    return list(mongo_to_object(u) for u in USERS)
