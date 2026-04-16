#!/usr/bin/env python3
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import time
import httpx
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from functools import wraps

app = Flask(__name__)
CORS(app)
app.url_map.strict_slashes = False

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / 'portfolio_data.json'
STATS_FILE = BASE_DIR / 'stats.json'
RADIO_FILE = BASE_DIR / 'radio_data.json'

rate_limit_storage = defaultdict(list)
RATE_LIMIT = 100
RATE_WINDOW = 3600

ADMIN_AUTH_HASH = "cfe8a35f2a07b0f3ef244831a36e8e8a0e4c8b4d8e0f4e0e0e0e0e0e0e0e0e0e"

GITHUB_RAW_BASE = os.environ.get(
    "RADIO_GITHUB_RAW",
    "https://raw.githubusercontent.com/Muaves/portfolio-api/main/radio/tracks"
)

STATION_START = time.time()

if not STATS_FILE.exists():
    with open(STATS_FILE, 'w') as f:
        json.dump({'total_visits': 0, 'project_views': {}, 'last_visit': None}, f)

if not RADIO_FILE.exists():
    with open(RADIO_FILE, 'w') as f:
        json.dump([], f)


def load_data():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_stats():
    with open(STATS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_stats(stats):
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)

def load_radio():
    with open(RADIO_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_radio(tracks):
    with open(RADIO_FILE, 'w', encoding='utf-8') as f:
        json.dump(tracks, f, indent=2)

def get_client_ip():
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    return request.remote_addr

def rate_limit_check(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = get_client_ip()
        now = datetime.now()
        rate_limit_storage[ip] = [t for t in rate_limit_storage[ip] if now - t < timedelta(seconds=RATE_WINDOW)]
        if len(rate_limit_storage[ip]) >= RATE_LIMIT:
            return jsonify({'error': 'Rate limit exceeded. Try again later.'}), 429
        rate_limit_storage[ip].append(now)
        return f(*args, **kwargs)
    return decorated_function

def verify_admin(auth_hash):
    return auth_hash == ADMIN_AUTH_HASH


# ---------------------------------------------------------------------------
# Existing portfolio endpoints
# ---------------------------------------------------------------------------

@app.route('/')
def home():
    return jsonify({
        'message': 'Muaves Portfolio API v1.1.0',
        'endpoints': {
            'projects': '/api/projects',
            'links': '/api/links',
            'about': '/api/about',
            'stats': '/api/stats',
            'search': '/api/search?q=term',
            'radio': {
                'tracks': '/api/radio/tracks',
                'now_playing': '/api/radio/now-playing',
                'add_track': 'POST /api/radio/tracks (admin)',
                'delete_track': 'DELETE /api/radio/tracks/<id> (admin)',
            }
        },
        'security': {
            'rate_limit': f'{RATE_LIMIT} requests per hour per IP',
            'admin': 'X-Auth-Hash header required'
        }
    })

@app.route('/api/visit', methods=['POST'])
@rate_limit_check
def track_visit():
    stats = load_stats()
    stats['total_visits'] += 1
    stats['last_visit'] = datetime.now().isoformat()
    save_stats(stats)
    return jsonify(stats)

@app.route('/api/projects', methods=['GET'])
@rate_limit_check
def get_projects():
    return jsonify(load_data()['projects'])

@app.route('/api/projects/<int:id>', methods=['GET'])
@rate_limit_check
def get_project(id):
    data = load_data()
    if 0 <= id - 1 < len(data['projects']):
        return jsonify(data['projects'][id - 1])
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/projects/<int:id>/view', methods=['POST'])
@rate_limit_check
def increment_view(id):
    stats = load_stats()
    pid = str(id)
    if pid not in stats['project_views']:
        stats['project_views'][pid] = 0
    stats['project_views'][pid] += 1
    save_stats(stats)
    return jsonify({'project_id': id, 'views': stats['project_views'][pid]})

@app.route('/api/projects/<int:id>/views', methods=['GET'])
@rate_limit_check
def get_views(id):
    stats = load_stats()
    return jsonify({'project_id': id, 'views': stats['project_views'].get(str(id), 0)})

@app.route('/api/projects/filter')
@rate_limit_check
def filter_projects():
    data = load_data()
    projects = data['projects']
    status = request.args.get('status')
    tech = request.args.get('tech')
    if status:
        projects = [p for p in projects if status.lower() in p['status'].lower()]
    if tech:
        projects = [p for p in projects if tech.lower() in p['tech'].lower()]
    return jsonify(projects)

@app.route('/api/search')
@rate_limit_check
def search():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    data = load_data()
    return jsonify([
        p for p in data['projects']
        if query in p['name'].lower()
        or query in p['description'].lower()
        or query in p['tech'].lower()
    ])

@app.route('/api/links', methods=['GET'])
@rate_limit_check
def get_links():
    return jsonify(load_data()['links'])

@app.route('/api/about', methods=['GET'])
@rate_limit_check
def get_about():
    return jsonify({'about': load_data()['about']})

@app.route('/api/stats', methods=['GET'])
@rate_limit_check
def get_stats():
    data = load_data()
    stats = load_stats()
    sorted_views = sorted(stats['project_views'].items(), key=lambda x: x[1], reverse=True)[:3]
    top_projects = []
    for pid, views in sorted_views:
        idx = int(pid) - 1
        if 0 <= idx < len(data['projects']):
            p = data['projects'][idx].copy()
            p['views'] = views
            top_projects.append(p)
    return jsonify({
        'total_projects': len(data['projects']),
        'total_links': len(data['links']),
        'version': data['version'],
        'total_visits': stats['total_visits'],
        'last_visit': stats['last_visit'],
        'most_viewed_projects': top_projects
    })

@app.route('/api/projects', methods=['POST'])
@rate_limit_check
def add_project():
    auth_hash = request.headers.get('X-Auth-Hash')
    if not verify_admin(auth_hash):
        return jsonify({'error': 'Unauthorized'}), 401
    data = load_data()
    new_project = request.json
    if not all(k in new_project for k in ['name', 'description', 'tech', 'status']):
        return jsonify({'error': 'Missing fields'}), 400
    data['projects'].append(new_project)
    save_data(data)
    return jsonify({'message': 'Added!', 'project': new_project}), 201

@app.route('/api/projects/<int:id>', methods=['DELETE'])
@rate_limit_check
def delete_project(id):
    auth_hash = request.headers.get('X-Auth-Hash')
    if not verify_admin(auth_hash):
        return jsonify({'error': 'Unauthorized'}), 401
    data = load_data()
    if 0 <= id - 1 < len(data['projects']):
        deleted = data['projects'].pop(id - 1)
        save_data(data)
        return jsonify({'message': 'Deleted!', 'project': deleted})
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/links', methods=['POST'])
@rate_limit_check
def add_link():
    auth_hash = request.headers.get('X-Auth-Hash')
    if not verify_admin(auth_hash):
        return jsonify({'error': 'Unauthorized'}), 401
    data = load_data()
    new_link = request.json
    if 'name' not in new_link or 'url' not in new_link:
        return jsonify({'error': 'Missing fields'}), 400
    data['links'].append(new_link)
    save_data(data)
    return jsonify({'message': 'Added!', 'link': new_link}), 201

@app.route('/api/admin/stats', methods=['GET'])
@rate_limit_check
def admin_stats():
    auth_hash = request.headers.get('X-Auth-Hash')
    if not verify_admin(auth_hash):
        return jsonify({'error': 'Unauthorized'}), 401
    data = load_data()
    stats = load_stats()
    completed = len([p for p in data['projects'] if 'completed' in p['status'].lower()])
    in_progress = len([p for p in data['projects'] if 'progress' in p['status'].lower()])
    return jsonify({
        'projects': {
            'total': len(data['projects']),
            'completed': completed,
            'in_progress': in_progress
        },
        'links': {'total': len(data['links'])},
        'views': {
            'total_visits': stats['total_visits'],
            'last_visit': stats['last_visit'],
            'project_views': stats['project_views']
        }
    })


# ---------------------------------------------------------------------------
# Radio endpoints
# ---------------------------------------------------------------------------

@app.route('/api/radio/tracks', methods=['GET'])
@rate_limit_check
def radio_tracks():
    tracks = load_radio()
    for i, t in enumerate(tracks):
        t['id'] = i
        t['url'] = f"{GITHUB_RAW_BASE}/{t['filename']}"
    return jsonify(tracks)


@app.route('/api/radio/now-playing', methods=['GET'])
@rate_limit_check
def radio_now_playing():
    tracks = load_radio()
    if not tracks:
        return jsonify({'error': 'No tracks in playlist'}), 404

    total_duration = sum(t.get('duration', 180) for t in tracks)
    if total_duration == 0:
        return jsonify({'error': 'Tracks have no duration set'}), 500

    elapsed = (time.time() - STATION_START) % total_duration

    cumulative = 0
    for i, track in enumerate(tracks):
        duration = track.get('duration', 180)
        if cumulative + duration > elapsed:
            result = dict(track)
            result['id'] = i
            result['url'] = f"{GITHUB_RAW_BASE}/{track['filename']}"
            result['seek'] = round(elapsed - cumulative, 2)
            result['index'] = i
            return jsonify(result)
        cumulative += duration

    first = dict(tracks[0])
    first['id'] = 0
    first['url'] = f"{GITHUB_RAW_BASE}/{tracks[0]['filename']}"
    first['seek'] = 0
    first['index'] = 0
    return jsonify(first)


@app.route('/api/radio/tracks', methods=['POST'])
@rate_limit_check
def radio_add_track():
    auth_hash = request.headers.get('X-Auth-Hash')
    if not verify_admin(auth_hash):
        return jsonify({'error': 'Unauthorized'}), 401

    body = request.json
    if not all(k in body for k in ['title', 'artist', 'filename', 'duration']):
        return jsonify({'error': 'Missing fields: title, artist, filename, duration'}), 400

    tracks = load_radio()
    new_track = {
        'title': body['title'],
        'artist': body['artist'],
        'filename': body['filename'],
        'duration': float(body['duration']),
    }
    tracks.append(new_track)
    save_radio(tracks)
    return jsonify({'message': 'Track added!', 'track': new_track}), 201


@app.route('/api/radio/tracks/<int:id>', methods=['DELETE'])
@rate_limit_check
def radio_delete_track(id):
    auth_hash = request.headers.get('X-Auth-Hash')
    if not verify_admin(auth_hash):
        return jsonify({'error': 'Unauthorized'}), 401

    tracks = load_radio()
    if not (0 <= id < len(tracks)):
        return jsonify({'error': 'Track not found'}), 404

    deleted = tracks.pop(id)
    save_radio(tracks)
    return jsonify({'message': 'Deleted!', 'track': deleted})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port, host='0.0.0.0')
