# encoding: utf-8

import requests
import json
import random
import math
import operator

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
    features = _all_stations_as_list()
    l = {
        'type': 'FeatureCollection',
        'properties': {},
        'totalResults': len(features),
        'features': features
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
    json_content = _get_stations(source_id, station_id)
    return jsonify(json_content)


def _get_stations(source_id, station_id):
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
        return json_content
    else:
        # not dealt with => back to default behaviour
        scope = ''
    if not scope:
        # default behaviour
        json_content = io_helper.resource_get(src, 'list')
        #json_content['properties']['source_name'] = src['name']
        station_feature = next((d for (index, d) in enumerate(json_content['features']) if d["properties"]["productIdentifier"] == station_id), None)
        if not station_feature:
            return None
        json_content['features'] = [station_feature]
        json_content['totalResults']=1
        return json_content


@app.route('/api/v1/stations/<station_id>')
def get_any_station(station_id):
    """
    Get station definition without knowing the source id. It looks over all sources for available station
    :param station_id: the id given in productIdentifier field
    :return: station object. If ?scope=data parameter is provided, returns the stations altimetric data
    """
    station = _get_any_station(station_id)
    return jsonify(station)


def _get_any_station(station_id):
    """
    Uses code quite similar to _get_stations, but dealing with
    :param station_id:
    :return:
    """
    station = None
    for src in sources:
        try:
            station = _get_stations(src, station_id)
        except FileNotFoundError as e:
            # this is not the right source
            pass
        else:
            # If there has been no error, and its value != None this is the right source
            if station:
                return station
    return None


@app.route('/api/v1/stations/nearby/<station_id>')
def get_nearby_stations(station_id):
    """
    Get stations that are close to the provided station
    :param station_id: the reference station's id
    :return: list of close-by stations, by order of distance
    """
    nearbys = None
    nb = 5
    limit = request.args.get('limit')
    if limit:
        try:
            nb = int(limit)
        except ValueError:
            # we keep default
            pass

    radius = request.args.get('radius')
    if radius:
        try:
            radius = float(radius)
        except ValueError:
            # we keep default
            pass
        else:
            nearbys = list(filter(lambda x: x['distance'] < radius, _get_nearby_stations(station_id)))
    if not nearbys:
        # default
        nearbys = _get_nearby_stations(station_id)[:nb]
    return jsonify(_as_feature_collection(nearbys))



def _deduplicate_helper(features):
    seen = set()
    for x in features:
        t = tuple(x['geometry']['coordinates'])
        if t not in seen:
            yield x
            seen.add(t)

def _all_stations_as_list():
    """
    Concatenates the list of stations from all sources and return it as a list
    :return:
    """
    features = []
    for src_name, src in sources.items():
        json_content = io_helper.resource_get(src, 'list')
        features.extend(json_content['features'])
    # # TODO: remove these 6 lines after demo
    # print(len(features))
    # random.shuffle(features)
    # features_dedup = []
    # for f in _deduplicate_helper(features):
    #     features_dedup.append(f)
    # print(len(features_dedup))
    return features

def _get_nearby_stations(station_id):
    ref_station = _get_any_station(station_id)['features'][0]
    all_stations = _all_stations_as_list()
    #nearbys = sorted([_distance(ref_station, s) for s in all_stations], key=lambda x: x[1])
    with_distance = [_distance(ref_station, s) for s in all_stations]
    nearbys = sorted(with_distance, key=operator.itemgetter('distance'))
    print(nearbys)
    return nearbys


def _distance(ref, s):
    """
    Calculate cartesian distance between 2 stations
    :param p0:
    :param p1:
    :return: a tuple (id, distance)
    """
    p1 = ref["geometry"]["coordinates"]
    p2 = s["geometry"]["coordinates"]
    dist = math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
    s["distance"] = dist
    return s


def _as_feature_collection(features):
    return {
        'type': 'FeatureCollection',
        'properties': {},
        'totalResults': len(features),
        'features': features
    }