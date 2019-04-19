# encoding: utf-8

import configs

def load_sources_from_config_file(path):
    c = configs.load(path)
    srcs = dict()
    for s in c['sources']:
        props = c[s].dict_props
        props['id'] = s
        srcs[s] = props
    return srcs