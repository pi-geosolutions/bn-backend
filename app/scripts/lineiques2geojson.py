# encoding: utf-8

'''
Reads the txt files given as 'lineiques' and builds a geojson out of it
'''

import logging
import argparse
import glob
import re
import geojson
import json
from os import path

logger = logging.getLogger()

def main():
    # Input arguments
    parser = argparse.ArgumentParser(description='''
    Reads the txt files given as 'lineiques' and builds a geojson out of it
    ''')
    parser.add_argument('-v', '--verbose', help='verbose output (debug loglevel)',
                        action='store_true')
    parser.add_argument('--logfile',
                        help='logfile path. Default: prints logs to the console')
    parser.add_argument('-l', '--lineiques_path', help='path to the text files')
    parser.add_argument('-o', '--out_file', help='name of the geojson file')
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

    # do the stuff
    lineiques_to_geojson(args.lineiques_path, args.out_file)


def lineiques_to_geojson(lineiques_path, out_file):
    files = glob.glob(path.join(lineiques_path, '*.txt'))
    lines = []
    # scan the files
    for file in files:
        line = make_feature(file)
        lines.append(line)
    # create the geojson 'shapefile'
    feature_collection = geojson.FeatureCollection(lines)
    # write the file
    with open(out_file, 'w') as outfile:
        json.dump(feature_collection, outfile)

def make_feature(file_path):
    with open(file_path) as file:
        line = file.readline()
        data = []
        while line:
            if not line.lstrip().startswith('#'):
                entries = [float(x) for x in re.split(r'\t+', line)]
                data.append(tuple(entries))
            line = file.readline()
    l = geojson.LineString(data)
    name = path.splitext(path.basename(file_path))[0]
    feature = geojson.Feature(geometry=l, properties={"name": name})
    logger.info("parsed {}".format(name))
    return feature


if __name__ == '__main__':
    main()