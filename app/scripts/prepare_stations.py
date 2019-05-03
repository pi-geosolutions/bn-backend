# encoding: utf-8

'''
Reads the source configuration from app configuration,
retrieves the stations list for each source,
downloads the stations data locally for web resources,
produces the png thumbnails.
'''

import logging
import argparse
import glob
import json
import numpy
import requests
import urllib.request
from os import path, makedirs
from matplotlib import pyplot, dates as mdates
from datetime import datetime

from app import app

# local to the module
from utils import io_utils, parsing
from utils.io_utils import IoHelper

logger = logging.getLogger()
io_helper = app.io_helper
FORCE_UPDATE = False


def main():
    # Input arguments
    parser = argparse.ArgumentParser(description='''
    Reads the source configuration, scans the stations and produces:
     * the stations list in geojson format,
    similar to http://hydroweb.theia-land.fr/hydroweb/search?_m=light&lang=fr&basin=Niger&lake=&river=&status=&box=&q=
     * graph thumbnails for each station
    ''')
    parser.add_argument('-v', '--verbose', help='verbose output (debug loglevel)',
                        action='store_true')
    parser.add_argument('--logfile',
                        help='logfile path. Default: prints logs to the console')
    parser.add_argument('-l', '--list', help='only generate stations list',
                        action='store_true')
    parser.add_argument('-t', '--thumbnails', help='generate stations graph thumbnails',
                        action='store_true')
    parser.add_argument('--storage_path',
                        help='Where the generatd files will be stored (root folder). Defaults to /mnt/data')

    args = parser.parse_args()


    # INITIALIZE LOGGER
    handler = logging.StreamHandler()
    if args.logfile:
        handler = logging.FileHandler(args.logfile)

    formatter = logging.Formatter(
            '%(asctime)s %(name)-5s %(levelname)-3s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    loglevel = logging.INFO
    if args.verbose:
        loglevel = logging.DEBUG
    logger.setLevel(loglevel)

    srcs = app.sources

    for src_name, src in srcs.items():
        prepare_stations_for_source(src)


def prepare_stations_for_source(src):
    """
    Reads the source configuration from app configuration,
    retrieves the stations list for this source,
    downloads the stations data locally for web resources,
    re-creates the stations list (for consistency between local and remote source)
    produces the png thumbnails.
    :param src:
    :return:
    """

    # make sure the folders exist
    for k, v in io_helper.paths.items():
        if k.endswith('.folder'):
            makedirs(v.format(source_id = src['id']), exist_ok=True)

    if src['list_uri'].startswith("http"):
        r = requests.get(src['list_uri'])
        _retrieve_stations_data(src, r.json())

    files = glob.glob(io_helper.paths['stations.data'].format(source_id=src['id'], station_id='*'))
    # create the stations list in geojson format,
    _generate_stations_list(src, files)

    # generate graph thumbnails
    _generate_thumbnails(src, files)


def _retrieve_stations_data(src, stations_list):
    """
    Downloads the data files for each station of this data source and stores it locally for further use
    :param src:
    :param stations_list:
    :return:
    """
    for f in stations_list['features']:
        url = src['details_uri'].format(id=f['properties']['productIdentifier'])
        dest_file = io_helper.paths['stations.data'].format(source_id=src['id'],
                                                           station_id = f['properties']['productIdentifier'])
        if not FORCE_UPDATE:
            # don't re-download the file if already present on the disk
            if path.exists(dest_file):
                continue
        urllib.request.urlretrieve(url, dest_file)


def _generate_stations_list(src, files_list):
    features = []
    for file in files_list:
        try:
            line_as_feature = parsing.txt2geojson(file)
            line_as_feature['properties']['thumbnail'] = io_helper.paths['stations.png.url'].format(source_id = src['id'],
                                                    station_id = line_as_feature['properties']['productIdentifier'])
            line_as_feature['properties']['collection'] = src.get('name')
            features.append(line_as_feature)
        except parsing.HydrowebParsingError as e:
            logger.error('failed while extracting header information for hydroweb TXT file {}. {}'.format(file, e))

    stations_list = {
        'type': 'FeatureCollection',
        'totalResults': len(features),
        'properties': {},
        'features': features
    }

    filename = io_helper.paths['stations.list'].format(source_id=src['id'])
    with open(filename, 'w') as outfile:
        json.dump(stations_list, outfile, indent=2, sort_keys=False)


def _generate_thumbnails(src, files_list):
    pyplot.rcParams['font.size'] = 6.0
    pyplot.rcParams['figure.frameon'] = False
    pyplot.rcParams['figure.figsize'] = [3, 2]
    for file in files_list:
        try:
            data = parsing.txt2data_vectors(file)
            # parse dates as dates
            x = [datetime.strptime(ii, "%Y/%m/%d %H:%M") for ii in data['dates']]
            a_x = numpy.asarray(x)
            a_y = numpy.asarray(data['h'], numpy.float32)
            #ax.xaxis.set_minor_locator(mdates.MonthLocator())
            fig, ax = pyplot.subplots()
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(True)
            ax.spines['left'].set_visible(True)
            ax.plot_date(a_x, a_y, fmt='b-', xdate=True, ydate=False, linewidth=0.5)

            filename = '{}.png'.format(path.splitext(path.basename(file))[0])
            filepath = path.join(io_helper.paths['png.folder'].format(source_id=src['id']), filename)
            fig.savefig(filepath)
            pyplot.close(fig)
            #fig.show()
            logger.debug("processed station {}".format(file))

        except parsing.HydrowebParsingError as e:
            logger.error('failed while extracting header information for hydroweb TXT file {}. {}'.format(file, e))


if __name__ == '__main__':
    main()