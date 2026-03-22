#!/usr/bin/env python3
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from pathlib import Path

app = Flask(__name__)
CORS(app)

B = Path(__file__).parent
D = B / 'portfolio_data.json'
S = B / 'stats.json'
A_K = "TungTungTungSahur"

def load_j(p):
    with open(p, 'r', encoding='utf-8') as f: return json.load(f)

@app.route('/api/visit', methods=['POST'])
def track_visit():
    s = load_j(S)
    s['total_visits'] += 1
    with open(S, 'w') as f: json.dump(s, f)
    return jsonify(s)

@app.route('/api/projects')
def get_projects():
    return jsonify(load_j(D)['projects'])

@app.route('/api/admin/stats')
def admin_stats():
    if request.headers.get('X-Auth-Token') != A_K:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = load_j(D)
    stats = load_j(S)
    return jsonify({
        'projects': {'total': len(data['projects'])},
        'views': {'total_visits': stats['total_visits']}
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
