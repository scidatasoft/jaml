#!/usr/bin/env python
import argparse
import datetime
import json
import logging as log
import os
import sys
import time
import traceback

from db.JamlDbConfig import JamlDbConfig
from features import load_features

log.basicConfig(level=log.INFO)
JamlDbConfig()
load_features()

from keras.callbacks import Callback

import config
from db.JamlEntities import JobInfo, Config
from db.JamlMongo import JamlMongo
from errors import JamlError
from jobs import MLJob
from variables import METHODS_NAMES
from predict import predict
from rabbit import RabbitMQ
from auth import create_session, set_context_session, delete_context_session
from utils.preps import configure_gpu
from utils.utils import Tee


class SaveToDatabase(Callback):

    def __init__(self, job_info, out, err, every=1000):
        super().__init__()
        self.job_info = job_info
        self.out = out
        self.err = err
        self.every = every

    def on_train_begin(self, logs=None):
        if self.job_info:
            self.job_info.stdout = self.out.getvalue()
            self.job_info.stderr = self.err.getvalue()
            self.job_info.save()

    def on_epoch_end(self, epoch, logs=None):
        if epoch % self.every == 0:
            if self.job_info:
                self.job_info.stdout = self.out.getvalue()
                self.job_info.stderr = self.err.getvalue()
                self.job_info.save()


def callback(ch, m, properties, body):

    db_cfg = Config.objects(name=config.PROFILE).first()
    if db_cfg.settings['version'] != config.VERSION:
        print('Restarting to accept version change...')
        exit()

    print(" [x] Received %r" % body)

    token = None
    job_info = None
    exit_code = False
    enter_time = time.time()
    try:
        params = json.loads(body)
        job_info = JobInfo.objects(id=params['job_id']).first()
        if not job_info:
            raise JamlError("Missing job info")

        job_info.server_name = config.SERVER_NAME
        job_info.container_name = config.CONTAINER_NAME
        job_info.save()

        session, _ = create_session(job_info.acl.owner)
        token = set_context_session(session)

        if params['job_type'] == 'train':
            run_train_job(ch, m, job_info, params)
            # if params['method'] == 'DL':
            #    print(" [x] Recycling to release GPU resources")
            #    exit_code = True

        elif params['job_type'] == 'predict':
            run_predict_job(ch, m, job_info, params)

        else:
            raise JamlError(f"Unsupported job type: {params['job_type']}")

        ch.basic_ack(delivery_tag=m.delivery_tag)

    except Exception as ex:
        ch.basic_nack(delivery_tag=m.delivery_tag, requeue=False)

        log.error(traceback.format_exc())

        if job_info:
            job_info.status = 'Failed'
            job_info.error = str(ex)
            job_info.stack_trace = traceback.format_exc()

        print(" [x] Recycling after error")
        exit_code = True  # It's easier to recycle process resource

    finally:
        if job_info:
            job_info.stats['execution_time'] = datetime.timedelta(seconds=time.time() - enter_time).seconds
            job_info.save()

        delete_context_session(close=True, token=token)

    if exit_code:
        exit()

    print(" [x] Done")


def run_train_job(ch, m, job_info, params) -> None:
    job = MLJob(**params)
    try:
        job_info.status = 'Running'
        job_info.save()

        with Tee(sys.stdout) as out, Tee(sys.stderr) as err:
            job.callback = SaveToDatabase(job_info, out, err)
            job.run()

        RabbitMQ.send_message(ch, "management", job.result)

        job_info.status = 'Failed' if job.result.error else 'Done'
        job_info.model_id = job.result.model_id

    finally:
        if out:
            job_info.stdout = out.getvalue()
        if err:
            job_info.stderr = err.getvalue()
            if not job_info.stderr:
                job_info.stderr = job.result.stack_trace
        job_info.save()


def run_predict_job(ch, m, job_info, params):
    try:
        job_info.status = 'Running'
        job_info.save()

        with Tee(sys.stdout) as out, Tee(sys.stderr) as err:
            predict(**params)

        job_info.status = 'Done'

    finally:
        if out:
            job_info.stdout = out.getvalue()
        if err:
            job_info.stderr = err.getvalue()
        job_info.save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Worker module")
    parser.add_argument("-q", "--queues", type=str, choices=METHODS_NAMES + ['ALL'], help="queues to listen on")
    args = parser.parse_args()

    if args.queues == 'ALL':
        args.queues = ','.join(METHODS_NAMES + ['predict'])

    queues = list(q.strip() for q in (args.queues if args.queues else os.getenv('QUEUES')).split(","))
    if not queues:
        print("Queues not defined")
        exit(-1)

    log.info(queues)

    if 'DL' in queues:
        configure_gpu()

    JamlMongo()

    rabbit = RabbitMQ(host=config.RABBIT_HOST, username=config.RABBIT_USERNAME, password=config.RABBIT_PASSWORD)
    rabbit.consume(queues, callback)
