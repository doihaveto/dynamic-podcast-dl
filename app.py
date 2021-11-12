import os
import json
import settings
import subprocess
import email.utils
import urllib.parse
from lxml import etree
from flask import Flask, Response, request, render_template
from datetime import datetime
from mutagen.id3 import ID3
from mutagen.mp3 import MP3

YOUTUBE_DL_OPTIONS = ['yt-dlp', '-x', '--audio-format', 'mp3', '-f', 'bestaudio', '--no-continue', '--write-info-json', '-o', '%(title).100s-%(id).20s.%(timestamp)s.%(ext)s']

app = Flask(__name__)

def youtube_dl(url, feed_name):
    yield '<pre>'
    proc = subprocess.Popen(YOUTUBE_DL_OPTIONS + [url], cwd='files', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    line = b''
    info = {'metadata': {}, 'file': None}
    while True:
        line += proc.stdout.read(1).replace(b'\r', b'\n')
        if not line:
            err = proc.stderr.readline()
            if err:
                yield err
            break
        if b'\n' in line:
            line = line.decode()
            if 'as JSON to:' in line:
                info['metadata_file'] = os.path.join('files', line.split('as JSON to:')[1].strip())
            elif 'Destination: ' in line:
                info['file'] = line.split('Destination: ')[1].strip()
            elif 'ExtractAudio' in line and 'exists, skipping' in line:
                info['file'] = line.split('Post-process file ')[1].split(' exists, skipping')[0]
            yield line
            line = b''
    if 'metadata_file' in info:
        with open(info['metadata_file']) as f:
            info['metadata'] = json.load(f)
    if info['file']:
        yield 'Adding to RSS feed... '
        rss_add_file(feed_name, info)
        yield 'done'
    else:
        yield 'Unable to locate file'

def rss_add_file(feed_name, file_info):
    feed = settings.FEEDS[feed_name]
    if os.path.exists(f'rss/{feed_name}.rss'):
        rss = etree.parse(f'rss/{feed_name}.rss')
        channel = rss.find('channel')
    else:
        rss = etree.Element('rss')
        channel = etree.SubElement(rss, 'channel')
        etree.SubElement(channel, 'title').text = feed['title']
    item = etree.SubElement(channel, 'item')
    enclosure = etree.SubElement(item, 'enclosure')
    enclosure.set('length', '0')
    enclosure.set('type', 'audio/mpeg')
    enclosure.set('url', urllib.parse.urljoin(settings.MP3_URL, urllib.parse.quote(file_info['file'])))
    audio = MP3(f'files/{file_info["file"]}')
    etree.SubElement(item, 'duration').text = str(int(audio.info.length))
    if file_info['metadata'].get('title'):
        title = file_info['metadata']['title']
    else:
        id3 = ID3(f'files/{file_info["file"]}')
        title = '{} - {}'.format(id3['TRCK'].text[0], id3['TIT2'].text[0])
    etree.SubElement(item, 'title').text = title
    etree.SubElement(item, 'pubDate').text = email.utils.format_datetime(datetime.now())
    if file_info['metadata'].get('description'):
        etree.SubElement(item, 'description').text = file_info['metadata']['description']
    with open(f'rss/{feed_name}.rss', 'wb') as f:
        f.write(etree.tostring(rss, pretty_print=True))

def validate_login(request):
    feed_name = request.args.get('feed')
    access_key = request.args.get('key')
    if feed_name not in settings.FEEDS:
        return 'Feed not found', 404
    elif access_key != settings.FEEDS[feed_name]['access_key']:
        return 'Incorrect access key', 403

@app.route('/download')
def download_api():
    valid = validate_login(request)
    if valid is not None:
        return valid
    feed_name = request.args.get('feed')
    url = request.args.get('url')
    if not url or not url.startswith(('http://', 'https://')):
        return 'Invalid URL', 400
    return Response(youtube_dl(url, feed_name))

@app.route('/')
def index():
    valid = validate_login(request)
    if valid is not None:
        return valid
    return render_template('index.html')
