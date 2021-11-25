import standard.auth
from auth import create_session
from auth import set_context_session


def create_session_by_uid(uid: str):
    session, _ = create_session(uid=uid, auth_function=standard.auth.authenticate)
    token = set_context_session(session)
    return token
