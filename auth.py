from contextvars import ContextVar
from typing import Tuple

from mongoengine import Q

from db.JamlEntities import Session, User

session_var = ContextVar('session', default=None)


def set_context_session(session):
    return session_var.set(session)


def get_context_session():
    return session_var.get()


def delete_context_session(close=False, token=None):
    session = session_var.get()

    if session and close:
        session.active = False
        session.save()

    if token:
        session_var.reset(token)


def create_session(uid=None, username=None, password_hash=None, auth_function=None) -> Tuple[Session, User]:
    user = auth_function(uid, username, password_hash) if auth_function else authenticate(uid, username, password_hash)
    session = Session(user=user, privileges=user.privileges)
    session.save()
    return session, user


def authenticate(uid=None, username=None, password_hash=None):
    pass


def get_acl_query():
    session = session_var.get()
    if session and 'admin' in session.privileges:
        q = Q()
    else:
        access = ['public', 'authenticated'] if session else ['public']
        q = Q(acl__access__in=access)
        if session:
            q |= Q(acl__owner=str(session.user.id))
            q |= Q(acl__read=str(session.user.id))

    # print(q)
    return q


def is_authenticated():
    session = session_var.get()
    return True if session and session.user.id else False


def get_user():
    session = session_var.get()
    return session.user if is_authenticated() else None


def get_user_id():
    session = session_var.get()
    return str(session.user.id) if is_authenticated() else None


def has_privilege(privilege):
    session = session_var.get()
    return True if is_authenticated() and privilege in session.privileges else False


def is_admin():
    return has_privilege('admin')


def can_create():
    return is_admin() or has_privilege('create')


def can_train():
    return is_admin() or has_privilege('train')


def can_predict():
    return is_admin() or has_privilege('predict')


def has_valid_acl(item):
    return False if not item or 'acl' not in item or not item.acl else True


def is_owner(item):
    session = session_var.get()
    return False if not has_valid_acl(item) or not is_authenticated() or item.acl.owner != str(
        session.user.id) else True


def can_delete(item):
    return is_admin() or is_owner(item)


def can_acl(item):
    return is_admin() or is_owner(item)


def can_read(item):
    session = session_var.get()
    return is_admin() or is_owner(item) or \
           (item.acl.access == 'public' or item.acl.access == 'authenticated' and is_authenticated() or \
            is_authenticated() and has_valid_acl(item) and str(session.user.id) in item.acl.read)


def can_write(item):
    session = session_var.get()
    return is_admin() or is_owner(item) or \
           (is_authenticated() and has_valid_acl(item) and str(session.user.id) in item.acl.write)
