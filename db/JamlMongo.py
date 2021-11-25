"""
JamlDb is a mongodb interface to Jaml
"""
import json
import logging
import math
import pickle
import tempfile

from bson import ObjectId
from flask import abort
from indigo import *
from mongoengine import *
from tensorflow.keras.models import model_from_json

import basic.models
from auth import can_read, can_write, can_delete, can_create, get_acl_query, get_user_id
from chem.SimpleStdizer import SimpleStdizer
from chem.readers import get_records_reader
from constants import CLASS_LABELS, VALUE_LABELS, SPLIT_ON_VALUE_LABELS
from db.JamlEntities import SDF, Molecule, Dataset, Protocol, StdizerRecord, Issue, DatasetCompound, ResultSet, Model, \
    Descriptors, StructureRecord, ACL
from errors import JamlError
from models import SKLearnModel, BOOSTER_METHODS
from utils import mime
from utils.utils import xstr, mongo_to_object

log = logging.getLogger(__name__)


class JamlMongo:
    def __init__(self, silent: bool = True):
        pass

    @staticmethod
    def get_file(id: str):
        sdf = SDF.objects(id=id).first()
        if sdf is None:
            raise DoesNotExist

        if not can_read(sdf):
            abort(403, description='Access forbidden by ACL')

        return sdf

    @staticmethod
    def get_file_blob(id: str) -> tuple:
        sdf = SDF.objects(id=id).first()
        if sdf is None:
            raise DoesNotExist

        if not can_read(sdf):
            abort(403, description='Access forbidden by ACL')

        return sdf.name, sdf.file.read(), sdf.file.content_type

    @staticmethod
    def update_file(id: str, metadata: dict):
        sdf = SDF.objects(id=id).first()
        if sdf is None:
            raise DoesNotExist

        if not can_write(sdf):
            abort(403, description='Access forbidden by ACL')

        if 'name' in metadata:
            sdf.name = metadata['name']
            del metadata['name']
        sdf.metadata = metadata
        sdf.save()

        sdf.records = None
        return json.loads(sdf.to_json())

    @staticmethod
    def delete_file(id: str):
        sdf = SDF.objects(id=id).first()
        if sdf is None:
            raise DoesNotExist

        if not can_delete(sdf):
            abort(403, description='Access forbidden by ACL')

        sdf.delete()

    @staticmethod
    def get_mol(id: str) -> str:
        mol = Molecule.objects(id=id).only("mol").first()
        if mol is None:
            raise DoesNotExist

        return mol.mol

    # Datasets
    @staticmethod
    def list_datasets(start: int = 0, count: int = None) -> list:
        return list(json.loads(ds.to_json())
                    for ds in
                    Dataset.objects.exclude("records"))

    @staticmethod
    def get_dataset(id: str):
        if ObjectId.is_valid(id):
            ds = Dataset.objects(id=id).first()
        else:
            ds = Dataset.objects(name=id).first()

        if ds is None:
            raise DoesNotExist

        if not can_read(ds):
            abort(403, description='Access forbidden by ACL')

        return ds

    class FieldsOptions:
        def __init__(self, class_field=None, value_field=None, split_on_value_field=None,
                     op_value=None, op_split=None, threshold=None):
            self.class_field = class_field
            self.value_field = value_field
            self.split_on_value_field = split_on_value_field
            self.op_value = op_value
            self.op_split = op_split
            self.threshold = threshold

    @staticmethod
    def create_dataset(dataset_spec: dict):
        if not can_create():
            abort(403, description='Access forbidden by ACL')

        file_ids = dataset_spec["file_ids"]
        if not file_ids:
            raise JamlError(f"Empty files list")

        # Deal with the label/value fields
        class_field, _, _ = JamlMongo.find_field(dataset_spec, CLASS_LABELS)
        value_field, op_value, _ = JamlMongo.find_field(dataset_spec, VALUE_LABELS)
        split_on_value_field, op_split, threshold = JamlMongo.find_field(dataset_spec, SPLIT_ON_VALUE_LABELS)

        if not class_field and not value_field and not split_on_value_field:
            raise JamlError(f"'label' or 'value' field(s) are not specified")
        if class_field and split_on_value_field:
            raise JamlError(f"Both 'single-class-label' and 'split-on-value' field are specified")
        if split_on_value_field and op_split not in ['lt', 'le', 'ge', 'gt']:
            raise JamlError(f"Invalid op '{op_split}'")

        n_actives = 0
        low_value = None
        high_value = None

        dataset_name = None
        metadata = None
        protocol = Protocol(name=dataset_spec['stdizer'])
        ds = Dataset(protocol=protocol, fields_mapping=dataset_spec["fields_mapping"])

        new_structures = []
        for file_id in file_ids:
            sf = SDF.objects(id=file_id).first()
            if not sf:
                raise DoesNotExist(f"SDF[{file_id}] not found")

            if not can_read(sf):
                abort(403, description='Access forbidden by ACL')

            if not sf.fields_mapping:
                sf.fields_mapping = dataset_spec["fields_mapping"]
                if can_write(sf):
                    sf.save()

            if dataset_spec['mode'] == 'batch' or not dataset_name:
                dataset_name = f"{xstr(dataset_spec['prefix'])}{dataset_spec['name'] if dataset_spec['name'] else sf.name.rsplit('.', 1)[0]}{xstr(dataset_spec['suffix'])}"

            if not metadata:
                metadata = sf.metadata

            if Dataset.objects(name=dataset_name).first():
                raise JamlError(f"{dataset_name} already exist")

            print(f" [+] {dataset_name}", end="... ", flush=True)

            ds.files.append(sf)

            fo = JamlMongo.FieldsOptions(class_field=class_field, value_field=value_field,
                                         split_on_value_field=split_on_value_field, op_value=op_value,
                                         op_split=op_split, threshold=threshold)
            n_actives, low_value, high_value = JamlMongo.create_dataset_records(ds, sf, dataset_spec, new_structures,
                                                                                fo, n_actives, low_value, high_value)

        ds.name = dataset_name
        ds.metadata = metadata
        ds.acl = sf.acl

        if n_actives:
            ds.stats["actives"] = n_actives
            ds.stats["inactives"] = len(ds.records) - n_actives

        if low_value is not None:
            ds.stats["low_value"] = low_value
            ds.stats["high_value"] = high_value

        # Add new split-on-value activity field
        if split_on_value_field:
            ds.fields_mapping.append(dict(name=f'{split_on_value_field}_active', type='single-class-label'))

        if new_structures:
            Molecule.objects.insert(new_structures)

        protocol.records_number = len(protocol.records)
        if protocol.records_number:
            protocol.save()
        else:
            ds.protocol = None

        ds.records_number = len(ds.records)
        ds.save()

        print(f"{len(ds.records)}.")

        # Save on return size
        ds.protocol = None
        ds.records = None

        return json.loads(ds.to_json())

    @staticmethod
    def create_dataset_records(ds, sf, dataset_spec, new_structures, fo, n_actives, low_value, high_value):
        stdizer = SimpleStdizer()
        inchi_keys = set()

        for r in sf.records:
            print(".", end="", flush=True)

            fields_values = {f["name"]: r.fields[f["name"]] for f in dataset_spec["fields_mapping"] if
                             f["type"] and f["name"] in r.fields}
            sr = StdizerRecord(file=sf, ord=r.ord, file_fields=fields_values, mol_org=r.molecule)

            res = stdizer.standardize(r.molecule.mol)
            for issue in res.issues:
                sr.issues.append(Issue(severity=issue[0], message=issue[1]))

            inchi, inchi_key = res.inchi()
            if inchi_key in inchi_keys:
                sr.issues.append(Issue(severity='Warning', message='Duplicate record removed'))
                ds.protocol.records.append(sr)
                continue

            if not res:
                ds.protocol.records.append(sr)
                continue

            inchi_keys.add(inchi_key)

            if res.changed():
                inchi_org, _ = res.inchi(original=True)
                sr.issues.append(Issue(severity='Debug', message=f"Org: {inchi_org}"))
                sr.issues.append(Issue(severity='Debug', message=f"Std: {inchi}"))

            molecule = Molecule.objects(inchi_key=inchi_key).first()
            if not molecule:
                molecule = Molecule(inchi_key=inchi_key, inchi=inchi, mol=res.mol())
                new_structures.append(molecule)

            fields_values = {f["type"]: r.fields[f["name"]] for f in dataset_spec["fields_mapping"] if
                             f["type"] and f["name"] in r.fields}

            skip = False
            if fo.class_field:
                try:
                    active = int(bool(float(r.fields[fo.class_field])))
                    n_actives += active

                except Exception as ex:
                    sr.issues.append(Issue(severity='Error', message=str(ex)))
                    skip = True

            if fo.value_field:
                try:
                    value = float(r.fields[fo.value_field])
                    if fo.op_value:
                        if fo.op_value == 'log':
                            value = math.log(value, 10)
                            fields_values['continuous-value'] = value
                        else:
                            raise JamlError(f"Invalid op {fo.op_value}")

                    if not low_value or value < low_value:
                        low_value = value
                    if not high_value or value > high_value:
                        high_value = value

                except Exception as ex:
                    sr.issues.append(Issue(severity='Error', message=str(ex)))
                    skip = True

            if fo.split_on_value_field:
                try:
                    value = float(r.fields[fo.split_on_value_field])
                    if fo.op_split == 'lt':
                        active = int(value < fo.threshold)
                    elif fo.op_split == 'le':
                        active = int(value <= fo.threshold)
                    elif fo.op_split == 'ge':
                        active = int(value >= fo.threshold)
                    elif fo.op_split == 'gt':
                        active = int(value > fo.threshold)
                    else:
                        raise JamlError(f"Invalid op {fo.op_split}")

                    n_actives += active

                    fields_values['single-class-label'] = active

                except Exception as ex:
                    sr.issues.append(Issue(severity='Error', message=str(ex)))
                    skip = True

            if not skip:
                cmp = DatasetCompound(ord=r.ord, fields=fields_values, molecule=molecule)
                ds.records.append(cmp)

            if res.changed() or len(sr.issues) > 0:
                sr.mol_std = molecule
                sr.ds_fields = fields_values
                ds.protocol.records.append(sr)

        return n_actives, low_value, high_value

    @staticmethod
    def update_dataset(id: str, metadata: dict):
        ds = Dataset.objects(id=id).first()
        if ds is None:
            raise DoesNotExist

        if not can_write(ds):
            abort(403, description='Access forbidden by ACL')

        if 'name' in metadata:
            ds.name = metadata['name']
            del metadata['name']
        ds.metadata = metadata
        ds.save()

        ds.records = None
        return json.loads(ds.to_json())

    @staticmethod
    def delete_dataset(id: str):
        ds = Dataset.objects(id=id).first()
        if ds is None:
            raise DoesNotExist

        if not can_delete(ds):
            abort(403, description='Access forbidden by ACL')

        ds.delete()

    @staticmethod
    def get_dataset_compounds(id: str, label: str) -> list:
        if ObjectId.is_valid(id):
            ds = Dataset.objects(id=id).first()
        else:
            ds = Dataset.objects(name=id).first()

        if ds is None:
            raise DoesNotExist

        if not can_read(ds):
            abort(403, description='Access forbidden by ACL')

        return list(
            dict(db_id=c.ord, value=c.fields[label], mol=c.molecule.mol) for c in ds.records if label in c.fields)

    # Resultsets
    @staticmethod
    def get_resultset(id: str) -> ResultSet:
        if ObjectId.is_valid(id):
            rs = ResultSet.objects(id=id).first()
        else:
            rs = ResultSet.objects(name=id).first()

        if rs is None:
            raise DoesNotExist

        if not can_read(rs):
            abort(403, description='Access forbidden by ACL')

        return rs

    @staticmethod
    def create_resultset(dataset_spec: dict):
        if not can_create():
            abort(403, description='Access forbidden by ACL')

        file_ids = dataset_spec["file_ids"]
        if not file_ids:
            raise JamlError(f"Empty files list")

        value_field, op_value, _ = JamlMongo.find_field(dataset_spec, VALUE_LABELS)

        resultset_name = None
        metadata = None
        protocol = Protocol(name=dataset_spec['stdizer'])
        rs = ResultSet(protocol=protocol, fields_mapping=dataset_spec["fields_mapping"])

        stdizer = SimpleStdizer()
        new_structures = []
        for file_id in file_ids:
            sf = SDF.objects(id=file_id).first()
            if not sf:
                raise DoesNotExist(f"SDF[{file_id}] not found")

            if not can_read(sf):
                abort(403, description='Access forbidden by ACL')

            if not sf.fields_mapping:
                sf.fields_mapping = dataset_spec["fields_mapping"]
                if can_write(sf):
                    sf.save()

            if dataset_spec['mode'] == 'batch' or not resultset_name:
                resultset_name = f"{xstr(dataset_spec['prefix'])}{dataset_spec['name'] if dataset_spec['name'] else sf.name.rsplit('.', 1)[0]}{xstr(dataset_spec['suffix'])}"

            if not metadata:
                metadata = sf.metadata

            if ResultSet.objects(name=resultset_name).first():
                raise JamlError(f"{resultset_name} already exist")

            print(f" [+] {resultset_name}", end="... ", flush=True)

            rs.files.append(sf)

            for r in sf.records:
                fields_values = {f["name"]: r.fields[f["name"]] for f in dataset_spec["fields_mapping"] if
                                 f["type"] and f["name"] in r.fields}
                sr = StdizerRecord(file=sf, ord=r.ord, file_fields=fields_values, mol_org=r.molecule)

                res = stdizer.standardize(r.molecule.mol)
                for issue in res.issues:
                    sr.issues.append(Issue(severity=issue[0], message=issue[1]))

                inchi, inchi_key = res.inchi()

                if not res:
                    rs.protocol.records.append(sr)
                    continue

                if res.changed():
                    inchi_org, _ = res.inchi(original=True)
                    sr.issues.append(Issue(severity='Debug', message=f"Org: {inchi_org}"))
                    sr.issues.append(Issue(severity='Debug', message=f"Std: {inchi}"))

                molecule = Molecule.objects(inchi_key=inchi_key).first()
                if not molecule:
                    molecule = Molecule(inchi_key=inchi_key, inchi=inchi, mol=res.mol())
                    new_structures.append(molecule)

                if value_field:
                    try:
                        value = float(r.fields[value_field])
                        if op_value:
                            if op_value == 'log':
                                value = math.log(value, 10)
                                fields_values[value_field] = value
                            else:
                                raise JamlError(f"Invalid op {op_value}")
                    except Exception as ex:
                        sr.issues.append(Issue(severity='Warning', message=str(ex)))

                cmp = DatasetCompound(ord=r.ord, fields=fields_values, molecule=r.molecule)
                rs.records.append(cmp)

                if res.changed() or len(sr.issues) > 0:
                    sr.mol_std = molecule
                    sr.ds_fields = fields_values
                    rs.protocol.records.append(sr)

        rs.name = resultset_name
        rs.metadata = metadata
        rs.acl = sf.acl

        if new_structures:
            Molecule.objects.insert(new_structures)

        protocol.records_number = len(protocol.records)
        if protocol.records_number:
            protocol.save()
        else:
            rs.protocol = None

        rs.records_number = len(rs.records)
        rs.save()

        print(f"{len(rs.records)}.")

        # Save on return size
        rs.protocol = None
        rs.records = None

        return json.loads(rs.to_json())

    @staticmethod
    def delete_resultset(id: str):
        rs = ResultSet.objects(id=id).first()
        if rs is None:
            raise DoesNotExist

        if not can_delete(rs):
            abort(403, description='Access forbidden by ACL')

        rs.delete()

    @staticmethod
    def get_resultset_compounds(name: str) -> list:
        rs = ResultSet.objects(name=name).first()
        if rs is None:
            raise DoesNotExist

        if not can_read(rs):
            abort(403, description='Access forbidden by ACL')

        return list(dict(db_id=c.fields['single-class-label'] or c.ord, mol=c.molecule.mol) for c in rs.records)

    @staticmethod
    def update_resultset(id: str, metadata: dict):
        rs = ResultSet.objects(id=id).first()
        if rs is None:
            raise DoesNotExist

        if not can_write(rs):
            abort(403, description='Access forbidden by ACL')

        if 'name' in metadata:
            rs.name = metadata['name']
            del metadata['name']
        rs.metadata = metadata
        rs.save()

        rs.records = None
        return json.loads(rs.to_json())

    # Models
    @staticmethod
    def list_models(ids: list) -> list:
        if not ids:
            return list(mongo_to_object(m) for m in Model.objects(get_acl_query()))
        else:
            res = []
            for id in ids:
                if ObjectId.is_valid(id):
                    m = Model.objects(Q(id=id) & get_acl_query()).first()
                    res.append(m)
                else:
                    ms = Model.objects(Q(name=id) & get_acl_query())
                    res.extend(ms)

            return list(mongo_to_object(m) for m in res)

    @staticmethod
    def create_model(model_name: str, dataset, model: SKLearnModel, descriptors, label, result):
        ds = Dataset.objects(name=dataset.name).only("name", "acl").first()
        if ds is None:
            raise DoesNotExist

        if not can_read(ds):
            abort(403, description='Access forbidden by ACL')

        if not model_name:
            model_name = dataset.name
        mongo_model = Model.objects(name=model_name, method_name=model.name).only("name", "method_name", "acl").first()

        # We can recalculate existing model
        if mongo_model is not None:
            log.warning(f'Model {model_name}/{model.name} already exists - deleting')
            mongo_model.delete()

        acl = ACL(access=ds.acl.access, owner=get_user_id(), read=ds.acl.read, write=ds.acl.write)
        mongo_model = Model(name=model_name, method_name=model.name, label=label, acl=acl)

        mongo_model.dataset = ds
        mongo_model.params = model.params

        for d in descriptors:
            mongo_model.descriptors.append(
                Descriptors(provider=d['provider'] if 'provider' in d else None,
                            name=d['name'],
                            params=d['params'] if 'params' in d else None))

        JamlMongo.serialize_model(mongo_model, model)

        mongo_model.acl = ds.acl
        mongo_model.acl.owner = get_user_id()

        mongo_model.test_set_size = dataset.test_set_size
        mongo_model.train_indices = list(dataset.train_indices) if dataset.train_indices else None
        mongo_model.test_indices = list(dataset.test_indices) if dataset.test_indices else None
        mongo_model.metrics = result.metrics
        mongo_model.execution_time = result.execution_time
        mongo_model.save()

        return mongo_model

    @staticmethod
    def serialize_model(mongo_model, model: SKLearnModel):
        if model.name == "DL":
            mongo_model.architecture = model.model.to_json()
            mongo_model.model = pickle.dumps(model.model.get_weights())
        elif mongo_model.method_name in BOOSTER_METHODS:
            with tempfile.NamedTemporaryFile(delete=False) as tf:
                tmp_name = tf.name
            try:
                model.model.save_model(tmp_name)
                with open(tmp_name, "rb") as f:
                    mongo_model.model = f.read()
            finally:
                os.remove(tmp_name)
        elif mongo_model.method_name in ['tsvc', 'tsvr']:
            mongo_model.model = model.model.save_to_string()
        else:
            mongo_model.model = pickle.dumps(model.model)

    @staticmethod
    def is_model_exist(name, method_name) -> bool:
        return Model.objects(name=name, method_name=method_name).only("name", "method_name").first() is not None

    @staticmethod
    def get_model(id, method_name=None) -> tuple:
        if ObjectId.is_valid(id):
            mongo_model = Model.objects(id=id).first()
        else:
            mongo_model = Model.objects(name=id, method_name=method_name).first()

        if not mongo_model:
            raise DoesNotExist

        if not can_read(mongo_model):
            abort(403, description='Access forbidden by ACL')

        model = JamlMongo.load_model(mongo_model)

        return model, mongo_model

    @staticmethod
    def get_models_ensemble(name, regression: bool) -> list:
        result = []
        for mongo_model in filter(
                lambda mm: not mm.method_name.startswith("stack") and not mm.method_name.startswith("vote"),
                Model.objects(name=name)):
            if regression and mongo_model.method_name.endswith(
                    'r') or not regression and not mongo_model.method_name.endswith('r'):
                if mongo_model.method_name == 'DL':
                    model = basic.models.create_model('DL')
                    model.model = JamlMongo.load_model(mongo_model)
                else:
                    model = JamlMongo.load_model(mongo_model)

                result.append([model, mongo_model])

        return result

    @staticmethod
    def load_model(mongo_model):
        if mongo_model.method_name == "DL":
            model = model_from_json(mongo_model.architecture)
            model.set_weights(pickle.loads(mongo_model.model.read()))
        elif mongo_model.method_name == "xgb":
            from xgboost import XGBClassifier
            model = XGBClassifier()
            model.load_model(bytearray(mongo_model.model.read()))
        elif mongo_model.method_name == "xgbr":
            from xgboost import XGBRegressor
            model = XGBRegressor()
            model.load_model(bytearray(mongo_model.model.read()))
        elif mongo_model.method_name == "tsvc":
            from enterprise.models import TSVC
            model = TSVC(probability=True, class_weight='balanced', random_state=42)
            model.load_from_string(mongo_model.model.read())
        elif mongo_model.method_name == "tsvr":
            from thundersvm import SVR
            model = SVR()
            model.load_from_string(mongo_model.model.read())
        else:
            try:
                model = pickle.loads(mongo_model.model.read())
            except pickle.UnpicklingError:
                raise JamlError("Unsupported model format")
        return model

    @staticmethod
    def delete_model(id: str):
        if ObjectId.is_valid(id):
            model = Model.objects(id=id).first()
            if model is None:
                raise DoesNotExist

            if not can_delete(model):
                abort(403, description='Access forbidden by ACL')

            model.delete()
        else:
            for model in Model.objects(name=id):
                if not can_delete(model):
                    abort(403, description='Access forbidden by ACL')
                model.delete()

    @staticmethod
    def find_field(dataset_spec, labels):
        class_fields = list([m for m in dataset_spec["fields_mapping"] if m["type"] in labels])
        if len(class_fields) > 0:
            return class_fields[0]["name"], \
                   class_fields[0]["op"] if "op" in class_fields[0] else None, \
                   float(class_fields[0]["value"]) if class_fields[0]["value"] else None
        else:
            return None, None, None

    @staticmethod
    def create_file(path: str, name: str, metadata: dict = None, field_name=None, access='public'):
        if not can_create():
            abort(403, description='Access forbidden by ACL')

        if not os.path.exists(path):
            raise FileNotFoundError(path)

        dir, _filename = os.path.split(path.replace("\\", "/"))

        if name is None:
            name = _filename

        if not metadata and dir:
            metadata = dict(project=dir.rsplit(":", 1).pop().strip("/").replace("/", "_"))

        sf = SDF.objects(name=name).first()
        if sf is not None:
            raise JamlError(f'{name} already exists')

        print(f" [+] {name}", end="")

        sf = SDF(name=name)
        sf.save()

        try:
            sf.size = os.path.getsize(path)

            with open(path, "rb") as fd:
                sf.file.put(fd, filename=name, content_type=mime.get_content_type(name))

            new_structures = []
            records = []
            fields = []
            inchi_keys = set()

            n_skipped = 0
            i = 0

            for rec in get_records_reader(path, name, field_name):
                i += 1

                if not rec or not rec.inchi_key:
                    print("!", end="", flush=True)
                    n_skipped += 1
                    continue
                else:
                    inchi_keys.add(rec.inchi_key)

                s = Molecule.objects(inchi_key=rec.inchi_key).only("id").first()
                if s is not None:
                    print(".", end="", flush=True)
                else:
                    s = next((s for s in new_structures if s.inchi_key == rec.inchi_key), None)
                    if s is not None:
                        print("*", end="", flush=True)
                    else:
                        s = Molecule(inchi_key=rec.inchi_key, inchi=rec.inchi, mol=rec.mol())
                        print("+", end="", flush=True)
                        new_structures.append(s)

                sr = StructureRecord(ord=i - 1, molecule=s)
                sr.fields = rec.props
                fields.extend([f for f in sr.fields.keys() if f not in fields])

                records.append(sr)

            if new_structures:
                Molecule.objects.insert(new_structures)

            sf.metadata = metadata
            sf.fields = fields
            sf.records_number = i - n_skipped
            sf.records = records
            sf.acl = ACL(owner=str(get_user_id()), access=access)
            sf.save()

            print(f"\n [ ] {len(records)} records, {len(new_structures)} new, {n_skipped} skipped")

        except:
            sf.delete()
            raise

        return json.loads(sf.to_json())
