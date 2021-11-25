from getpass import getpass

from mongoengine import connect

import config
from db.JamlEntities import User, Config


class JamlDbConfig:
    def __init__(self, silent: bool = True):
        if silent:
            self.host = config.MONGO_HOST
        else:
            self.host = input(f"Host [{config.MONGO_HOST}]: ").strip()
            if not self.host:
                self.host = config.MONGO_HOST

        self.port = config.MONGO_PORT

        self.database = config.MONGO_DB

        if silent:
            self.username = config.MONGO_USERNAME
        else:
            self.username = input(f"User [{config.MONGO_USERNAME}]: ").strip()
            if not self.username:
                self.username = config.MONGO_USERNAME

        if silent:
            self.password = config.MONGO_PASSWORD
        else:
            self.password = getpass().strip()
            if not self.password:
                self.password = config.MONGO_PASSWORD

        print(f"Connecting to: {self}...")

        connect(self.database, host=self.host, port=self.port,
                username=self.username, password=self.password, authentication_source='admin')

        JamlDbConfig.initialize()

    @staticmethod
    def initialize():
        user = User.objects(username=config.DEFAULT_USER['username']).first()
        if not user:
            user = User(**config.DEFAULT_USER)
            user.save()

        cfg = Config.objects(name=config.PROFILE).first()
        if not cfg:
            cfg = Config(name=config.PROFILE, settings=config.CONFIG[config.PROFILE])
            cfg.save()

    def __str__(self):
        return f"{self.username}@{self.host}:{self.port}/{self.database}"
