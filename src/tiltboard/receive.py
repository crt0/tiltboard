from datetime import date
import json
import os
import re
import sys
import tempfile
from urllib.parse import parse_qs

import gunicorn.app.base

from tiltboard import CONFGEN

DATE_RE = re.compile('2[0-9]{7}')
MAIL_RE = re.compile('@')
SPREADSHEET_DAYS = (date(1970, 1, 1) - date(1899, 12, 30)).days
TMP_LINK = '.tmp_link'

def ssdate_to_seconds(ssdate):
    return int((ssdate - SPREADSHEET_DAYS) * 24 * 3600)

def sg_to_plato(sg):
    return -616.868 + 1111.14 * sg - 630.272 * sg ** 2 + 135.997 * sg ** 3

def generate_response(dict, start_func):
    response_body = (json.dumps(dict) + '\n').encode('utf-8')
    header = [
        ('Content-Type', 'application/json'),
        ('Content-Length', str(len(response_body)))
    ]
    start_func('200 OK', header)
    return [response_body]

def main():
    base_dir = CONFGEN.get('pub_base')

    try:
        testfile = tempfile.TemporaryFile(dir = base_dir)
        testfile.close()
    except OSError as e:
        e.filename = base_dir
        sys.tracebacklimit = 0
        raise

    options = {
        'bind': '%s:%s' % ('127.0.0.1', '8081'),
        'workers': 2,
    }
    StandaloneApplication(handle_request, options).run()

def beer_dir_join(beer, beerid):
    base_dir = CONFGEN.get('pub_base')
    beer_subdir = f"{beerid}-{beer}"
    return [os.path.join(base_dir, beer_subdir), beer_subdir]

def handle_request(environ, start_response):
    base_dir = CONFGEN.get('pub_base')

    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except ValueError:
        request_body_size = 0

    try:
        timepoint, plato, temp, beer, comment = 0.0, 0.0, 0.0, '', ''
        request_body = environ['wsgi.input'].read(request_body_size)
        d = parse_qs(request_body, False, True)

        beer = d.get(b'Beer', '')[0].decode('utf-8')
        if not beer or beer == '':
            raise Exception(f"Beer undefined {beer=}")

        comment = d.get(b'Comment', '')
        if comment:
            comment = comment[0].decode('utf-8')

        color = d.get(b'Color', '')
        if color:
            color = color[0].decode('utf-8')

        try:
            beer, beerid = beer.split(',')
        except ValueError:
            if not MAIL_RE.search(comment):
                raise Exception("Start a new Tiltboard by entering " +
                                f"your email address as a comment {comment=}")
            comment = ''
            beerid = date.today().strftime('%Y%m%d')
            beer_dir, beer_subdir = beer_dir_join(beer, beerid)
            try:
                os.mkdir(beer_dir)
            except FileExistsError:
                pass
            link_dir = os.path.join(base_dir, color.lower())
            tmp_link = os.path.join(base_dir, TMP_LINK)
            try:
                os.symlink(beer_dir, link_dir)
            except FileExistsError:
                try:
                    os.unlink(tmp_link)
                except FileNotFoundError:
                    pass
                os.symlink(beer_dir, tmp_link)
                os.replace(tmp_link, link_dir)
        else:
            if not DATE_RE.fullmatch(beerid):
                raise Exception(f"Bad beer id {beerid=}")
            beer_dir, beer_subdir = beer_dir_join(beer, beerid)

        timepoint = float(d.get(b'Timepoint', '0')[0])
        if timepoint <= 0:
            raise Exception(f"Timepoint out of range {timepoint=}, {d=}")

        timepoint = str(ssdate_to_seconds(timepoint))

        sg = float(d.get(b'SG', '0')[0])
        if sg <= 0 or sg > 2:
            raise Exception(f"SG out of range {sg=}")

        plato = str(sg_to_plato(sg))

        temp = float(d.get(b'Temp', '0')[0])
        if temp <= 0 or temp > 100:
            raise Exception(f"Temp out of range {temp=}")
        temp = str(temp)
    except Exception as e:
        try:
            color
        except:
            color = 'unknown'
        response = {
            'result': f"""{beer}<br>
<strong>TILT | {color}</strong><br>
{e}""",
            'beername': beer,
            'tiltcolor': color
        }
        return generate_response(response, start_response)

    with open(os.path.join(beer_dir, CONFGEN.get('data_file')), 'a') as f:
        f.write(' '.join([timepoint, plato, temp]))
        if comment:
            f.write(f' "{comment}"')
        f.write('\n')

    url = CONFGEN.get('base_url') + beer_subdir + '/'
    response = {
        'result': f'''{beer}<br>
<strong>TILT | {color}</strong><br>
Success logging to Tilboard.<br>
<a class="link external" href="{url}">View Tiltboard</a>''',
        'beername': ','.join([beer, beerid]),
        'tiltcolor': color,
        'doclongurl': url
    }
    return generate_response(response, start_response)

class StandaloneApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application
