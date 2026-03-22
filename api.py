#!/usr/bin/env python3

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import hashlib
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from functools import wraps
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / 'portfolio_data.json'
STATS_FILE = BASE_DIR / 'stats.json'

# Rate limiting
rate_limit_storage = defaultdict(list)
RATE_LIMIT = 100
RATE_WINDOW = 3600

verification_codes = {}

ADMIN_EMAIL = 'muaves@protonmail.com'  
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '') 

ADMIN_AUTH_HASH = "temp-hash-after-email-verification"

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
            return jsonify({'error': 'Rate limit exceeded'}), 429
        rate_limit_storage[ip].append(now)
        return f(*args, **kwargs)
    return decorated_function

def send_verification_email(email, code):
    """Send verification code via email"""
    try:
        GMAIL_SENDER = 'gbrzanchetta21@gmail.com'
        
        msg = MIMEMultipart()
        msg['From'] = GMAIL_SENDER
        msg['To'] = email
        msg['Subject'] = 'Muaves Admin - Verification Code'
        
        body = f"""
Hello!

Your verification code for Muaves Admin Panel is:

{code}

This code will expire in 10 minutes.

If you didn't request this, please ignore this email.

- Muaves Portfolio System
"""
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def verify_admin(auth_hash):
    return auth_hash == ADMIN_AUTH_HASH

@app.route('/')
def home():
    return jsonify({
        'message': 'Muaves Portfolio API v1.0.5',
        'endpoints': {
            'projects': '/api/projects',
            'links': '/api/links',
            'about': '/api/about',
            'stats': '/api/stats',
            'search': '/api/search?q=term'
        },
        'security': 'Email verification + 2FA required for admin'
    })

@app.route('/api/admin/request-code', methods=['POST'])
@rate_limit_check
def request_verification_code():
    """Request email verification code"""
    data = request.json
    email = data.get('email', '').strip()
    
    if email != ADMIN_EMAIL:
        return jsonify({'error': 'Unauthorized email'}), 401
    
    code = str(random.randint(100000, 999999))
    
    verification_codes[email] = {
        'code': code,
        'expires': datetime.now() + timedelta(minutes=10)
    }
    
    if send_verification_email(email, code):
        return jsonify({
            'message': 'Verification code sent to your email',
            'expires_in': 600  
        })
    else:
        return jsonify({'error': 'Failed to send email'}), 500

@app.route('/api/admin/verify-code', methods=['POST'])
@rate_limit_check
def verify_code():
    """Verify email code and generate auth token"""
    data = request.json
    email = data.get('email', '').strip()
    code = data.get('code', '').strip()
    
    if email not in verification_codes:
        return jsonify({'error': 'No verification code requested'}), 400
    
    stored = verification_codes[email]
    
    if datetime.now() > stored['expires']:
        del verification_codes[email]
        return jsonify({'error': 'Code expired'}), 400
    
    if code != stored['code']:
        return jsonify({'error': 'Invalid code'}), 401
    
    session_token = hashlib.sha256(f"{email}{code}{datetime.now()}".encode()).hexdigest()
    
    del verification_codes[email]
    
    return jsonify({
        'message': 'Verification successful',
        'auth_token': session_token
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
    auth_token = request.headers.get('X-Auth-Token')
    if not auth_token:
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
    auth_token = request.headers.get('X-Auth-Token')
    if not auth_token:
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
    auth_token = request.headers.get('X-Auth-Token')
    if not auth_token:
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
        'version': '1.0.5',
        'total_visits': stats['total_visits'],
        'last_visit': stats['last_visit'],
        'most_viewed_projects': top_projects
    })

@app.route('/api/admin/stats')
@rate_limit_check
def admin_stats():
    auth_token = request.headers.get('X-Auth-Token')
    if not auth_token:
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
    print(f"\nAdmin email: {ADMIN_EMAIL}")
    if not EMAIL_PASSWORD:
        print("WARNING: EMAIL_PASSWORD not set! Email verification will not work.")
        print("Set environment variable: EMAIL_PASSWORD=your-app-password")
    app.run(debug=True, port=5000, host='0.0.0.0')
