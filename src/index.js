const API_URL = window.location.hostname === 'localhost' ?
    'http://localhost:5000/api' :
    'https://muaves-portfolio-api.onrender.com/api';

let allProjects = [];

function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById(sectionId).classList.add('active');
}

window.addEventListener('DOMContentLoaded', async () => {
    try {
        await trackVisit();
        await loadStats();
        await loadAbout();
        await loadProjects();
        await loadLinks();

        document.getElementById('loading').style.display = 'none';
        document.getElementById('sections').style.display = 'block';
    } catch (error) {
        document.getElementById('loading').innerHTML = 'ERROR: Cannot connect to API server';
        console.error('Error:', error);
    }
});

async function trackVisit() {
    const response = await fetch(`${API_URL}/visit`, {
        method: 'POST'
    });
    const data = await response.json();
    document.getElementById('totalVisits').textContent = data.total_visits;
}

async function loadStats() {
    const response = await fetch(`${API_URL}/stats`);
    const stats = await response.json();

    const html = `
            <div class="stat-box">
                <div class="stat-number">${stats.total_projects}</div>
                <div class="stat-label">Projects</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">${stats.total_links}</div>
                <div class="stat-label">Links</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">${stats.total_visits}</div>
                <div class="stat-label">Visits</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">v${stats.version}</div>
                <div class="stat-label">Version</div>
            </div>`;

    document.getElementById('homeStats').innerHTML = html;
    document.getElementById('statsGrid').innerHTML = html;

    const topProjects = document.getElementById('topProjects');
    if (stats.most_viewed_projects && stats.most_viewed_projects.length > 0) {
        topProjects.innerHTML = stats.most_viewed_projects.map((p, i) => `
                <div class="project-box">
                    <div class="project-title">#${i + 1} ${p.name}</div>
                    <div class="project-desc">${p.description}</div>
                    <div class="project-tech">Views: ${p.views}</div>
                </div>
            `).join('');
    }
}

async function loadAbout() {
    const response = await fetch(`${API_URL}/about`);
    const data = await response.json();
    document.getElementById('aboutContent').textContent = data.about;
}

async function loadProjects() {
    const response = await fetch(`${API_URL}/projects`);
    allProjects = await response.json();
    const container = document.getElementById('projectsGrid');
    container.innerHTML = '';

    for (let i = 0; i < allProjects.length; i++) {
        const project = allProjects[i];
        const projectId = i + 1;

        const viewsResponse = await fetch(`${API_URL}/projects/${projectId}/views`);
        const viewsData = await viewsResponse.json();

        const box = document.createElement('div');
        box.className = 'project-box';
        box.onclick = () => viewProject(project, projectId);
        box.innerHTML = `
                <div class="project-title">${project.name}</div>
                <div class="project-desc">${project.description}</div>
                <div class="project-tech">
                    Tech: ${project.tech} | Status: ${project.status} | Views: ${viewsData.views}
                </div>`;
        container.appendChild(box);
    }
}

async function viewProject(project, projectId) {
    await fetch(`${API_URL}/projects/${projectId}/view`, {
        method: 'POST'
    });
    alert('PROJECT: ' + project.name + '\n\n' + project.description + '\n\nTech: ' + project.tech + '\nStatus: ' + project.status);
    loadProjects();
}

async function loadLinks() {
    const response = await fetch(`${API_URL}/links`);
    const links = await response.json();
    const container = document.getElementById('linksGrid');
    container.innerHTML = links.map(link => `
            <a href="${link.url}" target="_blank" class="link-button">${link.name}</a>
        `).join('');
}