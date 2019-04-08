import requests
import json

from flask import Flask, abort, request, jsonify, current_app

from app import app, sources

def resource_as_json(uri):
    if uri.startswith("http"):
        r = requests.get(uri)
        current_app.logger.debug(r.status_code)
        return r.json()
    else: # we assume it is local path
        with open(uri) as json_file:
            json_local = json.load(json_file)
            return json_local


@app.route('/')
def index():
    return ''


#TODO: add source name in the stations list so we can build the station/XXX request
@app.route('/services/stations')
def stationslist():
    json_all = []
    for src in sources:
        json_content = resource_as_json( src['list_uri'])
        json_content['properties']['source_name'] = src['name']
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
    return jsonify(resource_as_json(uri))