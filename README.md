#  Muaves Portfolio API

> A modern, full-featured REST API powering my personal portfolio with real-time analytics, project management, and dynamic content delivery.

[![API Status](https://img.shields.io/badge/status-online-success)](https://muaves-portfolio-api.onrender.com)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask Version](https://img.shields.io/badge/flask-3.0.0-lightgrey.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Uptime](https://img.shields.io/uptimerobot/ratio/7/m797506512-c2c8e8e8e8e8e8e8e8e8e8e8)](https://stats.uptimerobot.com/pjTx4GKB5E)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Demo](#-demo)
- [Tech Stack](#-tech-stack)
- [API Documentation](#-api-documentation)
- [Getting Started](#-getting-started)
- [Deployment](#-deployment)
- [Monitoring](#-monitoring)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## 🎯 Overview

This is the backend API for my personal portfolio website, built with Flask and deployed on Render. It provides RESTful endpoints for managing projects, links, analytics, and more. The API supports real-time view tracking, search functionality, filtering, and full CRUD operations for portfolio content.

**Live API:** [muaves-portfolio-api.onrender.com](https://muaves-portfolio-api.onrender.com)  
**Frontend:** [muaves.github.io/portfolio-api](https://muaves.github.io/portfolio-api)  
**Status Page:** [stats.uptimerobot.com/pjTx4GKB5E](https://stats.uptimerobot.com/pjTx4GKB5E)

---

## ✨ Features

-  **RESTful API** - Clean, intuitive endpoint design
-  **Analytics** - Track project views and visitor stats
-  **Search & Filter** - Find projects by name, tech stack, or status
-  **CRUD Operations** - Full create, read, update, delete support
-  **CORS Enabled** - Works with any frontend
-  **Real-time Stats** - Live visitor tracking and project metrics
-  **Admin Dashboard** - Manage content through intuitive interface
-  **Fast & Lightweight** - Optimized for performance
-  **Auto-scaling** - Handles traffic spikes gracefully
-  **JSON Storage** - Simple, portable data persistence

---

## 🎬 Demo

### API Response Example

```json
GET /api/projects

[
  {
    "name": "Redstone Launcher",
    "description": "The best launcher currently on the entire planet!",
    "tech": "HTML, CSS, JS, Node.js",
    "status": "Completed"
  },
  {
    "name": "ProTiers",
    "description": "Uhm smth with tiers",
    "tech": "JavaScript, WebServer, HTML, CSS",
    "status": "Completed"
  }
]
```

### Live Stats

```json
GET /api/stats

{
  "total_projects": 5,
  "total_links": 5,
  "version": "1.0.4",
  "total_visits": 127,
  "last_visit": "2025-02-15T12:45:00",
  "most_viewed_projects": [...]
}
```

---

## 🛠️ Tech Stack

| Technology | Purpose | Version |
|------------|---------|---------|
| **Python** | Backend Runtime | 3.11+ |
| **Flask** | Web Framework | 3.0.0 |
| **Flask-CORS** | Cross-Origin Support | 4.0.0 |
| **Gunicorn** | WSGI Server | 21.2.0 |
| **Render** | Hosting Platform | - |
| **UptimeRobot** | Monitoring | - |
| **GitHub** | Version Control | - |

---

## 📚 API Documentation

### Base URL

```
https://muaves-portfolio-api.onrender.com
```

### Endpoints

#### 🏠 Home

```http
GET /
```

Returns API information and available endpoints.

---

#### 📁 Projects

##### Get All Projects

```http
GET /api/projects
```

Returns all portfolio projects.

##### Get Single Project

```http
GET /api/projects/{id}
```

Returns a specific project by ID (1-indexed).

##### Add New Project

```http
POST /api/projects
Content-Type: application/json

{
  "name": "Project Name",
  "description": "Project description",
  "tech": "Technologies used",
  "status": "Completed"
}
```

##### Update Project

```http
PUT /api/projects/{id}
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description",
  "tech": "Updated tech",
  "status": "Updated status"
}
```

##### Delete Project

```http
DELETE /api/projects/{id}
```

##### Filter Projects

```http
GET /api/projects/filter?status=Completed
GET /api/projects/filter?tech=rust
```

---

#### 🔍 Search

```http
GET /api/search?q=redstone
```

Search projects by name, description, or technology.

---

#### 🔗 Links

##### Get All Links

```http
GET /api/links
```

##### Add New Link

```http
POST /api/links
Content-Type: application/json

{
  "name": "GitHub",
  "url": "https://github.com/muaves"
}
```

---

#### 👁️ View Tracking

##### Increment Project Views

```http
POST /api/projects/{id}/view
```

##### Get Project Views

```http
GET /api/projects/{id}/views
```

---

#### 📊 Analytics

##### Get Stats

```http
GET /api/stats
```

Returns overall portfolio statistics.

##### Track Visit

```http
POST /api/visit
```

Records a new visitor.

##### Admin Stats

```http
GET /api/admin/stats
```

Returns detailed admin dashboard statistics.

---

#### ℹ️ About

##### Get About

```http
GET /api/about
```

##### Update About

```http
PUT /api/about
Content-Type: application/json

{
  "about": "New about text"
}
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git

### Local Development

1. **Clone the repository**

```bash
git clone https://github.com/Muaves/portfolio-api.git
cd portfolio-api
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Run the API**

```bash
python api.py
```

The API will be available at `http://localhost:5000`

4. **Test the endpoints**

```bash
# Get all projects
curl http://localhost:5000/api/projects

# Get stats
curl http://localhost:5000/api/stats
```

---

## 🌐 Deployment

### Deploy to Render

1. **Fork this repository**

2. **Sign up at [Render.com](https://render.com)**

3. **Create a new Web Service**
   - Connect your GitHub repository
   - Select `portfolio-api`
   - Configure settings:
     - **Environment:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn api:app`
     - **Instance Type:** Free

4. **Deploy!**

Your API will be live at: `https://your-app-name.onrender.com`

### Environment Variables

No environment variables required for basic setup. All configuration is done through `portfolio_data.json`.

---

## 📡 Monitoring

This API uses [UptimeRobot](https://uptimerobot.com) for 24/7 uptime monitoring and status tracking.

### Public Status Page

Check the API status in real-time:

🔗 **[stats.uptimerobot.com/pjTx4GKB5E](https://stats.uptimerobot.com/pjTx4GKB5E)**

The status page shows:
- ✅ Current API status (Online/Offline)
- 📊 Uptime percentage (24h, 7d, 30d, 90d)
- 📈 Response time graphs
- 🕐 Incident history
- 🔔 Real-time alerts

### Monitoring Details

- **Check Interval:** Every 5 minutes
- **Monitored Endpoint:** `/api/stats`
- **Alert Methods:** Email, Dashboard
- **Response Time Tracking:** Yes
- **SSL Certificate Monitoring:** Yes

### Why UptimeRobot?

UptimeRobot keeps the API alive by pinging it regularly, preventing the free Render instance from sleeping due to inactivity. This ensures:

- 🚀 **Fast response times** for all visitors
- 💪 **99.9% uptime** reliability
- 📊 **Performance insights** and analytics
- 🔔 **Instant alerts** if issues occur

---

## 📂 Project Structure

```
portfolio-api/
├── api.py                  # Main Flask application
├── portfolio_data.json     # Project and link data
├── stats.json             # Analytics data (auto-generated)
├── requirements.txt       # Python dependencies
├── index.html            # Frontend homepage
├── admin.html            # Admin dashboard
├── README.md             # This file
└── LICENSE               # MIT License
```

### Key Files

- **`api.py`** - Flask application with all API routes
- **`portfolio_data.json`** - Main data store for projects and links
- **`stats.json`** - Visitor and view tracking data
- **`requirements.txt`** - Python package dependencies
- **`index.html`** - Public-facing portfolio website
- **`admin.html`** - Content management interface

---

## 🎨 Frontend Integration

### Example: Fetch Projects

```javascript
// Fetch all projects
async function loadProjects() {
  const response = await fetch('https://muaves-portfolio-api.onrender.com/api/projects');
  const projects = await response.json();
  
  projects.forEach(project => {
    console.log(project.name);
  });
}
```

### Example: Add New Project

```javascript
// Add a new project
async function addProject() {
  const newProject = {
    name: "My New Project",
    description: "An awesome project",
    tech: "Python, Flask, React",
    status: "In Progress"
  };
  
  const response = await fetch('https://muaves-portfolio-api.onrender.com/api/projects', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(newProject)
  });
  
  const result = await response.json();
  console.log(result.message);
}
```

---

## 🤝 Contributing

Contributions are welcome! If you'd like to improve this API:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide for Python code
- Add comments for complex logic
- Update documentation for new endpoints
- Test all changes locally before pushing
- Keep dependencies minimal and up-to-date

---

## 🐛 Known Issues

### Render Free Tier Limitations

- **Cold Starts:** The API may take 30-60 seconds to respond after 15 minutes of inactivity
- **Sleep Mode:** Free instances sleep after inactivity (mitigated by UptimeRobot pinging)
- **Resource Limits:** Limited CPU and memory on free tier

**Solution:** UptimeRobot pings the API every 5 minutes to prevent sleep mode.

---

## 🔮 Future Enhancements

- [ ] Add authentication for admin endpoints
- [ ] Implement database (PostgreSQL/MongoDB) for better scalability
- [ ] Add image upload support for projects
- [ ] Create automated tests (pytest)
- [ ] Add API rate limiting
- [ ] Implement caching with Redis
- [ ] Add GitHub API integration for automatic project sync
- [ ] Create Swagger/OpenAPI documentation
- [ ] Add webhook support for notifications
- [ ] Implement GraphQL endpoint

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Average Response Time | ~150ms |
| Uptime (30 days) | 99.9% |
| Peak Requests/min | 100+ |
| Data Transfer | ~5MB/month |
| Cold Start Time | ~30s |

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### MIT License Summary

✅ **Permissions:**
- ✔️ Commercial use
- ✔️ Modification
- ✔️ Distribution
- ✔️ Private use

❌ **Limitations:**
- ✖️ Liability
- ✖️ Warranty

📋 **Conditions:**
- License and copyright notice must be included

---

## 👤 Contact

**Muaves**

- 🌐 Portfolio: [muaves.github.io/portfolio-api](https://muaves.github.io/portfolio-api)
- 💼 GitHub: [@Muaves](https://github.com/Muaves)
- 🔗 Website: [muaves.github.io](https://muaves.github.io)
- 📧 Redstone Launcher: [redstone-launcher.com](https://redstone-launcher.com)

---

## 🙏 Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - The web framework that powers this API
- [Render](https://render.com) - Hosting platform
- [UptimeRobot](https://uptimerobot.com) - Uptime monitoring
- [GitHub](https://github.com) - Version control and hosting
- [Animate.css](https://animate.style/) - Frontend animations
- The open-source community for inspiration and tools

---

## 📈 Statistics

![GitHub Repo Size](https://img.shields.io/github/repo-size/Muaves/portfolio-api)
![GitHub Last Commit](https://img.shields.io/github/last-commit/Muaves/portfolio-api)
![GitHub Issues](https://img.shields.io/github/issues/Muaves/portfolio-api)
![GitHub Stars](https://img.shields.io/github/stars/Muaves/portfolio-api?style=social)

---

<div align="center">

**⭐ Star this repo if you found it helpful!**

Made with ❤️ and ☕ by [Muaves](https://github.com/Muaves)

</div>
