# encoding: utf-8

from flask import Flask


from config import configure_app
from utils import io_utils


app = Flask(__name__)
configure_app(app)
path = app.config['SOURCES_CONFIG_FILE']
sources = io_utils.load_sources_from_config_file(path)