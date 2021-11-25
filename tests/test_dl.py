import unittest

from keras.callbacks import ReduceLROnPlateau, EarlyStopping
from tensorflow import keras
from tensorflow.keras import layers

import config
import stats
from auth import delete_context_session
from datasets import DataSet
from db.JamlDbConfig import JamlDbConfig
from db.JamlMongo import JamlMongo
from deep_learning import BatchLogger, model_DNN_classifier
from utils.session_utils import create_session_by_uid


class TestDL(unittest.TestCase):

    def setUp(self):
        config.MONGO_HOST = 'localhost'
        config.MONGO_DB = 'jaml'
        config.MONGO_USERNAME = 'root'
        config.MONGO_PASSWORD = 'qqq123'

        JamlDbConfig()
        JamlMongo()

        self.token = create_session_by_uid("603866ac373498658a7db464")

    def tearDown(self):
        delete_context_session(close=True, token=self.token)

    def test_dataset(self):
        dataset = DataSet("602c84449c9494fcbcadcfaa", 'single-class-label',
                          [{"name": "FCFP", "params": {"Bits": "1024", "Radius": "3"}}], test_set_size=20)

        out_batch = BatchLogger(display=100)
        reduce_lr = ReduceLROnPlateau(monitor='loss', factor=0.9, patience=50, min_lr=0.00001, verbose=1)
        stopping = EarlyStopping(monitor='loss', min_delta=0.0, patience=200, verbose=1, mode='auto')
        callbacks = [reduce_lr, stopping, out_batch]

        batch_size = int(dataset.y.shape[0] // 3)
        num_steps = 10001

        model = model_DNN_classifier(input_dim=dataset.X.values.shape[1], dropout=0.7, beta=0.01)
        model.fit(dataset.X.values, dataset.y.values, epochs=num_steps, callbacks=callbacks, batch_size=batch_size)

        s = stats.get_class_stats(model, dataset.X, dataset.y)
        self.assertTrue(s)
        print(f"\nTraining: {s}\n")

        s = stats.get_class_stats(model, dataset.X_test, dataset.y_test)
        self.assertTrue(s)
        print(f"\nTesting: {s}\n")

    def test_layers(self):
        dataset = DataSet("602c84449c9494fcbcadcfaa", 'single-class-label',
                          [{"name": "FCFP", "params": {"Bits": "1024", "Radius": "3"}}], test_set_size=20)

        inputs = keras.Input(shape=(dataset.X.values.shape[1],), name="Input")
        x = layers.Dense(1024, activation="relu", name="dense_1")(inputs)
        x = layers.Dense(1024, activation="relu", name="dense_2")(x)
        x = layers.Dense(1024, activation="relu", name="dense_3")(x)
        outputs = layers.Dense(1, activation="softmax", name="predictions")(x)

        model = keras.Model(inputs=inputs, outputs=outputs)

        model.compile(optimizer=keras.optimizers.SGD(lr=0.01, nesterov=True),
                      loss='binary_crossentropy',
                      metrics=['binary_accuracy'])

        history = model.fit(dataset.X.values, dataset.y.values, batch_size=64, epochs=10000)
        print(history)

        s = stats.get_class_stats(model, dataset.X, dataset.y)
        self.assertTrue(s)
        print(f"\nTraining: {s}\n")

        s = stats.get_class_stats(model, dataset.X_test, dataset.y_test)
        self.assertTrue(s)
        print(f"\nTesting: {s}\n")
