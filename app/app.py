# encoding: utf-8

from flask import Flask


from config import configure_app, load_sources_from_config_file


app = Flask(__name__)
configure_app(app)
path = app.config['SOURCES_CONFIG_FILE']
sources = load_sources_from_config_file(path)