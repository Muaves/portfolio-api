#!/usr/bin/env python3

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / 'portfolio_data.json'
STATS_FILE = BASE_DIR / 'stats.json'

# Initialize stats if not exists
if not STATS_FILE.exists():
    with open(STATS_FILE, 'w') as f:
        json.dump({
            'total_visits': 0,
            'project_views': {},
            'last_visit': None
        }, f)

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

@app.route('/')
def home():
    return jsonify({
        'message': 'Muaves Portfolio API v1.0.4',
        'endpoints': {
            'projects': '/api/projects',
            'links': '/api/links',
            'about': '/api/about',
            'stats': '/api/stats',
            'search': '/api/search?q=term',
            'filter': '/api/projects/filter?status=Completed'
        }
    })

@app.route('/api/visit', methods=['POST'])
def track_visit():
    stats = load_stats()
    stats['total_visits'] += 1
    stats['last_visit'] = datetime.now().isoformat()
    save_stats(stats)
    return jsonify(stats)

@app.route('/api/projects')
def get_projects():
    data = load_data()
    return jsonify(data['projects'])

@app.route('/api/projects/<int:id>')
def get_project(id):
    data = load_data()
    if 0 <= id - 1 < len(data['projects']):
        return jsonify(data['projects'][id - 1])
    return jsonify({'error': 'Project not found'}), 404

@app.route('/api/projects/<int:id>/view', methods=['POST'])
def increment_view(id):
    stats = load_stats()
    project_id = str(id)
    
    if project_id not in stats['project_views']:
        stats['project_views'][project_id] = 0
    
    stats['project_views'][project_id] += 1
    save_stats(stats)
    
    return jsonify({
        'project_id': id,
        'views': stats['project_views'][project_id]
    })

@app.route('/api/projects/<int:id>/views')
def get_views(id):
    stats = load_stats()
    project_id = str(id)
    views = stats['project_views'].get(project_id, 0)
    return jsonify({'project_id': id, 'views': views})

@app.route('/api/projects', methods=['POST'])
def add_project():
    data = load_data()
    new_project = request.json
    
    required_fields = ['name', 'description', 'tech', 'status']
    if not all(field in new_project for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    data['projects'].append(new_project)
    save_data(data)
    
    return jsonify({
        'message': 'Project added successfully!',
        'project': new_project
    }), 201

@app.route('/api/projects/<int:id>', methods=['PUT'])
def update_project(id):
    data = load_data()
    
    if 0 <= id - 1 < len(data['projects']):
        updated_project = request.json
        data['projects'][id - 1] = updated_project
        save_data(data)
        return jsonify({
            'message': 'Project updated!',
            'project': updated_project
        })
    
    return jsonify({'error': 'Project not found'}), 404

@app.route('/api/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    data = load_data()
    
    if 0 <= id - 1 < len(data['projects']):
        deleted = data['projects'].pop(id - 1)
        save_data(data)
        return jsonify({
            'message': 'Project deleted!',
            'project': deleted
        })
    
    return jsonify({'error': 'Project not found'}), 404

@app.route('/api/projects/filter')
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
def search():
    data = load_data()
    query = request.args.get('q', '').lower()
    
    if not query:
        return jsonify([])
    
    results = []
    for project in data['projects']:
        if (query in project['name'].lower() or 
            query in project['description'].lower() or 
            query in project['tech'].lower()):
            results.append(project)
    
    return jsonify(results)

@app.route('/api/links')
def get_links():
    data = load_data()
    return jsonify(data['links'])

@app.route('/api/links', methods=['POST'])
def add_link():
    data = load_data()
    new_link = request.json
    
    if 'name' not in new_link or 'url' not in new_link:
        return jsonify({'error': 'Missing name or url'}), 400
    
    data['links'].append(new_link)
    save_data(data)
    
    return jsonify({
        'message': 'Link added!',
        'link': new_link
    }), 201

@app.route('/api/about')
def get_about():
    data = load_data()
    return jsonify({'about': data['about']})

@app.route('/api/about', methods=['PUT'])
def update_about():
    data = load_data()
    new_about = request.json.get('about')
    
    if not new_about:
        return jsonify({'error': 'Missing about text'}), 400
    
    data['about'] = new_about
    save_data(data)
    
    return jsonify({
        'message': 'About updated!',
        'about': new_about
    })

@app.route('/api/stats')
def get_stats():
    data = load_data()
    stats = load_stats()
    
    return jsonify({
        'total_projects': len(data['projects']),
        'total_links': len(data['links']),
        'version': data['version'],
        'total_visits': stats['total_visits'],
        'last_visit': stats['last_visit'],
        'most_viewed_projects': get_top_projects(stats)
    })

def get_top_projects(stats):
    if not stats['project_views']:
        return []
    
    data = load_data()
    sorted_views = sorted(
        stats['project_views'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]
    
    top_projects = []
    for project_id, views in sorted_views:
        idx = int(project_id) - 1
        if 0 <= idx < len(data['projects']):
            project = data['projects'][idx].copy()
            project['views'] = views
            top_projects.append(project)
    
    return top_projects

@app.route('/api/admin/stats')
def admin_stats():
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
        'links': {
            'total': len(data['links'])
        },
        'views': {
            'total_visits': stats['total_visits'],
            'last_visit': stats['last_visit'],
            'project_views': stats['project_views']
        }
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')