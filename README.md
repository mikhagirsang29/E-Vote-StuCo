# 🏆 Student Council E-Voting Portal (VoteStuCo)

A modern, real-time, and secure LAN E-Voting web application built for student council elections. Powered by **FastAPI**, **HTMX**, **Postgresql / SQLite (WAL Mode)**, and **WebSockets** for instant live election result broadcasting without requiring browser page refreshes.

## 💻 DEMO
you can try the WebApp here :
https://e-vote-stuco.onrender.com

default admin user is
username : admin
password : password
---

## ✨ Features

* **⚡ Instant Live Results:** Real-time WebSocket broadcasting that updates the results charts across all connected screens the millisecond a ballot is cast.
* **🛡️ Bulletproof Confirmations:** Intercepted HTMX confirmation modals matching the UI theme to prevent accidental votes.
* **🎨 Modern UI:** Glassmorphism and responsive cards built with Tailwind CSS.
* **🌐 LAN-Optimized:** Zero external dependencies on runtime; everything runs 100% locally over a school Wi-Fi or wired network.

---

## 📋 Prerequisites

Before running the application, make sure you have the following installed on your host machine:
* [Git](https://git-scm.com/)
* [Docker & Docker Compose](https://www.docker.com/) *(for production/LAN deployment)*
* [Python 3.10+](https://www.python.org/) *(for local development)*

---

## 🚀 Option 1: Running with Docker Compose (Recommended for Elections)

This setup is ideal for election day on your school LAN. It includes volume mappings so that your database and uploaded images survive container restarts, crashes, or system reboots.

### 1. Clone the Repository
```bash
git clone https://github.com/mikhagirsang29/E-Vote-StuCo.git
cd E-Vote-StuCo
```

### 2. Prepare Data Directories
To prevent SQLite WAL mode locking errors and ensure data persistence, create the required local folders before starting Docker:
```bash
mkdir -p data static/uploads
```

### 3. Build and Start the Container
Run Docker Compose in detached mode (-d):
```bash
docker compose up -d --build
```
NOTE : the default admin username is `admin` and the password is `password`, you can change the admin password in the admin page

## 💻 Option 2: Local Development Setup (Python & Uvicorn)

If you are developing new features, modifying UI components, or debugging locally without Docker, use Uvicorn's hot-reload feature.

### 1. Clone and Navigate to the Project
```bash
git clone https://github.com/mikhagirsang29/E-Vote-StuCo.git
cd E-Vote-StuCo
```

### 2. Create a Virtual Environment
It is recommended to use a virtual environment to avoid conflicts with global Python packages:
```bash
# On Linux/macOS
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
Install all required libraries, including Uvicorn with standard WebSocket support:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create the Data Folder
Ensure the local data folder exists for SQLite:
```bash
mkdir -p data static/uploads
```

### 5. Run the Server with Hot-Reload
Start the Uvicorn development server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
NOTE : change the port to your need
- The --reload flag tells Uvicorn to automatically restart the server whenever you save changes to your .py, .html, or .js files.
- The --host 0.0.0.0 flag makes the development server accessible to other devices connected to your local Wi-Fi/LAN network.
- the default admin username is `admin` and the password is `password`, you can change the admin password in the admin page

---

## 🧪 Testing the Application
Once your server is running (either via Docker or Uvicorn), open your web browser and test the endpoints:
| Page / Feature | URL | Description |
| :--- | :--- | :--- |
| **Voter Dashboard** | `http://localhost:8000/` | The main voting portal where students cast their ballots. |
| **Admin Panel** | `http://localhost:8000/admin` | Manage candidates, students, and toggle the election state (`SETUP`, `OPEN`, `CLOSED`). |
| **Live Results Feed (Admin Only when election is `OPEN`)** | `http://localhost:8000/results` | Watch live WebSocket bar charts update instantly when an election is `OPEN`, or view the trophy tally when `CLOSED`. |

---

## 🗂️ Project Structure
```plaintext
voteStuco/
├── data/                  # Persistent SQLite database folder (voting.db resides here)
├── routes/                # Isolated FastAPI route modules (admin.py, client.py)
├── static/                # Static assets (Tailwind CSS, HTMX, custom scripts, uploads)
├── templates/             # Jinja2 HTML templates & HTMX fragments
├── Dockerfile             # Container instructions (Python 3.14-slim base)
├── docker-compose.yaml    # Container orchestration & persistent volume mappings
├── database.py            # SQLAlchemy database setup & SQLite WAL mode pragma
├── main.py                # FastAPI application entrypoint & WebSocket routes
├── ws_manager.py          # Shared WebSocket connection manager
└── requirements.txt       # Python dependency list
```

---

## 🤝 Contributing
Contributions are always welcome! Please follow these steps:
1. Fork the project repository.
2. Create a new feature branch (git checkout -b feature/AmazingFeature).
3. Commit your changes (git commit -m 'Add some AmazingFeature').
4. Push to the branch (git push origin feature/AmazingFeature).
5. Open a Pull Request.

## 📄 License
This project is licensed under the GPL-3.0 license
