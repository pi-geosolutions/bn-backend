import os
import logging
from flask_compress import Compress
import configs


class BaseConfig(object):
    DEBUG = False
    TESTING = False
    # sqlite :memory: identifier is the default if no filepath is present
    LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOGGING_LEVEL = logging.INFO
    CACHE_TYPE = 'simple'
    COMPRESS_MIMETYPES = ['text/html', 'text/css', 'text/xml',
                          'application/json', 'application/javascript']
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500
    SUPPORTED_LANGUAGES = {'en': 'English', 'fr': 'Francais'}
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    SOURCES_CONFIG_FILE = 'source.ini'
    STORAGE_PATH = '/mnt/data'
    DEFAULT_NEARBY_LIMIT = 5


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False
    LOGGING_LEVEL = logging.DEBUG
    ENV = 'dev'


class StagingConfig(BaseConfig):
    DEBUG = False
    TESTING = True
    LOGGING_LEVEL = logging.INFO
    ENV = 'staging'


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False
    LOGGING_LEVEL = logging.WARN
    ENV = 'prod'


config = {
    "dev": "config.DevelopmentConfig",
    "staging": "config.StagingConfig",
    "prod": "config.ProductionConfig",
    "default": "config.DevelopmentConfig"
}

ENVIRONMENT_OVERRIDES = [
    "SOURCES_CONFIG_FILE",
    "STORAGE_PATH",
    "DEFAULT_NEARBY_LIMIT",
]

def configure_app(app):
    config_name = os.getenv('FLASK_CONFIGURATION', 'default')
    app.config.from_object(config[config_name])
    app.config.from_pyfile('config.cfg', silent=True)
    # Allow override config file path using env var
    app.config.from_envvar('FLASK_CONFIG_FILE_PATH', silent=True)


    # Allow defining the source file from environment variable directly (bypassing the config)
    for conf_var in ENVIRONMENT_OVERRIDES:
        sourcepath = os.getenv(conf_var)
        if sourcepath:
            app.config[conf_var] = sourcepath

    # Configure logging
    handler = logging.StreamHandler('wsgi')
    handler.setLevel(app.config['LOGGING_LEVEL'])
    formatter = logging.Formatter(app.config['LOGGING_FORMAT'])
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    # Configure Compressing
    Compress(app)


def load_sources_from_config_file(path):
    c = configs.load(path)
    srcs = dict()
    for s in c['sources']:
        props = c[s].dict_props
        props['id'] = s
        srcs[s] = props
    return srcs
