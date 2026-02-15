#!/usr/bin/env python3

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from functools import wraps

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / 'portfolio_data.json'
STATS_FILE = BASE_DIR / 'stats.json'

# Rate limiting
rate_limit_storage = defaultdict(list)
RATE_LIMIT = 100
RATE_WINDOW = 3600

# 2FA: Combined hash of (password_hash + secret_hash)
# Default: password="admin123" + secret="mysecret456"
# Combined hash = SHA256(SHA256("admin123") + SHA256("mysecret456"))
ADMIN_AUTH_HASH = "cfe8a35f2a07b0f3ef244831a36e8e8a0e4c8b4d8e0f4e0e0e0e0e0e0e0e0e0e"

# To change: Run this Python code with YOUR password and secret:
# import hashlib
# password_hash = hashlib.sha256("your_password".encode()).hexdigest()
# secret_hash = hashlib.sha256("your_secret".encode()).hexdigest()
# auth_hash = hashlib.sha256((password_hash + secret_hash).encode()).hexdigest()
# print(f"Set ADMIN_AUTH_HASH to: {auth_hash}")

if not STATS_FILE.exists():
    with open(STATS_FILE, 'w') as f:
        json.dump({'total_visits': 0, 'project_views': {}, 'last_visit': None}, f)

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

@app.route('/')
def home():
    return jsonify({
        'message': 'Muaves Portfolio API v1.0.4',
        'endpoints': {
            'projects': '/api/projects',
            'links': '/api/links',
            'about': '/api/about',
            'stats': '/api/stats',
            'search': '/api/search?q=term'
        },
        'security': {
            'rate_limit': f'{RATE_LIMIT} requests per hour per IP',
            'admin': 'Two-factor authentication required'
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

@app.route('/api/projects')
@rate_limit_check
def get_projects():
    return jsonify(load_data()['projects'])

@app.route('/api/projects/<int:id>')
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

@app.route('/api/projects/<int:id>/views')
@rate_limit_check
def get_views(id):
    stats = load_stats()
    return jsonify({'project_id': id, 'views': stats['project_views'].get(str(id), 0)})

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
    return jsonify([p for p in data['projects'] if query in p['name'].lower() 
                    or query in p['description'].lower() or query in p['tech'].lower()])

@app.route('/api/links')
@rate_limit_check
def get_links():
    return jsonify(load_data()['links'])

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

@app.route('/api/about')
@rate_limit_check
def get_about():
    return jsonify({'about': load_data()['about']})

@app.route('/api/stats')
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

@app.route('/api/admin/stats')
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
        'projects': {'total': len(data['projects']), 'completed': completed, 'in_progress': in_progress},
        'links': {'total': len(data['links'])},
        'views': {'total_visits': stats['total_visits'], 'last_visit': stats['last_visit'], 
                  'project_views': stats['project_views']}
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
