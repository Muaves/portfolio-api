#!/usr/bin/env python3

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import hashlib
import random
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from functools import wraps
import os

app = Flask(__name__)
CORS(app)
app.url_map.strict_slashes = False

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / 'portfolio_data.json'
STATS_FILE = BASE_DIR / 'stats.json'

rate_limit_storage = defaultdict(list)
RATE_LIMIT = 100
RATE_WINDOW = 3600

def load_data():
    if not DATA_FILE.exists():
        return {"projects": [], "links": [], "about": ""}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return {"projects": [], "links": [], "about": ""}

def save_stats(stats):
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)

def load_stats():
    default_stats = {'total_visits': 0, 'project_views': {}, 'last_visit': None}
    if not STATS_FILE.exists():
        save_stats(default_stats)
        return default_stats
    with open(STATS_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            save_stats(default_stats)
            return default_stats

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
            return jsonify({'error': 'Rate limit exceeded'}), 429
        rate_limit_storage[ip].append(now)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'version': '1.0.7',
        'endpoints': ['/api/projects', '/api/links', '/api/about', '/api/stats', '/api/visit']
    })

@app.route('/api/visit', methods=['POST'])
@rate_limit_check
def track_visit():
    stats = load_stats()
    stats['total_visits'] = stats.get('total_visits', 0) + 1
    stats['last_visit'] = datetime.now().isoformat()
    save_stats(stats)
    return jsonify(stats)

@app.route('/api/projects')
@rate_limit_check
def get_projects():
    return jsonify(load_data().get('projects', []))

@app.route('/api/projects/<int:id>')
@rate_limit_check
def get_project(id):
    projects = load_data().get('projects', [])
    if 0 <= id - 1 < len(projects):
        return jsonify(projects[id - 1])
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/projects/<int:id>/view', methods=['POST'])
@rate_limit_check
def increment_view(id):
    stats = load_stats()
    pid = str(id)
    if 'project_views' not in stats: stats['project_views'] = {}
    stats['project_views'][pid] = stats['project_views'].get(pid, 0) + 1
    save_stats(stats)
    return jsonify({'project_id': id, 'views': stats['project_views'][pid]})

@app.route('/api/stats')
@rate_limit_check
def get_stats():
    data = load_data()
    stats = load_stats()
    projects = data.get('projects', [])
    views = stats.get('project_views', {})
    sorted_views = sorted(views.items(), key=lambda x: x[1], reverse=True)[:3]
    top = []
    for pid, v in sorted_views:
        try:
            idx = int(pid) - 1
            if 0 <= idx < len(projects):
                p = projects[idx].copy()
                p['views'] = v
                top.append(p)
        except: continue
    return jsonify({
        'total_projects': len(projects),
        'total_visits': stats.get('total_visits', 0),
        'last_visit': stats.get('last_visit'),
        'top_projects': top
    })

@app.route('/api/links')
@rate_limit_check
def get_links():
    return jsonify(load_data().get('links', []))

@app.route('/api/about')
@rate_limit_check
def get_about():
    return jsonify({'about': load_data().get('about', '')})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
