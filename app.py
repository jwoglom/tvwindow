#!/usr/bin/env python3

import os
import arrow
import logging
import json
import time
import asyncio
import random
from urllib.parse import urlparse

from flask import Flask, Response, request, abort, redirect, jsonify, render_template, send_from_directory

is_gunicorn = "gunicorn" in os.environ.get("SERVER_SOFTWARE", "")
if is_gunicorn:
    from prometheus_flask_exporter.multiprocess import GunicornInternalPrometheusMetrics as PrometheusMetrics
else:
    from prometheus_flask_exporter import PrometheusMetrics

from prometheus_client import Counter, Gauge

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)

app = Flask(__name__)

metrics = PrometheusMetrics(app)


FOLDER = os.getenv('FOLDER', '/videos/')

def _is_video(p):
    if not os.path.isfile(p):
        return False

    EXTS = ['.mp4', '.webm']

    return any([p.lower().endswith(ext) for ext in EXTS])

def grab_src(filt=None):
    files = [f for f in os.listdir(FOLDER) if _is_video(os.path.join(FOLDER, f))]
    if filt:
        files = [f for f in files if filt in f]

    if not files:
        return None

    return os.path.join('/videos/', random.choice(files))


@app.route('/')
def index():
    cache_bust = str(urlparse(request.url).query or '').split('&ts=')[0] + '&ts=' + str(int(time.time()))
    return render_template('index.html',
                           cache_bust=cache_bust,
                           seconds=request.args.get('seconds', os.getenv('SECONDS', 300)),
                           src=grab_src(request.args.get('filter', None)))

@app.route('/videos/<path:path>')
def render_static(path):
    return send_from_directory(FOLDER, path, conditional=True)

@app.route('/folder')
def folder_route():
    return jsonify([f for f in os.listdir(FOLDER) if _is_video(os.path.join(FOLDER, f))])


@app.route('/healthz')
def healthz_route():
    return 'ok'