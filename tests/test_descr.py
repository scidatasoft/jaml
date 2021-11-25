from unittest import TestCase

import requests

from config import PADEL_API, MORDRED_API, TOXPRINTS_API, WEBTEST_API


class TestDescriptors(TestCase):
    def test_PaDEL_get(self):
        response = requests.get(f"{PADEL_API}?smiles=CCCC")
        o = response.json()
        self.assertEqual(o["info"]["name"], "PaDEL")
        self.assertEqual(len(o["chemicals"]), 1)
        self.assertEqual(len(o["chemicals"][0]["descriptors"]), 1444)

    def test_PaDEL_post(self):
        response = requests.post(PADEL_API,
                                 json=dict(chemicals=["CCCC", "CCCCC"], options=dict(computeFingerprints=True)))
        o = response.json()
        self.assertEqual(o["info"]["name"], "PaDEL")
        self.assertEqual(len(o["chemicals"]), 2)
        self.assertEqual(len(o["chemicals"][0]["descriptors"]), 2325)

    def test_MORDRED_get(self):
        response = requests.get(f"{MORDRED_API}?smiles=CCCC")
        o = response.json()
        self.assertEqual(o["info"]["name"], "mordred")
        self.assertEqual(len(o["chemicals"]), 1)
        self.assertEqual(len(o["chemicals"][0]["descriptors"]), 1613)

    def test_MORDRED_post(self):
        response = requests.post(MORDRED_API, json=dict(chemicals=["CCCC", "CCCCC"]))
        o = response.json()
        self.assertEqual(o["info"]["name"], "mordred")
        self.assertEqual(len(o["chemicals"]), 2)
        self.assertEqual(len(o["chemicals"][0]["descriptors"]), 1613)

    def test_Toxprints_get(self):
        response = requests.get(f"{TOXPRINTS_API}?smiles=CCCC")
        o = response.json()
        self.assertEqual(o["info"]["name"], "Toxprints")
        self.assertEqual(len(o["chemicals"]), 1)
        self.assertEqual(len(o["chemicals"][0]["descriptors"]), 729)

    def test_Toxprints_post(self):
        response = requests.post(TOXPRINTS_API, json=dict(chemicals=["CCCC", "CCCCC"]))
        o = response.json()
        self.assertEqual(o["info"]["name"], "Toxprints")
        self.assertEqual(len(o["chemicals"]), 2)
        self.assertEqual(len(o["chemicals"][0]["descriptors"]), 729)

    def test_WebTEST_get(self):
        response = requests.get(f"{TOXPRINTS_API}?smiles=CCCC")
        o = response.json()
        self.assertEqual(o["info"]["name"], "WebTEST")
        self.assertEqual(len(o["chemicals"]), 1)
        self.assertEqual(len(o["chemicals"][0]["descriptors"]), 729)

    def test_WebTEST_post(self):
        response = requests.post(TOXPRINTS_API, json=dict(chemicals=["CCCC", "CCCCC"]))
        o = response.json()
        self.assertEqual(o["info"]["name"], "WebTEST")
        self.assertEqual(len(o["chemicals"]), 2)
        self.assertEqual(len(o["chemicals"][0]["descriptors"]), 729)
