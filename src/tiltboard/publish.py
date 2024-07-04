from datetime import datetime
from importlib import resources as R
import os
import re
import subprocess
import time

import inotify.adapters

from tiltboard import CONFGEN
from tiltboard import resources

BEER_SUBDIR_RE = re.compile('^2[0-9]{7}-')

def main():
    base_dir = CONFGEN.get('pub_base');
    data_file = CONFGEN.get('data_file')

    i = inotify.adapters.Inotify()
    i.add_watch(base_dir)
    with os.scandir(base_dir) as d:
        for entry in d:
            if (entry.is_dir(follow_symlinks=False) and
                BEER_SUBDIR_RE.search(entry.name)):
                i.add_watch(entry.path)

    for event in i.event_gen(yield_nones=False):
        (_, type_names, path, filename) = event
        if 'IN_CREATE' in type_names and BEER_SUBDIR_RE.search(filename):
            i.add_watch(os.path.join(path, filename))
        if ('IN_CLOSE_WRITE' in type_names and filename == data_file and
            BEER_SUBDIR_RE.search(os.path.basename(path))):
            render(path, filename)

def parse_line(line):
    fields = line.split(' ')
    return [int(fields[0]), float(fields[1]), float(fields[2])]

def render(data_dir, filename):
    with open(os.path.join(data_dir, filename)) as f:
        line = next(f)
        first_telem, min_gravity, temp = parse_line(line)
        last_telem = first_telem
        plateau_start = last_telem
        gravity = min_gravity
        head = [line]
        for i, line in enumerate(f):
            head.append(line)
            last_telem, gravity, _ = parse_line(line)
            if gravity < min_gravity:
                plateau_start = last_telem
                min_gravity = gravity
            if i >= 3:
                break
        og = sum([float(x.split(' ', 2)[1]) for x in head]) / len(head)
        for line in f:
            last_telem, gravity, temp = parse_line(line)
            if gravity < min_gravity:
                plateau_start = last_telem
                min_gravity = gravity

    drop = og - gravity
    attenuation = drop / og * 100
    duration = (last_telem - first_telem) / 86400
    try:
        rate = drop / duration
    except ZeroDivisionError:
        rate = 0
    abv = drop * 0.52945
    plateau = (last_telem - plateau_start) / 3600

    os.environ['TZ'] = CONFGEN.get('timezone')
    time.tzset()
    offset = int((datetime.utcfromtimestamp(last_telem) -
                  datetime.fromtimestamp(last_telem)).total_seconds())
    last_telem_adj = last_telem + offset
    last_telem_full = time.strftime('%a %b %d %H:%M %Z', time.localtime(last_telem_adj))
    refresh = last_telem_adj + 15 * 60 - int(time.time())
    if refresh < 0:
        refresh = 15 * 60

    try:
        start_date, beer = os.path.basename(data_dir).split('-')
    except FileNotFoundError:
        beer = ''
    except ValueError:
        raise Exception(f"{data_dir=} doesn't look right")

    res_dir = R.files(resources)
    template = res_dir.joinpath('template.html').read_text()

    index_file = CONFGEN.get('index_file')
    with open(os.path.join(data_dir, index_file), 'w') as f:
        f.write(template.format(abv=abv, attenuation=attenuation, beer=beer,
                                duration=duration, gravity=gravity,
                                last_telem=last_telem_full, og=og,
                                plateau=plateau, rate=rate, refresh=refresh,
                                temp=temp))

    with R.as_file(R.files(resources) / 'tiltboard.gp') as gnuplot_script:
        subprocess.run(['gnuplot', '-c', gnuplot_script, data_dir])
