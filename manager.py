#!/usr/bin/env python
import atexit
import json
import logging as log
import traceback

import config
from db.JamlDbConfig import JamlDbConfig
from features import load_features

log.basicConfig(level=log.INFO)
JamlDbConfig()
load_features()

from db.JamlMongo import JamlMongo

from rabbit import RabbitMQ
from utils.mail import send_email

jobs_results = []


def wrap_up():
    if jobs_results:
        send_email("Modeling job is completed", "job-completed.html", {"results": jobs_results})


atexit.register(wrap_up)


def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)

    try:
        job_result = json.loads(body)
        jobs_results.append(job_result)

        if len(jobs_results) >= config.EMAIL_THRESHOLD:
            try:
                send_email("Modeling jobs completed", "job-completed.html",
                           {"results": sorted(jobs_results, key=lambda r: r["dataset"])})
            except Exception as ex:
                log.error(ex)

            jobs_results.clear()

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as ex:
        ch.basic_nack(delivery_tag=method.delivery_tag)
        print(traceback.format_exc())


if __name__ == '__main__':
    JamlMongo()

    log.info("manager")

    rabbit = RabbitMQ(host=config.RABBIT_HOST, username=config.RABBIT_USERNAME, password=config.RABBIT_PASSWORD)
    rabbit.consume(["management"], callback)
