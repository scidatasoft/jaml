#!/usr/bin/env python3
import io
import json
import logging as log
from tempfile import mkstemp

import auth
from db.JamlDbConfig import JamlDbConfig
from features import load_features, all_features

log.basicConfig(level=log.INFO)
JamlDbConfig()
load_features()

import connexion
from connexion.exceptions import OAuthProblem
from flask import send_file, abort, request, g
from flask_cors import CORS
from indigo import *
from indigo.renderer import IndigoRenderer
from mongoengine import DoesNotExist

import config
from auth import get_acl_query, can_read, set_context_session, delete_context_session, create_session, is_admin
from constants import PRIVILEGES

from errors import JamlError
from jobs import MLJob
from models import METHODS_META
from predict import schedule_predict, predict_structures
from utils.mime import MIME_TYPES
from utils.utils import file_remover, mongo_to_object
from variables import METHODS_META, FEATURES
from db.JamlEntities import Model, Dataset, Session, SDF, ResultSet, Blob, Config, Protocol
from db.JamlMongo import JamlMongo


def get_metadata():
    cfg = Config.objects(name=config.PROFILE).first()

    return dict(config=cfg.settings, methods=METHODS_META, features=FEATURES)


def get_features():
    return all_features()


def put_config(cfg):
    if not is_admin() or auth.get_user().username != 'admin':
        abort(403, description='Access denied')

    db_cfg = Config.objects(name=config.PROFILE).first()
    db_cfg.settings.update(cfg)
    db_cfg.save()


def put_version(version):
    pass


# SDFs
def get_files():
    filtered = SDF.objects(get_acl_query()).exclude("records")
    return list(json.loads(ds.to_json()) for ds in filtered)


def get_file(id):
    try:
        return json.loads(JamlMongo.get_file(id).to_json())
    except DoesNotExist:
        abort(404, description="Object not found")


def download_file(id, format: str = 'sdf'):
    try:
        if format == 'sdf':
            name, _bytes, content_type = JamlMongo.get_file_blob(id)
            return send_file(io.BytesIO(_bytes), as_attachment=True, attachment_filename=name, mimetype=content_type)

        elif format == 'xlsx':
            return download_file_xlsx(id)

        else:
            abort(400, description="Unsupported format")
    except DoesNotExist:
        abort(404, description="Object not found")


def download_file_xlsx(id):
    abort(403, description="Unavailable in your version")


def download_files(download_request):
    abort(403, description="Unavailable in your version")


def create_file(file, metadata, field_name, access):
    path, fd = None, None
    try:
        fd, path = mkstemp()
        file.save(path)
        if file.filename.lower().endswith('.zip'):
            abort(403, description="Unavailable in your version")
        else:
            return [JamlMongo.create_file(path, file.filename, metadata, field_name, access)]

    finally:
        if fd:
            os.close(fd)
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass


def post_file():
    try:
        files_number = int(connexion.request.form['files_number'])
        metadata = json.loads(connexion.request.form['metadata'])
        field_name = connexion.request.form['field_name']
        access = connexion.request.form['access']
        result = []

        for i in range(files_number):
            file = connexion.request.files['file' + str(i)]
            res = create_file(file, metadata, field_name, access)
            result.extend(res)

        return result

    except JamlError as ex:
        log.error(ex)
        abort(400, description=str(ex))


def preload_file():
    abort(403, description="Unavailable in your version")


def put_file(id, metadata):
    abort(403, description="Unavailable in your version")


def set_file_acl(id, acl):
    abort(403, description="Unavailable in your version")


def set_dataset_acl(id, acl):
    abort(403, description="Unavailable in your version")


def set_model_acl(id, acl):
    abort(403, description="Unavailable in your version")


def set_resultset_acl(id, acl):
    abort(403, description="Unavailable in your version")


def delete_file(id):
    try:
        JamlMongo.delete_file(id)
    except DoesNotExist:
        abort(404, description="Object not found")


def delete_files(ids):
    abort(403, description="Unavailable in your version")


# Datasets
def get_datasets():
    return list(json.loads(ds.to_json())
                for ds in
                Dataset.objects(get_acl_query()).exclude("records"))


def get_dataset(id):
    try:
        return json.loads(JamlMongo.get_dataset(id=id).to_json())
    except DoesNotExist:
        abort(404, description="Object not found")


def create_dataset(dataset_spec):
    try:
        result = []

        if not dataset_spec['mode'] or dataset_spec['mode'] == 'combine':
            dataset_spec['prefix'] = dataset_spec['suffix'] = None
            result.append(JamlMongo.create_dataset(dataset_spec))
        else:  # batch
            dataset_spec['name'] = None
            file_ids = dataset_spec['file_ids'].copy()
            for file_id in file_ids:
                dataset_spec['file_ids'] = [file_id]
                result.append(JamlMongo.create_dataset(dataset_spec))

        return result

    except JamlError as ex:
        log.error(ex)
        abort(400, description=str(ex))


def put_dataset(id, metadata):
    abort(403, description="Unavailable in your version")


def delete_dataset(id):
    try:
        JamlMongo.delete_dataset(id)
    except DoesNotExist:
        abort(404, description="Object not found")


def download_dataset(id, format: str = 'sdf'):
    try:
        ds = JamlMongo.get_dataset(id)
        path = None
        if format == 'sdf':
            path = download_dataset_sdf(ds)
        elif format == 'xlsx':
            path = download_dataset_xlsx(ds)
        else:
            abort(400, description="Unsupported format")

        if path:
            resp = send_file(path, mimetype=MIME_TYPES[format])
            file_remover.cleanup_once_done(resp, path)
            return resp

    except DoesNotExist:
        abort(404, description="Object not found")


def download_dataset_xlsx(ds):
    abort(403, description="Unavailable in your version")


def download_dataset_sdf(ds):
    abort(403, description="Unavailable in your version")


def get_dataset_protocol(id):
    try:
        return json.loads(Protocol.objects(id=id).first().to_json())
    except DoesNotExist:
        abort(404, description="Object not found")


def download_protocol(id, format='sdf'):
    abort(403, description="Unavailable in your version")


# Resultsets
def get_resultsets():
    return list(json.loads(ds.to_json()) for ds in ResultSet.objects(get_acl_query()).exclude("records"))


def get_resultset(id):
    try:
        return json.loads(JamlMongo.get_resultset(id=id).to_json())
    except DoesNotExist:
        abort(404, description="Object not found")


def create_resultset(dataset_spec):
    try:
        result = []

        if not dataset_spec['mode'] or dataset_spec['mode'] == 'combine':
            dataset_spec['prefix'] = dataset_spec['suffix'] = None
            rs = JamlMongo.create_resultset(dataset_spec)
            result.append(rs)

            if dataset_spec['model_ids']:
                schedule_predict([rs['_id']['$oid']], dataset_spec['model_ids'], dataset_spec['average_mode'],
                                 dataset_spec['average_name'])
        else:  # batch
            dataset_spec['name'] = None
            file_ids = dataset_spec['file_ids'].copy()
            for file_id in file_ids:
                dataset_spec['file_ids'] = [file_id]
                rs = JamlMongo.create_resultset(dataset_spec)
                result.append(rs)

                if dataset_spec['model_ids']:
                    schedule_predict([rs['_id']['$oid']], dataset_spec['model_ids'], dataset_spec['average_mode'],
                                     dataset_spec['average_name'])

        return result

    except JamlError as ex:
        log.error(ex)
        abort(400, description=str(ex))


def download_resultset(id, format):
    try:
        rs = JamlMongo.get_resultset(id=id)

        path = None
        if format == 'xlsx':
            path = download_resultset_xlsx(rs)
        elif format == 'sdf':
            path = download_resultset_sdf(rs)
        else:
            abort(400, description="Format not supported")

        if path:
            resp = send_file(path, mimetype=MIME_TYPES[format])
            file_remover.cleanup_once_done(resp, path)
            return resp

    except DoesNotExist:
        abort(404, description="Object not found")


def download_resultset_sdf(rs):
    abort(403, description="Unavailable in your version")
    return None


def download_resultset_xlsx(rs):
    abort(403, description="Unavailable in your version")
    return None


def put_resultset(id, metadata):
    abort(403, description="Unavailable in your version")


def delete_resultset(id):
    try:
        JamlMongo.delete_resultset(id)
    except DoesNotExist:
        abort(404, description="Object not found")


def predict_resultsets(predict_spec):
    try:
        return list(predict_structures(predict_spec['structures'], predict_spec['models']))
    except JamlError as ex:
        log.error(ex)
        abort(400, description=str(ex))


def get_resultset_validations(id):
    abort(403, description="Unavailable in your version")


# Models
def get_models(aggr: str = None, name: str = None):
    models = Model.objects(get_acl_query())
    return list(mongo_to_object(m) for m in models)


def get_model(id):
    try:
        mongo_model = Model.objects(id=id).first()
        if not mongo_model:
            raise DoesNotExist

        if not can_read(mongo_model):
            abort(403, description='Access forbidden by ACL')

        if not can_read(mongo_model.dataset):
            model = mongo_to_object(mongo_model)
        else:
            model = mongo_to_object(mongo_model.dataset)
            model.update(mongo_to_object(mongo_model))

        return model

    except DoesNotExist:
        abort(404, description="Object not found")


def delete_model(id):
    try:
        JamlMongo.delete_model(id)
    except DoesNotExist:
        abort(404, description="Object not found")


def train_models(models_spec):
    abort(403, description="Unavailable in your version")


def impute_models(impute_spec):
    abort(403, description="Unavailable in your version")


def download_models(download_request):
    abort(403, description="Unavailable in your version")


def download_model(id, format: str = 'sdf'):
    abort(403, description="Unavailable in your version")


def get_model_image(id, set_type=None, kind=None, size=200, format='png'):
    """ Get model image from database or generate a new one """
    model = Model.objects(id=id).first()
    if not model:
        abort(404, description="Object not found")

    # TODO Re-enable when X-Auth is set to Cookie
    # if not can_read(model):
    #    abort(403, description='Access forbidden by ACL')

    try:
        if not kind:
            kind = 'reg' if model.method_name.endswith('r') else 'roc'

        images = list(filter(lambda b: b.params['kind'] == kind and b.params['set_type'] == set_type, model.images))

        if images:
            return send_file(io.BytesIO(images[0].file.read()), mimetype=images[0].file.content_type)
        else:
            return send_file(MLJob.generate_model_image(model, set_type=set_type, kind=kind, size=size, format=format),
                             mimetype=MIME_TYPES[format])

    except JamlError as ex:
        abort(400, description=str(ex))


def predict_structs(predict_spec):
    res = predict_structures(predict_spec['structures'], predict_spec['models'])
    return list(res)


# Jobs
def get_jobs(status: str = None):
    abort(403, description="Unavailable in your version")


def delete_job(id):
    abort(403, description="Unavailable in your version")


def delete_jobs(what: str):
    abort(403, description="Unavailable in your version")


def get_job(id):
    abort(403, description="Unavailable in your version")


def put_job(id, job_spec):
    abort(403, description="Unavailable in your version")


def download_jobs(download_request):
    abort(403, description="Unavailable in your version")


# Images

def render_image(id, format_=None, size=None):
    if not format_:
        format_ = "svg"

    if not size:
        size = 100

    try:
        mol = JamlMongo.get_mol(id)

        indigo = Indigo()
        renderer = IndigoRenderer(indigo)
        indigo.setOption("ignore-stereochemistry-errors", True)
        indigo.setOption("render-output-format", format_)
        indigo.setOption("render-image-width", size)
        indigo.setOption("render-image-height", size)
        indigo.setOption("render-coloring", True)

        buf = renderer.renderToBuffer(indigo.loadMolecule(mol))
        return send_file(io.BytesIO(buf), mimetype=MIME_TYPES[format_])

    except DoesNotExist:
        abort(404, description="Object not found")

    except IndigoException as ex:
        log.error(ex)

    return None


def get_image(id):
    blob = Blob.objects(id=id).first()
    if blob is None:
        abort(404, description="Object not found")

    return send_file(io.BytesIO(blob.file.read()), mimetype=blob.file.content_type)


def login(login_spec):
    try:
        session, user = create_session(username=login_spec['username'], password_hash=login_spec['password_hash'])

        res = dict(user=mongo_to_object(user), session=mongo_to_object(session))

        res.update(dict(users=get_users()))

        if 'admin' in session.privileges:
            res.update(dict(privileges=PRIVILEGES))

        headers = {'X-Auth': session.id}
        return res, 200, headers

    except JamlError:
        abort(401, description='Invalid credentials')


def logout():
    sess_id = request.headers.get('X-Auth', None)
    if sess_id:
        if sess_id in sessions:
            del sessions[sess_id]

        session = Session.objects(id=sess_id).first()
        if session:
            session.active = False
            session.save()


def apikey_auth(token, required_scopes):
    session = Session.objects(id=token).first()
    if not session:
        raise OAuthProblem('Invalid token')

    if required_scopes:
        for scope in required_scopes:
            if scope not in session.privileges:
                raise OAuthProblem('Invalid scope')

    return dict(uid=session.user.id)


def get_users():
    abort(403, description="Unavailable in your version")


def get_user(id):
    abort(403, description="Unavailable in your version")


def create_user(user_spec):
    abort(403, description="Unavailable in your version")


def delete_users(ids):
    abort(403, description="Unavailable in your version")


def update_user(id, user_spec):
    abort(403, description="Unavailable in your version")


def delete_user(id):
    abort(403, description="Unavailable in your version")


def get_roles():
    abort(403, description="Unavailable in your version")


app = connexion.App(__name__)
app.add_api('swagger.yaml')
CORS(app.app, supports_credentials=True)
application = app.app
sessions = {}


@application.before_request
def set_api_user():
    sess_id = request.headers.get('X-Auth', None)
    if sess_id:
        if sess_id in sessions:
            g.token = set_context_session(sessions[sess_id])
        else:
            session = Session.objects(id=sess_id, active=True).first()
            if not session:
                raise OAuthProblem('Invalid token')

            sessions[sess_id] = session
            g.token = set_context_session(session)


@application.after_request
def reset_api_user(response):
    if 'token' in g and g.token:
        delete_context_session(token=g.token)

    return response


if __name__ == '__main__':
    JamlMongo()

    server = os.getenv('API_SERVER')
    server = server if server else None

    port = os.getenv('API_PORT')
    port = int(port) if port else 8100

    debug = os.getenv('API_DEBUG')
    debug = bool(debug) if debug else False

    app.run(server=server, port=port, debug=debug)
