#!/usr/bin/python
import argparse
from datetime import datetime, timedelta
import os
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
#from wand.display import display
from wand.font import Font
from wand.image import Image

MODES=['latest', 'random', 'index']
DEFAULT_LOCK_BIN=["swaylock", "i3lock"]
DEFAULT_LOCK_ARGS=['-c', '#000000', '-s', 'fit']
LOG=False

URL='https://xkcd.com/'
LATEST_URL=URL
RANDOM_URL='https://c.xkcd.com/random/comic'

COOLDOWN_PREFIX='last-query'
DEFAULT_COOLDOWN_TIME=timedelta(hours=1)
TIME_FORMAT='%Y-%m-%d %H:%M:%S'

URL_FONT="https://github.com/ipython/xkcd-font/raw/master/xkcd-script/font/xkcd-script.ttf"
IMG_FONT_FILE='xkcd-script.ttf'
IMG_FONT_DIR=f'~/.local/share/fonts'
IMG_BACKGROUND_COLOR='#000000'
IMG_CAPTION_COLOR='#b0b0b0'
IMG_CAPTION_SIZE=18
IMG_TITLE_COLOR='#ffffff'
IMG_TITLE_SIZE=22


def check_font(path):
    font_dir = path 
    font_path = os.path.join(font_dir, IMG_FONT_FILE)
    try:
        if not os.path.isfile(font_path):
            log(f'Font {font_path} not found.')
            url=URL_FONT
            log(f'Downloading font {url}...')
            try:
                response = urllib.request.urlopen(url)
                log('Download succeeded.')
                font = response.read()
            except:
                log(f'Failed querying font from {url}.')
                return None
            os.makedirs(font_dir, exist_ok = True)
            with open(font_path, 'wb') as f:
                f.write(font)
    except:
        log(f'Failed reading font file')
        return None
    return font_path


def download(path, url):
    log(f'Downloading comic from {url}...')
    try:
        response = urllib.request.urlopen(url)
        html = response.read().decode()
    except:
        log(f'Failed querying comic from {url}.')
        return None

    title_match = re.search(r'<div[^>]*id="ctitle"[^>]*>([^<]*)</div>', html)
    img_tag_match = re.search(r'<div[^>]*id="comic"[^>]*>\s(.+)\s<\/div>', html)
    index_match = re.search(r'Permanent link .*\".*xkcd.com\/(\d+)\"', html)

    if title_match is None or img_tag_match is None or index_match is None:
        return None
    
    img_tag = img_tag_match[1]
    img_url_match = re.search(r'src="([^"]*)"', img_tag)
    img_tagline_match = re.search(r'title="([^"]*)"', img_tag)
    
    if img_url_match is None or img_tagline_match is None:
        return None

    title = title_match[1]
    img_url = img_url_match[1] 
    img_tagline = img_tagline_match[1]

    #manual char replacement
    img_tagline = img_tagline.replace('&#39;', '\'').replace('&amp', '&')

    index_str = index_match[1]
    try:
        index = int(index_str)
        index_str = str(index)
    except:
        log(f'Could not parse index {index_str}.')
        return None
    
    # pad url with protocol
    if img_url[:2] == '//':
        img_url = 'https:' + img_url 
    try:
        response = urllib.request.urlopen(img_url)
        img = response.read()
    except:
        log(f'Failed querying image from {img_url}.')
        return None

    # Write information to file
    try:
        img_path = os.path.join(path, index_str + '.png')
        with open(img_path, 'wb') as f:
            f.write(img)
        with open(os.path.join(path, index_str + '.txt'), 'w') as f:
            f.write(title + '\n')
            f.write(img_tagline + '\n')
    except:
        log(f'Failed writing to {path}, are permissions correct?')
        return None

    log('Download completed.')
    return (index, img_path, title, img_tagline)


def read_cooldown_cache(path, mode, cooldown=DEFAULT_COOLDOWN_TIME):
    cooldown_path = os.path.join(path, COOLDOWN_PREFIX + '-' + mode)
    now = datetime.now()
    cached_prefix = None
    try:
        if os.path.isfile(cooldown_path):
            with open(cooldown_path, 'r') as f:
                cached_time = datetime.strptime(f.readline().strip(), TIME_FORMAT)
                cached_prefix = f.readline().strip()
                if now - cached_time <= cooldown:
                    log(f'Found cached value for mode {mode}: {cached_prefix}')
                    return cached_prefix
    except:
        log(f'Failed reading cooldown')
    return None 
    

def write_cooldown_cache(path, mode, prefix):
    cooldown_path = os.path.join(path, COOLDOWN_PREFIX + '-' + mode)
    now = datetime.now()
    try:
        with open(cooldown_path, 'w') as f:
            f.write(now.strftime(TIME_FORMAT))
            f.write('\n')
            f.write(prefix)
            f.write('\n')
    except:
        log(f'Failed writing new cooldown time')



def download_latest(path, cooldown):
    cached = read_cooldown_cache(path, 'latest', cooldown=cooldown)
    if not cached is None:
         res = load(path, cached)
    if cached is None or res is None:
        res = download(path, LATEST_URL)
    if not res is None:
        (index, _, _, _) = res
        write_cooldown_cache(path, 'latest', str(index))
    return res


def download_random(path, cooldown):
    cached = read_cooldown_cache(path, 'random', cooldown=cooldown)
    if not cached is None:
         res = load(path, cached)
    if cached is None or res is None:
        res = download(path, RANDOM_URL)
    if not res is None:
        (index, _, _, _) = res
        write_cooldown_cache(path, 'random', str(index))
    return res


def download_index(path, index, cooldown):
    res = load(path, cached)
    if res is None:
        res = download(path, url + str(index)) 
    return res


def load(path, prefix):
    index = int(prefix)
    try:
        img_path = os.path.join(path, prefix + '.png')
        if not os.path.isfile(img_path):
            log(f'Could not find image file {path}/{prefix}.png')
            return None
        #with open(img_path, 'rb') as f:
        #    img = f.readall()
        with open(os.path.join(path, prefix + '.txt'), 'r') as f:
            title = f.readline().strip()
            tagline = f.readline().strip()
    except:
        log(f'Failed reading metadata from {path}/{prefix}.txt.')
        return None
    return (index, img_path, title, tagline)


def load_index(path, index):
    return load(path, str(index))


def load_random(path):
    # not the most optimal, but functional
    try:
        filenames = list(filter(lambda f: f.endswith('.png'), os.listdir(path)))
    except:
        log(f'Failed reading directory {path}, are permissions correct?')
        return None
    i = random.randint(0, len(filenames) - 1)
    return load(path, filenames[i].split('.')[0])


def load_latest(path):
    # use highest index through natural sorting
    try:
        filenames = list(filter(lambda f: f.endswith('.png'), os.listdir(path)))
    except:
        log(f'Failed reading directory {path}, are permissions correct?')
        return None
    return load(path, filenames[-1].split('.')[0])


def screen_resolution():
    try:
        xrandr_output = subprocess.run(['xrandr', '-q'], capture_output=True, encoding='ascii')
        match = re.search(r'(\d+)x(\d+)*', xrandr_output.stdout)
        if not match is None:
            return (int(match[1]), int(match[2]))
    except:
        log('Failed to obtain screen resolution with xrandr')
        return None
    log('Failed to obtain screen resolution with xrandr')
    return None


def lock(path, img_path, args):
    cmd = [path, '-i', img_path]
    cmd.extend(args)
    subprocess.Popen(cmd)
    # No return
    exit()


def main():
    global LOG
    
    parser = argparse.ArgumentParser(
        prog = 'xkcdlock-py',
        description = 'Launches a locking program with the XKCD comic embedded',
        epilog = 'Use at your own risk.')

    parser.add_argument('-l', '--lock',
                        help='Lock program')
    parser.add_argument('-d', '--dir',
                        help='Search directory for downloaded comics')
    parser.add_argument('mode',
                        metavar='MODE',
                        choices=MODES,
                        help=f"Which loading strategy to use. Choose between '{MODES[0]}', '{MODES[1]}' and '{MODES[2]}'")
    parser.add_argument('-i', '--index',
                        type=int,
                        help='In index mode, which index to show. If this option is not given in index mode, the program will default to latest mode.')
    parser.add_argument('-f', '--fallback',
                        metavar='MODE',
                        choices=MODES,
                        help='If no internet connection is available, which mode to use instead')
    parser.add_argument('-c', '--cooldown',
                        help='Cooldown time in format "HH:MM" for which no new comics should be downloaded for the given mode')
    parser.add_argument('-o', '--offline',
                        help='Use offline mode',
                        action='store_true')
    parser.add_argument('-v', '--verbose',
                        help='Verbose logging',
                        action='store_true')

    # Parse arguments
    args = parser.parse_args()

    if args.verbose:
        LOG=True
    
    offline = args.offline
    mode = args.mode
    path = args.dir
    if path is None:
        path = '/tmp/xkcdlock-py'
        log(f"No directory provided, choosing default directory '{path}'")
    else:
        path = os.path.expanduser(path)
    lock_bin = args.lock
    if lock_bin is None: # TODO
        lock_bin = DEFAULT_LOCK_BIN[0]
    index = args.index
    if index is None and mode == 'index':
        mode = 'latest'
        log('No index provided in \'index\' mode, switching to \'latest\' mode')
    fallback = args.fallback
    if fallback is None:
        fallback = mode
    cooldown = DEFAULT_COOLDOWN_TIME
    if not args.cooldown is None:
        cooldown_match = re.search(r'(\d\d):(\d\d)', args.cooldown)
        if cooldown_match is None:
            log(f'Failed parsing cooldown {args.cooldown}')
        else:
            hours = int(cooldown_match[1])
            minutes = int(cooldown_match[2])
            cooldown = datetime.timedelta(hours=hours, minutes=minutes) 

    # Create directory
    os.makedirs(path, exist_ok = True)

    img = None
    # Download comic
    if not offline:
        if mode == 'index':
            res = download_index(path, index, cooldown)
        elif mode == 'random':
            res = download_random(path, cooldown)
        else:
            res = download_latest(path, cooldown)

        if res is None:
            log("Download failed, falling back to offline mode '{fallback}'")
            mode = fallback
            offline = True
        else:
            (index, img_path, title, tagline) = res
            log(f'Successfully loaded comic {index}')
        
    # Load comic in offline mode
    if offline:
        res = None
        if mode == 'index':
            res = load_index(path, index)
        # fallback if index fails
        if (mode == 'index' and res is None) or mode == 'random':
            res = load_random(path)
        else:
            res = load_latest(path)

        if res is None:
            log('Offline loading failed, falling back to no image')
        else:
            (index, img_path, title, tagline) = res
            log(f'Successfully loaded comic {index}')

    # Check Font
    font_dir = os.path.expanduser(IMG_FONT_DIR)
    font_path = check_font(font_dir)
    
    # Prepare image
    resolution = screen_resolution()
    if img_path is not None and not resolution is None:
        try:
            (x, y) = resolution 
            with Image(filename=img_path) as img:
                img.background_color = IMG_BACKGROUND_COLOR
                #img.extent(x, y, gravity='center')
                
                # caption title directly above
                if not (font_path is None):
                    try:
                        img.extent(x, img.height + int(IMG_TITLE_SIZE * 1.5), gravity='south')
                        font = Font(font_path, color=IMG_TITLE_COLOR, size=IMG_TITLE_SIZE)
                        img.caption(title, font=font, gravity='north')
                    except:
                        log('Error loading font, is the path correct?')
                img.extent(x, y, gravity='center')
                if not (font_path is None):
                    try:
                        font = Font(font_path, color=IMG_CAPTION_COLOR, size=IMG_CAPTION_SIZE)
                        img.caption(tagline, font=font, gravity='south')
                        #font = Font(IMG_FONT_PATH, color=IMG_TITLE_COLOR, size=IMG_TITLE_SIZE)
                        #img.caption(title, font=font, gravity='north')
                    except:
                        log('Error loading font, is the path correct?')
                #display(img)

                img_path = os.path.join(path, 'lock.png')
                img.save(filename=img_path)
        except:
            log('Failed processing image')
    
    lock(lock_bin, img_path, DEFAULT_LOCK_ARGS)


def log(msg):
    if LOG:
        print(msg, file=sys.stderr)

if __name__ == "__main__":
    main()
