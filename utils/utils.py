import json
import logging as log
import numbers
import numpy as np
import os
import shutil
import sys
import weakref
from io import StringIO

from bson import json_util
from tensorflow.python.client import device_lib

from constants import json_constant_map


def xstr(s):
    return '' if s is None else str(s)


def get_available_gpus():
    return device_lib.list_local_devices()


def clean_dir(folder: str):
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=True)


def assign(tgt, src):
    if isinstance(src, dict):
        for key in src:
            if isinstance(tgt, dict):
                tgt[key] = src[key]
            else:
                setattr(tgt, key, src[key])
    else:
        for key in dir(src):
            val = getattr(src, key, None)
            if not callable(val):
                if isinstance(tgt, dict):
                    tgt[key] = val
                else:
                    setattr(tgt, key, val)


class FileRemover(object):
    def __init__(self):
        self.weak_references = dict()  # weak_ref -> filepath to remove

    def cleanup_once_done(self, response, filepath):
        wr = weakref.ref(response, self._do_cleanup)
        self.weak_references[wr] = filepath

    def _do_cleanup(self, wr):
        filepath = self.weak_references[wr]
        try:
            if os.path.isdir(filepath):
                shutil.rmtree(filepath, ignore_errors=True)
            else:
                os.remove(filepath)
        except Exception as ex:
            log.debug('Error deleting {}: {}'.format(filepath, str(ex)))


file_remover = FileRemover()


class Tee(object):
    def __init__(self, stream):
        self.stream = stream
        self._str = StringIO()

        if stream == sys.stdout:
            self.stream_type = 'stdout'
        elif stream == sys.stderr:
            self.stream_type = 'stderr'

        if self.stream_type == 'stdout':
            sys.stdout = self
        elif self.stream_type == 'stderr':
            sys.stderr = self

    def write(self, data):
        self._str.write(data)
        self.stream.write(data)

    def flush(self):
        self._str.flush()
        self.stream.flush()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.stream_type == 'stdout':
            sys.stdout = self.stream
        elif self.stream_type == 'stderr':
            sys.stderr = self.stream

    def getvalue(self):
        return self._str.getvalue()


def custom_split(*arrays, test_size=0.25, random_state=42, stratify=None):
    from sklearn.utils import indexable
    from sklearn.utils.validation import _num_samples
    from itertools import chain
    from sklearn.utils import _safe_indexing
    from sklearn.model_selection._split import _validate_shuffle_split

    if isinstance(arrays[0], numbers.Integral):
        n_samples = arrays[0]
        arrays = [np.arange(n_samples), np.arange(n_samples)]
    else:
        arrays = indexable(*arrays)
        n_samples = _num_samples(arrays[0])

    n_train, n_test = _validate_shuffle_split(n_samples, test_size, None, default_test_size=0.25)

    if stratify is not None:
        from sklearn.model_selection import StratifiedShuffleSplit
        CVClass = StratifiedShuffleSplit
    else:
        from sklearn.model_selection import ShuffleSplit
        CVClass = ShuffleSplit

    cv = CVClass(test_size=n_test, train_size=n_train, random_state=random_state)

    train, test = next(cv.split(X=arrays[0], y=stratify))

    res = list(chain.from_iterable((_safe_indexing(a, train), _safe_indexing(a, test)) for a in arrays))
    res.extend([train, test])
    return res


def mongo_to_object(mongo_object):
    to_json = getattr(mongo_object, 'to_json', None)
    if to_json and callable(to_json):
        return json.loads(mongo_object.to_json(), parse_constant=lambda constant: json_constant_map[constant])
    else:
        return json.loads(json_util.dumps(mongo_object), parse_constant=lambda constant: json_constant_map[constant])
