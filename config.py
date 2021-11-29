import os

GPU_MEMORY_FRACTION = 0.5

EMAIL_RECIPIENTS = [
    ("System Administrator", "admin@yourcompany.com")
]
EMAIL_HOST = "mail.host"
EMAIL_PORT = 25
EMAIL_FROM = "ml@sciencedataexperts.com"
EMAIL_LOGIN = None
EMAIL_PASSWORD = None
EMAIL_TLS = False

EMAIL_THRESHOLD = 100

MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = os.getenv('MONGO_PORT')
MONGO_DB = os.getenv('MONGO_DATABASE', 'jaml')
MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'root')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'qqq123')

RABBIT_HOST = os.getenv('RABBIT_HOST', 'localhost')
RABBIT_USERNAME = os.getenv('RABBIT_USERNAME', 'jaml')
RABBIT_PASSWORD = os.getenv('RABBIT_PASSWORD', 'qqq123')

SERVER_NAME = os.getenv('SERVER_NAME')
CONTAINER_NAME = os.getenv('CONTAINER_NAME')

PROFILE = os.getenv('PROFILE', 'default')

VERSION = os.getenv('VERSION', 'standard')

DEFAULT_USER = dict(
    username="admin",
    password_hash="0a197a5db6262529f793d739a5fc2ec7",
    email="admin@yourcompany.com",
    company="Your Company",
    privileges=["admin"],
    roles=[],
    active=True,
    full_name="System Administrator"
)

CONFIG = dict(
    default=dict(
        title="Just Another Machine Learner",
        logo="sde-logo.png",
        company="Science Data Experts",
        copyright="2021 &copy; Science Data Experts",
        links=[
            dict(icon='mdi-home', title='Company Home', url='http://www.sciencedataexperts.com/'),
            dict(icon='mdi-twitter', title='Twitter Profile', url='https://twitter.com/valery_tkachenk'),
            dict(icon='mdi-linkedin', title='LinkedIn Profile', url='https://www.linkedin.com/in/valerytkachenko/'),
            dict(icon='mdi-presentation-play', title='SlideShare Presentations',
                 url='https://www.slideshare.net/valerytkachenko16/'),
        ],
        home_text="""
        <h3>Just Another Machine Learner (JAML)</h3>
    
        <div>
          This app provides an easy way to create QSAR/QSPR models.     
        </div>
    """,
    ))

