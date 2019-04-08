import requests
import json

from flask import Flask, abort, request, jsonify, current_app

from app import app, DataSource, sources


def resource_as_json(type, uri):
    if type == DataSource.WEB:
        r = requests.get(uri)
        current_app.logger.debug(r.status_code)
        return r.json()
    elif type == DataSource.LOCAL:
        with open(uri) as json_file:
            json_local = json.load(json_file)
            return json_local
    else:
        current_app.logger.warning(
            "Data source is of type unknown ({0}). Ignoring it...".format(type))
        return None


@app.route('/')
def index():
    return ''


@app.route('/services/stations')
def stationslist():
    json_all = []
    for src in sources:
        json_content = resource_as_json(src['resource-type'], src['list_uri'])
        json_all.append(json_content)
    return jsonify(json_all)


@app.route('/services/station/<source_name>/<station_id>', methods=['GET', 'POST'])
def station(source_name, station_id):
    # Find the matching source
    src = next((d for (index, d) in enumerate(sources) if d["name"] == source_name), None)
    if not src:
        abort(404)
    # Extract the proper details URL
    uri = src['details_uri'].format(id=station_id)
    return jsonify(resource_as_json(src['resource-type'], uri))