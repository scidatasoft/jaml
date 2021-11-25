from db.JamlEntities import User
from errors import JamlError

USERS = [
    dict(id="603866ac373498658a7db464",
         username="admin",
         password_hash="931bd0e1cc9baae10e9ff6ca7002e834",
         full_name="System Administrator",
         email="admin@yourcompany.com",
         company="Your Company",
         privileges=["admin"]
         )
]


def authenticate(uid=None, username=None, password_hash=None):
    try:
        if uid:
            return User(**next(u for u in USERS if u['id'] == uid))
        elif username and password_hash:
            return User(**next(u for u in USERS if u['username'] == username and u['password_hash'] == password_hash))
        else:
            raise JamlError('Unauthorized')
    except StopIteration:
        raise JamlError('Unauthorized')
