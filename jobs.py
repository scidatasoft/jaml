import datetime
import io
import json
import logging as log
import platform
import time
import traceback
from abc import ABC, abstractmethod

import matplotlib.pyplot as plt
import seaborn as sn
from bson import json_util
from matplotlib.figure import Figure
from sklearn import model_selection
from sklearn.model_selection import ShuffleSplit

import config
from auth import can_train, get_user_id
from datasets import DataSet
from db.JamlEntities import Blob, ACL, JobInfo
from db.JamlMongo import JamlMongo
from errors import JamlError
from features import feature
from models import SKLearnModel, METHODS, METHODS_NAMES
from rabbit import RabbitMQ
from stats import std_metric_name
from utils.mime import MIME_TYPES
from variables import METHODS, METHODS_NAMES

sn.set()


class ModelingResult:
    def __init__(self, metrics, execution_time: float, error: str = None, stack_trace: str = None):
        self.metrics = metrics
        self.execution_time = execution_time
        self.error = error
        self.stack_trace = stack_trace
        self.model_id = None

    def __bool__(self):
        return bool(self.error)

    def __str__(self):
        return f"{self.metrics} in {self.execution_time}s"


class Job(ABC):
    """ Abstract base class for ML jobs """

    def __init__(self):
        self.enter_time = None
        self.exit_time = None

    def run(self):
        self.on_before()
        self.enter_time = time.time()
        self.on_run()
        self.exit_time = time.time()
        self.on_after()

    def on_before(self):
        pass

    @abstractmethod
    def on_run(self):
        pass

    def on_after(self):
        pass

    def execution_time(self):
        return datetime.timedelta(seconds=self.exit_time - self.enter_time)


class MLJob(Job):

    def __init__(self, ds_id=None, method=None, hyper_params=None, label=None, descriptors=None, model_name=None,
                 force=None,
                 test_set_size=None, train_indices=None, test_indices=None, **kwargs):
        super().__init__()
        self.ds_id = ds_id
        self.method = method
        self.hyper_params = hyper_params
        self.label = label
        self.descriptors = descriptors
        self.model_name = model_name
        self.force = force
        self.test_set_size = test_set_size
        self.train_indices = train_indices
        self.test_indices = test_indices
        self.result = None
        self.node = platform.node()
        self.callback = None
        self.dataset = None

    def on_before(self):
        if not can_train():
            raise JamlError('Access forbidden by ACL')

        self.dataset = DataSet(self.ds_id, self.label, self.descriptors, self.test_set_size, self.train_indices,
                               self.test_indices)

    def on_run(self):
        self.result = self.run_dataset(METHODS[METHODS_NAMES.index(self.method)])

    def on_after(self):
        # FIXME Run ensemble methods after each iteration... which is NOT good
        ens_methods = list(m for m in feature('ml-methods') if m.startswith('stack') or m.startswith('vote'))
        if ens_methods:
            regression = self.method.endswith('r')
            try:
                from enterprise.models import StackingModel, VotingModel

                models = JamlMongo.get_models_ensemble(self.model_name, regression)
                if len(models) > 1:
                    estimators = list((m[1].method_name, m[0]) for m in models)

                    # If there is stacking
                    model = None
                    if regression:
                        if 'stack_r' in ens_methods:
                            model = StackingModel(estimators, "stack_r", "StackingRegressor")
                    else:
                        if 'stack' in ens_methods:
                            model = StackingModel(estimators, "stack_c", "StackingClassifier")

                    if model:
                        self.run_dataset(model)

                    # If there is voting
                    model = None
                    if regression:
                        if 'vote_r' in ens_methods:
                            model = VotingModel(estimators, "vote_r", "VotingRegressor")
                    else:
                        if 'vote_c' in ens_methods:
                            model = VotingModel(estimators, "vote_c", "VotingClassifier")

                    if model:
                        self.run_dataset(model)

            except ImportError:
                pass

    def run_dataset(self, skl_model: SKLearnModel) -> ModelingResult:
        start_time = time.time()

        print(f" * {self.dataset.name}/{skl_model.name}", end="... ", flush=True)

        try:
            hyper_params = self.hyper_params.get(self.method, None) if self.hyper_params else None

            metrics = {}

            # k-fold split
            if skl_model.name == "DL":
                cv = model_selection.StratifiedKFold(shuffle=True, n_splits=5, random_state=42)
            elif skl_model.name.endswith('r'):
                cv = ShuffleSplit(n_splits=5, random_state=42)
            else:
                cv = model_selection.StratifiedKFold(shuffle=True, n_splits=5, random_state=42)

            # fit and metrics
            _metrics = skl_model.fit(self.dataset.X_train, self.dataset.y_train, cv, self.callback, hyper_params)
            for k, v in _metrics.items():
                metrics[f'{std_metric_name(k)}'] = v

            # test set exists - get test metrics
            if self.test_set_size:
                _metrics = skl_model.get_metrics(self.dataset.X_test, self.dataset.y_test)
                for k, v in _metrics.items():
                    metrics[f'{std_metric_name(k)}_ext'] = v

            # save model
            result = ModelingResult(metrics, time.time() - start_time)
            mongo_model = JamlMongo.create_model(self.model_name, self.dataset, skl_model, self.descriptors, self.label,
                                                 result)

            # generate images
            if self.dataset.test_set_size:
                MLJob.generate_model_image(mongo_model, set_type='test', dataset=self.dataset, model=skl_model.model)
            else:
                MLJob.generate_model_image(mongo_model, dataset=self.dataset, model=skl_model.model)

            if self.test_set_size:
                # Re-train the model on the whole set
                skl_model.model.fit(self.dataset.X.values if 'values' in dir(self.dataset.X) else self.dataset.X,
                                    self.dataset.y)
                JamlMongo.serialize_model(mongo_model, skl_model)

                # update metrics
                _metrics = skl_model.get_metrics(self.dataset.X, self.dataset.y)
                for k, v in _metrics.items():
                    metrics[f'{std_metric_name(k)}'] = v
                mongo_model.metrics = metrics

                # regenerate image as it should reflect the whole set
                MLJob.generate_model_image(mongo_model, dataset=self.dataset, model=skl_model.model)

                mongo_model.save()

            result.model_id = json.loads(json_util.dumps(mongo_model.id))['$oid']

        except Exception as ex:
            log.exception(ex)
            execution_time = time.time() - start_time
            result = ModelingResult(None, execution_time, error=str(ex), stack_trace=traceback.format_exc())

        print(f" * done: {result}")

        return result

    @staticmethod
    def generate_model_image(mongo_model, set_type=None, kind=None, dataset=None, model=None, size=200,
                             format='png'):

        if set_type != 'test':
            set_type = None

        """ Generate and save ROC or REG image """
        fig = Figure(figsize=(size / 100., size / 100.), constrained_layout=True)
        ax = fig.subplots()

        if not kind:
            kind = 'reg' if mongo_model.method_name.endswith('r') else 'roc'

        if kind == 'roc':
            if mongo_model.metrics.get('fpr', None) and mongo_model.metrics.get('tpr', None):
                ax.plot(mongo_model.metrics['fpr' if not set_type else 'fpr_ext'],
                        mongo_model.metrics['tpr' if not set_type else 'tpr_ext'])
            else:
                plt.close(fig)

        elif kind == 'reg':
            if not model:
                model, _ = JamlMongo.get_model(mongo_model.id)
            if not dataset:
                dataset = DataSet(mongo_model.dataset.id, mongo_model.label, mongo_model.descriptors)

            data = dict(y=dataset.y.values if not set_type else dataset.y_test.values,
                        y_pred=model.predict(dataset.X.values if not set_type else dataset.X_test.values))
            sn.regplot(x='y', y='y_pred', data=data, ax=ax, marker="+")

        else:
            plt.close(fig)
            raise JamlError("Unknown plot kind")

        buf = io.BytesIO()
        fig.savefig(buf, format=format)
        plt.close(fig)

        blob = Blob(params=dict(kind=kind, set_type=set_type))
        buf.seek(0)
        blob.file.put(buf, content_type=MIME_TYPES[format])
        blob.save()

        mongo_model.images.append(blob)
        mongo_model.save()

        buf.seek(0)
        return buf

    @staticmethod
    def schedule(dataset, method, model_name, hyper_params=None) -> dict:

        with RabbitMQ(host=config.RABBIT_HOST, username=config.RABBIT_USERNAME,
                      password=config.RABBIT_PASSWORD) as rabbit:

            params = dict(job_type='train', ds_id=dataset.ds_id, ds_name=dataset.name,
                          model_name=model_name, method=method, hyper_params=hyper_params)
            acl = ACL(access='private', owner=get_user_id())
            job = JobInfo(job_type='train', params=params, status='Created', acl=acl)
            job.save()

            try:
                params.update(dict(
                    job_id=json.loads(json_util.dumps(job.id))['$oid'],
                    label=dataset.label,
                    descriptors=dataset.descriptors,
                    test_set_size=dataset.test_set_size,
                    train_indices=dataset.train_indices if dataset.train_indices is not None else None,
                    test_indices=dataset.test_indices if dataset.test_indices is not None else None
                ))
                rabbit.publish(method, params)

                job.params = params
                job.save()

                return params
            except:
                job.delete()
                raise

    @staticmethod
    def reschedule(job):

        with RabbitMQ(host=config.RABBIT_HOST, username=config.RABBIT_USERNAME,
                      password=config.RABBIT_PASSWORD) as rabbit:
            rabbit.publish(job.params['method'], job.params)
            job.status = 'Rescheduled'
            job.save()
