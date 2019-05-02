# encoding: utf-8

import json
from os import path
from utils import parsing

from app import app


paths = {
    'root' : '/mnt/data',
    'sources.folder' : path.join('/mnt/data', 'sources', '{source_id}'),
    'stations.folder' : path.join('/mnt/data', 'sources', '{source_id}', 'stations'),
    'txt.folder' : path.join('/mnt/data', 'sources', '{source_id}', 'stations', 'txt'),
    'png.folder' : path.join('/mnt/data', 'sources', '{source_id}', 'stations', 'thumbnails'),
    'stations.list' : path.join('/mnt/data', 'sources', '{source_id}', 'stations', 'stations.json'),
    'stations.data' : path.join('/mnt/data', 'sources', '{source_id}', 'stations', 'txt',
                                '{station_id}.txt'),
    'stations.png.url' : path.join('/static', 'sources', '{source_id}', 'stations', 'thumbnails',
                                '{station_id}.png'),
}


# TODO: see if we could
def get_storage_base_path():
    return '/mnt/data'


def resource_get(src, res, id=''):
    """
    Get the resource (res) locally if possible.
    :param src: source definition
    :param res: the resource to get
    :return:
    """
    base_path = '/mnt/data'
    if res == 'list':
        uri = paths.get('stations.list').format(source_id = src['id'])
        #uri = path.join(base_path, 'sources', src['id'], 'stations', 'stations.json')
        with open(uri) as json_file:
            json_local = json.load(json_file)
            return json_local
    elif res == 'data':
        # TODO error-check if id doesn't exist
        uri = paths.get('stations.data').format(source_id = src['id'], station_id = id)
        #uri = path.join(base_path, 'sources', src['id'], 'stations', 'txt', '{id}.txt'.format(id=id))
        return parsing.txt2data_vectors(uri)
