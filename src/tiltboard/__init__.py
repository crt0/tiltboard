import configparser
import os

CONFIG = configparser.ConfigParser()
CONFIG.read_dict({
    'general': {
        'base_url':       'https://ajk.beer/tilt/',
        'data_file':      'data.txt',
        'etc_dir':        os.path.join(__package__, '..', '..', '..', '..',
                                       'etc'),
        'index_file':     'index.html',
        'pub_base':       os.path.join(os.sep, 'var', 'www', 'tilt'),
        'tilt_colors':    ['black', 'blue', 'green', 'orange', 'pink',
                           'purple', 'red', 'yellow'],
        'timezone':       'UTC'
    }
})
CONFGEN = CONFIG['general']
CONFIG.read(os.path.join(CONFGEN.get('etc_dir'), 'tiltboard.conf'))
