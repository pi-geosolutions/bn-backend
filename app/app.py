# encoding: utf-8

import logging
from enum import Enum

from flask import Flask

from config import configure_app

log = logging.getLogger()


class DataSource(Enum):
    WEB = 1
    LOCAL = 2

sources = [
    {
        'name': 'theia-hydroweb',
        'resource-type': DataSource.WEB,
        'list_uri': 'http://hydroweb.theia-land.fr/hydroweb/search?_m=light&lang=fr&basin=Niger&lake=&river=&status=&box=&q=',
        'details_uri': 'http://hydroweb.theia-land.fr/hydroweb/authdownload?products={id}&user=theia-user@mydomain.org&pwd=mypasswd&format=json'
    },
    {
        'name': 'experimental',
        'resource-type': DataSource.LOCAL,
        'list_uri': 'stations-experimental/stations.json',
        'details_uri': 'stations-experimental/{id}.json',
    }
]

app = Flask(__name__)
configure_app(app)
