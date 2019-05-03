# encoding: utf-8

from flask import Flask


from config import configure_app, load_sources_from_config_file
from utils.io_utils import IoHelper


app = Flask(__name__)
configure_app(app)
path = app.config['SOURCES_CONFIG_FILE']
sources = load_sources_from_config_file(path)
io_helper = IoHelper(app)