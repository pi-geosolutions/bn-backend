# encoding: utf-8

'''
Reads the source configuration, scans the stations and produces the stations list in geojson format,
similar to http://hydroweb.theia-land.fr/hydroweb/search?_m=light&lang=fr&basin=Niger&lake=&river=&status=&box=&q=
'''

import logging
import argparse
import glob
import json
import numpy
from os import path, makedirs
from matplotlib import pyplot, dates as mdates
from datetime import datetime

# local to the module
from utils import io_utils, parsing

logger = logging.getLogger()

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
    parser.add_argument('-l', '--list', help='generate stations list',
                        action='store_true')
    parser.add_argument('-t', '--thumbnails', help='generate stations graph thumbnails',
                        action='store_true')
    parser.add_argument('source_name', help='the source name to process')
    parser.add_argument('sources_ini_path', help='the path to the sources.ini file (the one containing the config of the sources')
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

    srcs = io_utils.load_sources_from_config_file(args.sources_ini_path)
    try:
        src = srcs[args.source_name]
    except KeyError as e:
        logger.error('Data source {0} missing in {1}'.format(args.source_name, args.sources_ini_path))

    files = glob.glob(src['details_uri'].replace('{id}', '*'))

    # create the stations list in geojson format,
    if args.list:
        _generate_stations_list(src, files)

    # generate graph thumbnails
    if args.thumbnails:
        _generate_thumbnails(src, files)


    logger.debug(args.source_name)


def _generate_stations_list(src, files_list):
    features = []
    for file in files_list:
        try:
            line_as_feature = parsing.txt2geojson(file)
            line_as_feature['properties']['thumbnail'] = _get_thumbnail_file_name(src, file)
            features.append(line_as_feature)
        except parsing.HydrowebParsingError as e:
            logger.error('failed while extracting header information for hydroweb TXT file {}. {}'.format(file, e))

    stations_list = {
        'type': 'FeatureCollection',
        'totalResults': len(features),
        'properties': {},
        'features': features
    }

    with open(src['list_uri'], 'w') as outfile:
        json.dump(stations_list, outfile, indent=2, sort_keys=False)


def _get_thumbnail_file_name(src, data_file_name):
    basepath, file_name = path.split(data_file_name)
    fname, fext = path.splitext(file_name)
    if src.get('thumbnails_uri'):
        folder, file_name = path.split(src.get('thumbnails_uri'))
    else:
        # we create a sibling folder named 'thumbnails'
        folder = path.normpath('{}/../thumbnails/'.format(basepath))
    if not path.exists(folder):
        makedirs(folder)
    return '{}/{}.png'.format(folder, fname)


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

            fig.savefig(_get_thumbnail_file_name(src, file))
            pyplot.close(fig)
            #fig.show()
            logger.debug("processed station {}".format(file))

        except parsing.HydrowebParsingError as e:
            logger.error('failed while extracting header information for hydroweb TXT file {}. {}'.format(file, e))


if __name__ == '__main__':
    main()