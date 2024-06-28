# encoding: utf-8
"""Helpers for parsing hydroweb files

"""

import os
import re
from dateutil import parser
from datetime import datetime

metadata_tpl = {
        'version': None,
        'id': None,
        'type': None,
        'name': None,
        'lat': None,
        'lon': None,
        'river': None,
        'lake': None,
        'basin': None,
        'country': None,
        'status': None,
        'start_date': None,
        'completion_date': None,
    }
capitalized_metadata=['river', 'lake', 'basin', 'country']

HYDROWEB_v1 = 'v1'
HYDROWEB_v2 = 'v2'


def txt2geojson(path):
    '''
    Convert data from hydroweb (v1 or v2) TXT format to geojson
    Needs to support both format, since current hydroweb source provides v2 for river stations
    but v1 for lakes
    :param path:
    :return:
    '''
    metadata = metadata_tpl.copy()

    # get the file name as ID
    id = os.path.splitext(os.path.basename(path))[0]
    metadata['id'] = id

    # Read header
    try:
        # Opening the file in binary mode to get optimized access to last line directly (see below)
        with open(path, "rb") as file:
            # read header (first line)
            line = file.readline().decode()
            # decode() Required since reading in binary mode. By default decodes using UTF8 encoding
            # Check file version
            if line.lstrip().startswith('#'):
                # It's hydroweb v2 file
                # read header and store it in a dictionary
                header = {}
                while line.lstrip().startswith('#'):
                    line = line.lstrip('#')
                    if '::' in line:
                        entry = line.split('::', 1)
                        if (len(entry)) == 1:
                            entry.append("")
                        header[entry[0]] = entry[1].strip()
                    else:
                        pass
                    line = file.readline().decode()

                # extract start and last date
                # get start date (will be in the lien read above (last in the loop)
                while line:
                    if not line.lstrip().startswith('#'):
                        line_data = _txt_parse_line_data(line, HYDROWEB_v2)
                        header['start_date'] = line_data['timestamp_iso']
                        break
                    line = file.readline().decode()

                # get last date
                file.seek(-2, os.SEEK_END)
                while file.read(1) != b'\n':
                    file.seek(-2, os.SEEK_CUR)
                line = file.readline().decode()
                line_data = _txt_parse_line_data(line, HYDROWEB_v2)
                header['completion_date'] = line_data['timestamp_iso']

                # fill metadata dict using the header
                metadata = _v2_header_to_metadata(header, metadata)
            else:
                # It's hydroweb v1 file
                header = _txt_parse_header(line)
                # extract start and last date
                # get start date
                line = file.readline().decode()
                while line:
                    if not line.lstrip().startswith('#'):
                        line_data = _txt_parse_line_data(line, HYDROWEB_v1)
                        header['start_date'] = line_data['timestamp_iso']
                        break
                    line = file.readline().decode()

                # get last date
                file.seek(-2, os.SEEK_END)
                while file.read(1) != b'\n':
                    file.seek(-2, os.SEEK_CUR)
                line = file.readline().decode()
                line_data = _txt_parse_line_data(line, HYDROWEB_v1)
                header['completion_date'] = line_data['timestamp_iso']
                metadata = _v1_header_to_metadata(header, metadata)

            # create geojson feature out of collected metadata
            return _metadata_to_geojson_feature(metadata)
    except FileNotFoundError as e:
        return None


def _v1_header_to_metadata(header, metadata):
    """
    v2 and v1 produce differently formatted headers. We use an intermadiate metadata dict, that allows to
    harmonize the metadata structure before we use it
    :param header: v1 header data
    :param metadata: home_made metadata harmonization dict
    :return:
    """
    metadata['version'] = '1.0'
    metadata['short_version'] = HYDROWEB_v1
    metadata['type'] = header.get('type', '').lower()
    metadata['name'] = header.get('station', header.get('lake', ''))
    metadata['lat'] = header.get('lat', '0')
    metadata['lon'] = header.get('lon', '0')
    metadata['river'] = header.get('river', '')
    metadata['lake'] = header.get('lake', '')
    metadata['basin'] = header.get('basin', '')
    metadata['country'] = header.get('country', '')
    metadata['start_date'] = header.get('start_date', '')
    metadata['completion_date'] = header.get('completion_date', '')

    metadata = _format_metadata(metadata)
    return metadata


def _v2_header_to_metadata(header, metadata):
    """
    v2 and v1 produce differently formatted headers. We use an intermadiate metadata dict, that allows to
    harmonize the metadata structure before we use it
    :param header: v2 header data
    :param metadata: home_made metadata harmonization dict
    :return:
    """
    metadata['version'] = header.get('PRODUCT VERSION', '2.0')
    metadata['short_version'] = HYDROWEB_v2
    metadata['type'] = header.get('STATUS', '').lower()
    metadata['name'] = metadata['id']
    metadata['lat'] = header.get('REFERENCE LATITUDE', '0')
    metadata['lon'] = header.get('REFERENCE LONGITUDE', '0')
    metadata['river'] = header.get('RIVER', '')
    metadata['lake'] = header.get('LAKE', '')
    metadata['basin'] = header.get('BASIN', '')
    metadata['country'] = ''
    metadata['start_date'] = header.get('FIRST DATE IN DATASET', '') + '00:00'
    metadata['completion_date'] = header.get('LAST DATE IN DATASET', '') + '00:00'
    # previous values lack time info. Following is better:
    metadata['start_date'] = header.get('start_date', '')
    metadata['completion_date'] = header.get('completion_date', '')

    metadata = _format_metadata(metadata)
    return metadata


def _format_metadata(metadata):
    #fix date formats
    try:
        metadata['start_date'] = datetime.strptime(metadata['start_date'], "%Y-%m-%d %H:%M")
        metadata['completion_date'] = datetime.strptime(metadata['completion_date'], "%Y-%m-%d %H:%M")
    except:
        print('date format invalid')
        pass

    # Capitalize place names
    for key in capitalized_metadata:
        metadata[key] = str(metadata[key]).capitalize()
    return metadata


def txt2data_vectors(path):
    """
    Produces a dict containing 2 vectors (list) of values : dates & water height
    :param path: file path
    :return:
    """
    try:
        data = txt2array(path)
        x, y = zip(*data)
        return {
            'dates': x,
            'h': y
        }
    except FileNotFoundError as e:
        return None


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
        file_version = HYDROWEB_v1
        if line.lstrip().startswith('#'):
            file_version = HYDROWEB_v2


        # parse the rest
        line = file.readline()
        data = []
        while line:
            if not line.lstrip().startswith('#'):
                line_data = _txt_parse_line_data(line, file_version)
                data.append((line_data['timestamp_iso'],
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
    return dict(item.strip().split('=')for item in line.split(';'))


def _metadata_to_geojson_feature(metadata):
    '''
    Use harmonized metadata dict (from v1 or v2 hydroweb headers to fill in a feature template
    :param path:
    :return:
    '''
    try:
        feature = {
            'type': 'Feature',
            'id': metadata.get('id', ''),
            'geometry': {
                'type': 'Point',
                'coordinates': [
                    float(metadata['lon']),
                    float(metadata['lat']),
                ]
            },
            'properties': {
                'name': metadata.get('name', ''),
                'startDate': metadata.get('start_date', ''),
                'completionDate': metadata.get('completion_date', ''),
                'status': metadata.get('type', ''),
                'country': metadata.get('country', ''),
                'river': metadata.get('river', ''),
                'lake': metadata.get('lake', ''),
                'basin': metadata.get('basin', ''),
                'type': metadata.get('type', ''),
                'productIdentifier': metadata.get('id', ''),
            }
        }
    except KeyError as e:
        print('failed while extracting header information for hydroweb TXT file. {}'.format(e))
        raise HydrowebParsingError(
            'failed while extracting header information for hydroweb TXT file. {}'.format(e)) from e
    return feature



def _txt_parse_line_data(line, file_version):
    """
    Create data dict from a data line
    We assume the date is timezone UTC
    :param line: line of data (semi-colon-separated
    :return: data dict
    """
    data = None
    if file_version == HYDROWEB_v2:
        entries = line.split(' ')
        data = {
            'date_iso' : '{}'.format(entries[0].strip()),
            'timestamp_iso' : '{} {}'.format(entries[0].strip(), entries[1].strip()),
            'water_surface_height_above_reference_datum': entries[2].strip(),
            'water_surface_height_uncertainty': entries[3].strip(),
        }
    else: # HYDROWEB_v1
        entries = line.split(';')
        data = {
            'time' : entries[0].strip(),
            'date_iso' : '{}'.format(entries[1].strip().replace('/', '-')),
            'timestamp_iso' : '{} {}'.format(entries[1].strip().replace('/', '-'), entries[2].strip()),
            'water_surface_height_above_reference_datum': entries[3].strip(),
            'water_surface_height_uncertainty': entries[4].strip(),
        }
    return data

class HydrowebParsingError(Exception):
    pass