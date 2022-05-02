# encoding: utf-8

'''
Reads the source configuration from app configuration,
retrieves the stations list for web resources (only),
downloads the stations data locally for web resources (only),
generates the stations list file for every source (so that the list is homogeneous from one source to another),
produces the png thumbnails.
All data is stored in files. The paths patterns are defined in utils/io_utils.py (class IoHelper). The root path can be
defined in the app's configuration

For now, all data is retrieved and re-generated at every run.
TODO: optimize the resource consumption.
- Only process data that have new values
- only get the new values for hydroweb resources available through api
'''

import logging
import argparse
import glob
import json
import numpy
import re
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time
from os import environ, path, makedirs, remove, getenv
from matplotlib import pyplot, dates as mdates
from datetime import datetime

from app import app

# local to the module
from utils import io_utils, parsing

logger = logging.getLogger()
io_helper = app.io_helper
CLEAN_DEPRECATED_STATIONS = False

REQUESTS_MAX_RETRIES=int(environ.get('REQUESTS_MAX_RETRIES','5'))

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
    parser.add_argument('-c', '--clean_deprecated_stations',
                        help='[http(s) sources only] remove stations that are not available online anymore',
                        action='store_true')
    parser.add_argument('--logfile',
                        help='logfile path. Default: prints logs to the console')
    parser.add_argument('-f', '--force', help='DEPRECATED',
                        action='store_true')
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

    if args.clean_deprecated_stations:
        global CLEAN_DEPRECATED_STATIONS
        CLEAN_DEPRECATED_STATIONS = True
    srcs = app.sources

    for src_name, src in srcs.items():
        prepare_stations_for_source(src)


class ShouldPauseDownloadException(Exception):
    pass


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

    # remove stations that are on the disk but not any more listed on the http source: simplest way is to remove them
    # all before downloading them again
    if CLEAN_DEPRECATED_STATIONS:
        on_disk = glob.glob(io_helper.paths['stations.data'].format(source_id=src['id'], station_id='*'))
        for station in on_disk:
            remove(station) # delete file

    # Retrieve the data.
    if src['list_uri'].startswith("http"):
        r = requests.get(src['list_uri'])
        _retrieve_stations_data(src, r.json())

    # Get the files list
    # files = []
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
    :return: lists tuple unchanged_files_list, new_files_list
    """
    details_uri = src['details_uri']

    # replace env vars by their values. Used particularly for password
    patterns = re.findall(r'{{.+?}}', details_uri)
    for p in patterns:
        # replace every pattern by its matching env var if available
        try:
            value = getenv(str(p).replace('{{', '').replace('}}', ''))
            details_uri = details_uri.replace(p, value)
        except:
            pass

    for f in stations_list['features']:
        url = details_uri.format(id=f['properties']['productIdentifier'])

        dest_file = io_helper.paths['stations.data'].format(source_id=src['id'],
                                                           station_id = f['properties']['productIdentifier'])

        # Download files using requests.Retry to handle timeouts and server failures
        retry_strategy = Retry(
            total=REQUESTS_MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.Session()
        http.mount("https://", adapter)
        http.mount("http://", adapter)

        response = http.get(url)
        response.raise_for_status()
        if response.status_code == 200:
            # Write data to file
            open(dest_file, 'wb').write(response.content)
        else:
            logger.warning("Error while retrieving {}".format(url))


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
        json.dump(stations_list, outfile, indent=2, sort_keys=False, default=str)


def _generate_thumbnails(src, files_list):
    pyplot.rcParams['font.size'] = 6.0
    pyplot.rcParams['figure.frameon'] = False
    pyplot.rcParams['figure.figsize'] = [3, 2]
    for file in files_list:
        try:
            data = parsing.txt2data_vectors(file)
            # parse dates as dates
            x = [datetime.strptime(ii, "%Y-%m-%d %H:%M") for ii in data['dates']]
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