# encoding: utf-8
# Helpers for parsing hydroweb files

from dateutil import parser

def txt2geojson(path, with_data=False):
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
        if not with_data:
            return feature

    return None


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
    try:
        feature = {
            'type': 'Feature',
            'id': header_as_dict['station'],
            'geometry': {
                'type': 'Point',
                'coordinates': [
                    header_as_dict['lat'],
                    header_as_dict['lon'],
                ]
            },
            'properties': {
                'collection': 'research_stations',
                'productIdentifier': header_as_dict.get('station', ''),
                'startDate': '',
                'completionDate': '',
                'status': header_as_dict.get('type'),
                'country': header_as_dict.get('river'),
                'river': header_as_dict.get('river'),
                'lake': header_as_dict.get('lake'),
                'basin': header_as_dict.get('basin'),
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
        'date_iso' : '{} {}:00Z'.format(entries[1].strip(), entries[2].strip()),
        'water_surface_height_above_reference_datum': entries[3].strip(),
        'water_surface_height_uncertainty': entries[4].strip(),
        'number_of_observations': entries[5].strip(),
        'satellite_cycle_number': entries[6].strip(),
    }
    return data


class HydrowebParsingError(Exception):
    pass