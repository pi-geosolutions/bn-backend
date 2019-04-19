# encoding: utf-8

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


@app.route('/api/v1/sources')
def list_sources():
    """
    Get the list of available sources
    :return: sources list
    """
    return jsonify(sources)


@app.route('/api/v1/sources/<source_id>')
def get_source(source_id):
    """
    Get definition for given source id
    :param source_id:
    :return: source definition for the matching id
    """
    source = sources[source_id]
    return jsonify(source)


@app.route('/api/v1/sources/<source_id>/stations')
def list_stations(source_id):
    """
    Get stations for given data source id
    :param source_id:
    :return: list of station objects
    """
    src = sources[source_id]
    json_content = resource_as_json( src['list_uri'])
    #json_content['properties']['source_name'] = src['name']
    return jsonify(json_content)



@app.route('/api/v1/sources/<source_id>/stations/<station_id>')
def get_stations(source_id, station_id):
    """
    Get station definition for given data source id
    :param source_id:
    :param station_id: the id given in productIdentifier field
    :return: station object. If ?scope=data parameter is provided, returns the stations altimetric data
    """
    src = sources[source_id]
    scope = request.args.get('scope')
    if scope == 'data':
        # Extract the proper details URL
        uri = src['details_uri'].format(id=station_id)
        return jsonify(resource_as_json(uri))
    else:
        # not dealt with => back to default behaviour
        scope = ''
    if not scope:
        # default behaviour
        json_content = resource_as_json( src['list_uri'])
        #json_content['properties']['source_name'] = src['name']
        station_feature = next((d for (index, d) in enumerate(json_content['features']) if d["properties"]["productIdentifier"] == station_id), None)
        json_content['features'] = [station_feature]
        return jsonify(json_content)