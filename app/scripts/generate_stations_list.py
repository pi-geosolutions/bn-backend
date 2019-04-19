# encoding: utf-8

'''
Reads the source configuration, scans the stations and produces the stations list in geojson format,
similar to http://hydroweb.theia-land.fr/hydroweb/search?_m=light&lang=fr&basin=Niger&lake=&river=&status=&box=&q=
'''

import logging
import argparse
import glob
import json

# local to the module
from utils import io_utils, parsing

logger = logging.getLogger()

def main():
    # Input arguments
    parser = argparse.ArgumentParser(description='''
    Reads the source configuration, scans the stations and produces the stations list in geojson format,
    similar to http://hydroweb.theia-land.fr/hydroweb/search?_m=light&lang=fr&basin=Niger&lake=&river=&status=&box=&q=
    ''')
    parser.add_argument('-v', '--verbose', help='verbose output (debug loglevel)',
                        action='store_true')
    parser.add_argument('--logfile',
                        help='logfile path. Default: prints logs to the console')
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
    features = []
    for file in files:
        try:
            line_as_feature = parsing.txt2geojson(file)
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

    logger.debug(args.source_name)


if __name__ == '__main__':
    main()