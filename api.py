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

rate_limit_storage = defaultdict(list)
RATE_LIMIT = 100
RATE_WINDOW = 3600

verification_codes = {}

ADMIN_EMAIL = 'muaves@protonmail.com' 
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '') 

ADMIN_AUTH_HASH = "0f156174a802717010777e324024340d04085429184518420140220677840134"

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
    try:
        msg = MIMEMultipart()
        msg['From'] = ADMIN_EMAIL
        msg['To'] = email
        msg['Subject'] = 'Muaves Admin - Verification Code'
        
        body = f"""
Hello!

Your verification code for Muaves Admin Panel is:

{code}

This code will expire in 10 minutes.

- Muaves Portfolio System
"""
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(ADMIN_EMAIL, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

@app.route('/')
def home():
    return jsonify({
        'message': 'Muaves Portfolio API v1.0.5',
        'security': 'Email verification required'
    })

@app.route('/api/admin/request-code', methods=['POST'])
@rate_limit_check
def request_verification_code():
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
        return jsonify({'message': 'Code sent', 'expires_in': 600})
    else:
        return jsonify({'error': 'Failed to send email'}), 500

@app.route('/api/admin/verify-code', methods=['POST'])
@rate_limit_check
def verify_code():
    data = request.json
    email = data.get('email', '').strip()
    code = data.get('code', '').strip()
    
    if email not in verification_codes:
        return jsonify({'error': 'No code requested'}), 400
    
    stored = verification_codes[email]
    if datetime.now() > stored['expires']:
        del verification_codes[email]
        return jsonify({'error': 'Code expired'}), 400
    
    if code != stored['code']:
        return jsonify({'error': 'Invalid code'}), 401
    
    del verification_codes[email]
    return jsonify({
        'message': 'Verification successful',
        'auth_token': ADMIN_AUTH_HASH
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
def get_projects():
    return jsonify(load_data()['projects'])

@app.route('/api/admin/stats')
@rate_limit_check
def admin_stats():
    auth_token = request.headers.get('X-Auth-Token')
    if auth_token != ADMIN_AUTH_HASH:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = load_data()
    stats = load_stats()
    completed = len([p for p in data['projects'] if 'completed' in p['status'].lower()])
    
    return jsonify({
        'projects': {'total': len(data['projects']), 'completed': completed},
        'links': {'total': len(data['links'])},
        'views': {'total_visits': stats['total_visits'], 'last_visit': stats['last_visit']}
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
