# encoding: utf-8
# Helpers for parsing hydroweb files

import os
from dateutil import parser

def txt2geojson(path):
    '''
    Convert data from hydroweb TXT format to geojson
    :param path:
    :return:
    '''
    with open(path) as file:
        # read header (first line)
        line = file.readline()

        feature = _txt_header_to_geojson_feature(line)

        # parse the rest
        line = file.readline()
        data = []
        station_id = feature.get('properties').get('productIdentifier')
        while line:
            if not line.lstrip().startswith('#'):
                line_data = _txt_parse_line_data(line)
                line_data['identifier'] = station_id
                data.append(line_data)
            line = file.readline()

        feature['properties']['startDate'] = data[0].get('date_iso')
        feature['properties']['completionDate'] = data[-1].get('date_iso')
        # get the file name as ID
        id = os.path.splitext(os.path.basename(path))[0]
        feature['properties']['productIdentifier'] = id
        feature['id'] = id
        return feature


def txt2data_vectors(path):
    """
    Produces a dict containing 2 vectors (list) of values : dates & water height
    :param path: file path
    :return:
    """
    data = txt2array(path)
    x, y = zip(*data)
    return {
        'dates': x,
        'h': y
    }


def txt2array(path):
    '''
    Convert data from hydroweb TXT format to numpy array (for graphs)
    Processes data only
    :param path:
    :return: list of (time, value) tuples
    '''
    #TODO: check if we get performance improvement using numpy.fromregex to read from file
    with open(path) as file:
        # drop header (first line)
        line = file.readline()

        # parse the rest
        line = file.readline()
        data = []
        while line:
            if not line.lstrip().startswith('#'):
                line_data = _txt_parse_line_data(line)
                data.append((line_data['date_iso'],
                             float(line_data['water_surface_height_above_reference_datum'])
                             )
                            )
            line = file.readline()
    return data


def _txt_parse_header(line):
    '''
    Get header (1st line and return a dict)
    :param line:
    :return:
    '''
    return dict(item.strip() .split('=')for item in line.split(';'))


def _txt_header_to_geojson_feature(line):
    '''
    Converts the first line of a hydroweb TXT file to a geojson feature dict
    :param line:
    :return:
    '''
    header_as_dict = _txt_parse_header(line)
    # TODO: reduce code redundancy here. Better would be to harmonize formats, see if hydroweb would change it for next version.
    if line.startswith('lake'):
        return _lake_header_to_geojson_feature(header_as_dict)
    else:
        return _station_header_to_geojson_feature(header_as_dict)

def _station_header_to_geojson_feature(header_as_dict):
    try:
        feature = {
            'type': 'Feature',
            'id': header_as_dict['station'],
            'geometry': {
                'type': 'Point',
                'coordinates': [
                    float(header_as_dict['lon']),
                    float(header_as_dict['lat']),
                ]
            },
            'properties': {
                'name': header_as_dict.get('station', ''),
                'startDate': '',
                'completionDate': '',
                'status': header_as_dict.get('type', ''),
                'country': str(header_as_dict.get('country', '')).capitalize(),
                'river': str(header_as_dict.get('river', '')).capitalize(),
                'lake': str(header_as_dict.get('lake', '')).capitalize(),
                'basin': str(header_as_dict.get('basin', '')).capitalize(),
                'type': header_as_dict.get('type', ''),
            }
        }
        date = header_as_dict.get('date')
        try:
            completionDate = parser.parse(date)
            feature['properties']['completionDate'] = completionDate
        except:
            print('date format invalid')
    except KeyError as e:
        print('failed while extracting header information for hydroweb TXT file. {}'.format(e))
        raise HydrowebParsingError(
            'failed while extracting header information for hydroweb TXT file. {}'.format(e)) from e
    return feature


def _lake_header_to_geojson_feature(header_as_dict):
    try:
        feature = {
            'type': 'Feature',
            'id': header_as_dict['lake'],
            'geometry': {
                'type': 'Point',
                'coordinates': [
                    header_as_dict['lon'],
                    header_as_dict['lat'],
                ]
            },
            'properties': {
                'collection': 'research_stations',
                'name': header_as_dict.get('lake', ''),
                'startDate': '',
                'completionDate': '',
                'status': header_as_dict.get('type', ''),
                'country': str(header_as_dict.get('country', '')).capitalize(),
                'river': str(header_as_dict.get('river', '')).capitalize(),
                'lake': str(header_as_dict.get('lake', '')).capitalize(),
                'basin': str(header_as_dict.get('basin', '')).capitalize(),
                'type': header_as_dict.get('type', ''),
            }
        }
        date = header_as_dict.get('date')
        try:
            completionDate = parser.parse(date)
            feature['properties']['completionDate'] = completionDate
        except:
            print('date format invalid')
    except KeyError as e:
        print('failed while extracting header information for hydroweb TXT file. {}'.format(e))
        raise HydrowebParsingError(
            'failed while extracting header information for hydroweb TXT file. {}'.format(e)) from e
    return feature


def _txt_parse_line_data(line):
    """
    Create data dict from a data line
    We assume the date is timezone UTC
    :param line: line of data (semi-colon-separated
    :return: data dict
    """
    entries = line.split(';')
    data = {
        'time' : entries[0].strip(),
        'date_iso' : '{} {}'.format(entries[1].strip(), entries[2].strip()),
        'water_surface_height_above_reference_datum': entries[3].strip(),
        'water_surface_height_uncertainty': entries[4].strip(),
        'number_of_observations': entries[5].strip(),
        'satellite_cycle_number': entries[6].strip(),
    }
    return data


class HydrowebParsingError(Exception):
    pass