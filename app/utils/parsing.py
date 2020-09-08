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
        with open(path) as file:
            # read header (first line)
            line = file.readline()

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
                    line = file.readline()

                # fill metadata dict using the header
                metadata = _v2_header_to_metadata(header, metadata)
            else:
                header = _txt_parse_header(line)
                # extract start and last date
                # get start date
                line = file.readline()
                while line:
                    if not line.lstrip().startswith('#'):
                        line_data = _txt_parse_line_data(line)
                        header['start_date'] = line_data['date_iso']
                        break
                    line = file.readline()

                # get last date
                file.seek(0, os.SEEK_END)
                file.seek(file.tell() - 80, os.SEEK_SET)
                line = file.readlines()[-1]
                line_data = _txt_parse_line_data(line)
                header['completion_date'] = line_data['date_iso']
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
    metadata['short_version'] = '1'
    metadata['type'] = header.get('type', '').lower()
    metadata['name'] = header.get('station', '')
    metadata['lat'] = header.get('lat', '0')
    metadata['lon'] = header.get('lon', '0')
    metadata['river'] = header.get('river', '')
    metadata['lake'] = header.get('lake', '')
    metadata['basin'] = header.get('basin', '')
    metadata['country'] = ''
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
    metadata['short_version'] = '2'
    metadata['type'] = header.get('STATUS', '').lower()
    metadata['name'] = metadata['id']
    metadata['lat'] = header.get('REFERENCE LATITUDE', '0')
    metadata['lon'] = header.get('REFERENCE LONGITUDE', '0')
    metadata['river'] = header.get('RIVER', '')
    metadata['lake'] = header.get('LAKE', '')
    metadata['basin'] = header.get('BASIN', '')
    metadata['country'] = ''
    metadata['start_date'] = header.get('FIRST DATE IN DATASET', '')
    metadata['completion_date'] = header.get('LAST DATE IN DATASET', '')

    metadata = _format_metadata(metadata)
    return metadata


def _format_metadata(metadata):
    #fix date formats
    try:
        metadata['start_date'] = datetime.strptime(metadata['start_date'], "%Y-%m-%d")
        metadata['completion_date'] = datetime.strptime(metadata['completion_date'], "%Y-%m-%d")
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
    return dict(item.strip().split('=')for item in line.split(';'))


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
            completionDate = datetime.strptime(date, "%Y-%m-%d")
            feature['properties']['completionDate'] = completionDate
        except:
            #print('date format invalid')
            pass
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
                    float(header_as_dict['lon']),
                    float(header_as_dict['lat']),
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
            completionDate = datetime.strptime(date, "%Y-%m-%d")
            feature['properties']['completionDate'] = completionDate
        except:
            #print('date format invalid')
            pass
    except KeyError as e:
        print('failed while extracting header information for hydroweb TXT file. {}'.format(e))
        raise HydrowebParsingError(
            'failed while extracting header information for hydroweb TXT file. {}'.format(e)) from e
    return feature


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