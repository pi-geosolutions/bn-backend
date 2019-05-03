# encoding: utf-8

import json
from os import path
from utils import parsing


class IoHelper():
    paths = {}

    def __init__(self, flask_app=None):
        self.app = flask_app
        root_path = '/mnt/data2' # default
        if self.app:
            root_path = self.app.config['STORAGE_PATH']
        self.paths = {
            'root': root_path,
            'sources.folder' : path.join(root_path, 'sources', '{source_id}'),
            'stations.folder' : path.join(root_path, 'sources', '{source_id}', 'stations'),
            'txt.folder' : path.join(root_path, 'sources', '{source_id}', 'stations', 'txt'),
            'png.folder' : path.join(root_path, 'sources', '{source_id}', 'stations', 'thumbnails'),
            'stations.list' : path.join(root_path, 'sources', '{source_id}', 'stations', 'stations.json'),
            'stations.data' : path.join(root_path, 'sources', '{source_id}', 'stations', 'txt',
                                        '{station_id}.txt'),
            'stations.png.url' : path.join('/static', 'sources', '{source_id}', 'stations', 'thumbnails',
                                        '{station_id}.png'),
        }


    def resource_get(self, src, res, id=''):
        """
        Get the resource (res) locally if possible.
        :param src: source definition
        :param res: the resource to get
        :return:
        """
        if res == 'list':
            uri = self.paths.get('stations.list').format(source_id = src['id'])
            #uri = path.join(base_path, 'sources', src['id'], 'stations', 'stations.json')
            with open(uri) as json_file:
                json_local = json.load(json_file)
                return json_local
        elif res == 'data':
            # TODO error-check if id doesn't exist
            uri = self.paths.get('stations.data').format(source_id = src['id'], station_id = id)
            #uri = path.join(base_path, 'sources', src['id'], 'stations', 'txt', '{id}.txt'.format(id=id))
            return parsing.txt2data_vectors(uri)
