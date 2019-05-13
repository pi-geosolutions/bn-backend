# encoding: utf-8

import requests
import json
import random

import utils.parsing as parsing

from flask import Flask, abort, request, jsonify, current_app
from flask_cors import CORS

from app import app, sources, io_helper
from utils import io_utils

cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
# TODO: pip install flask_cors


@app.route('/')
def index():
    return ''



@app.route('/api/v1/stations')
def list_all_stations():
    """
    Concatenates the list of stations from all sources and return it as geojson
    :return:
    """
    features = []
    for src_name, src in sources.items():
        json_content = io_helper.resource_get(src, 'list')
        features.extend(json_content['features'])
    # TODO: remove these 6 lines after demo
    print(len(features))
    random.shuffle(features)
    features_dedup = []
    for f in _deduplicate_helper(features):
        features_dedup.append(f)
    print(len(features_dedup))
    l = {
        'type': 'FeatureCollection',
        'properties': {},
        'totalResults': len(features_dedup),
        'features': features_dedup
    }
    return jsonify(l)


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
    json_content = io_helper.resource_get(src, 'list')
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
        json_content = io_helper.resource_get(src, 'data', station_id)
        return jsonify(json_content)
    else:
        # not dealt with => back to default behaviour
        scope = ''
    if not scope:
        # default behaviour
        json_content = io_helper.resource_get(src, 'list')
        #json_content['properties']['source_name'] = src['name']
        station_feature = next((d for (index, d) in enumerate(json_content['features']) if d["properties"]["productIdentifier"] == station_id), None)
        json_content['features'] = [station_feature]
        json_content['totalResults']=1
        return jsonify(json_content)

def _deduplicate_helper(features):
    seen = set()
    for x in features:
        t = tuple(x['geometry']['coordinates'])
        if t not in seen:
            yield x
            seen.add(t)