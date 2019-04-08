import os
import logging
from flask_compress import Compress


class BaseConfig(object):
    DEBUG = False
    TESTING = False
    # sqlite :memory: identifier is the default if no filepath is present
    LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOGGING_LOCATION = 'app.log'
    LOGGING_LEVEL = logging.DEBUG
    CACHE_TYPE = 'simple'
    COMPRESS_MIMETYPES = ['text/html', 'text/css', 'text/xml',
                          'application/json', 'application/javascript']
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500
    SUPPORTED_LANGUAGES = {'en': 'English', 'fr': 'Francais'}
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    SOURCES_CONFIG_FILE = 'source.ini'


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False
    ENV = 'dev'


class StagingConfig(BaseConfig):
    DEBUG = False
    TESTING = True
    ENV = 'staging'


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False
    ENV = 'prod'


config = {
    "dev": "config.DevelopmentConfig",
    "staging": "config.StagingConfig",
    "prod": "config.ProductionConfig",
    "default": "config.DevelopmentConfig"
}


def configure_app(app):
    config_name = os.getenv('FLASK_CONFIGURATION', 'default')
    app.config.from_object(config[config_name])
    app.config.from_pyfile('config.cfg', silent=True)
    # Allow override config file path using env var
    app.config.from_envvar('FLASK_CONFIG_FILE_PATH', silent=True)

    # Allow defining the source file from environment variable directly (bypassing the config)
    sourcepath = os.getenv('SOURCES_CONFIG_FILE')
    if sourcepath:
        app.config['SOURCES_CONFIG_FILE'] = sourcepath

    # Configure logging
    handler = logging.FileHandler(app.config['LOGGING_LOCATION'])
    handler.setLevel(app.config['LOGGING_LEVEL'])
    formatter = logging.Formatter(app.config['LOGGING_FORMAT'])
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    # Configure Compressing
    Compress(app)
