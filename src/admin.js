const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:5000/api'
    : 'https://muaves-portfolio-api.onrender.com/api';

const PASSWORD_HASH = '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9';

const SECRET_HASH = 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3';

let AUTH_HASH = '';

async function hashText(text) {
    const encoder = new TextEncoder();
    const data = encoder.encode(text);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

async function login() {
    const password = document.getElementById('passwordInput').value;
    const secret = document.getElementById('secretInput').value;

    const passwordHash = await hashText(password);
    const secretHash = await hashText(secret);

    if (passwordHash === PASSWORD_HASH && secretHash === SECRET_HASH) {
        AUTH_HASH = await hashText(passwordHash + secretHash);
        sessionStorage.setItem('adminAuth', AUTH_HASH);

        document.getElementById('loginScreen').style.display = 'none';
        document.getElementById('adminPanel').style.display = 'block';
        loadDashboard();
    } else {
        const errorMsg = document.getElementById('errorMsg');
        errorMsg.style.display = 'block';
        setTimeout(() => errorMsg.style.display = 'none', 3000);
    }
}

function logout() {
    sessionStorage.removeItem('adminAuth');
    location.reload();
}

async function loadDashboard() {
    try {
        const response = await fetch(`${API_URL}/admin/stats`, {
            headers: { 'X-Auth-Hash': AUTH_HASH }
        });

        if (response.status === 401) {
            logout();
            return;
        }

        const stats = await response.json();
        document.getElementById('statsContainer').innerHTML = `
            <div class="stat-box">
                <div class="stat-number">${stats.projects.total}</div>
                <div>Total Projects</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">${stats.projects.completed}</div>
                <div>Completed</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">${stats.links.total}</div>
                <div>Links</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">${stats.views.total_visits}</div>
                <div>Visits</div>
            </div>`;

        await loadProjects();
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

async function loadProjects() {
    const response = await fetch(`${API_URL}/projects`);
    const projects = await response.json();

    document.getElementById('projectsList').innerHTML = projects.map((p, i) => `
        <div class="project-item">
            <div>
                <strong>${p.name}</strong><br>
                ${p.description}<br>
                <small>Tech: ${p.tech} | Status: ${p.status}</small>
            </div>
            <button class="button" onclick="deleteProject(${i + 1}, '${p.name}')" style="width: auto;">
                DELETE
            </button>
        </div>
    `).join('');
}

document.getElementById('addProjectForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const project = {
        name: document.getElementById('projectName').value,
        description: document.getElementById('projectDescription').value,
        tech: document.getElementById('projectTech').value,
        status: document.getElementById('projectStatus').value
    };

    try {
        const res = await fetch(`${API_URL}/projects`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Auth-Hash': AUTH_HASH
            },
            body: JSON.stringify(project)
        });

        if (res.ok) {
            showSuccess('PROJECT ADDED');
            document.getElementById('addProjectForm').reset();
            loadDashboard();
        }
    } catch (error) {
        showSuccess('ERROR');
    }
});

document.getElementById('addLinkForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const link = {
        name: document.getElementById('linkName').value,
        url: document.getElementById('linkUrl').value
    };

    try {
        const res = await fetch(`${API_URL}/links`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Auth-Hash': AUTH_HASH
            },
            body: JSON.stringify(link)
        });

        if (res.ok) {
            showSuccess('LINK ADDED');
            document.getElementById('addLinkForm').reset();
            loadDashboard();
        }
    } catch (error) {
        showSuccess('ERROR');
    }
});

async function deleteProject(id, name) {
    if (!confirm(`Delete "${name}"?`)) return;

    try {
        await fetch(`${API_URL}/projects/${id}`, {
            method: 'DELETE',
            headers: { 'X-Auth-Hash': AUTH_HASH }
        });
        showSuccess('DELETED');
        loadDashboard();
    } catch (error) {
        showSuccess('ERROR');
    }
}

function showSuccess(msg) {
    const el = document.getElementById('successMsg');
    el.textContent = msg;
    el.style.display = 'block';
    setTimeout(() => el.style.display = 'none', 3000);
}

window.addEventListener('DOMContentLoaded', () => {
    const storedAuth = sessionStorage.getItem('adminAuth');
    if (storedAuth) {
        AUTH_HASH = storedAuth;
        document.getElementById('loginScreen').style.display = 'none';
        document.getElementById('adminPanel').style.display = 'block';
        loadDashboard();
    }
});