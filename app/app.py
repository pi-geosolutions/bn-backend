# encoding: utf-8

import logging
from enum import Enum
import configs
import os

from flask import Flask

from config import configure_app


def load_sources_from_config_file(path):
    c = configs.load(path)
    srcs = dict()
    for s in c['sources']:
        props = c[s].dict_props
        props['id'] = s
        srcs[s] = props
    return srcs


app = Flask(__name__)
configure_app(app)
path = app.config['SOURCES_CONFIG_FILE']
sources = load_sources_from_config_file(path)