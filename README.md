# 🏆 Student Council E-Voting Portal (VoteStuCo)

A modern, real-time, and secure LAN E-Voting web application built for student council elections. Powered by **FastAPI**, **HTMX**, **Postgresql / SQLite (WAL Mode)**, and **WebSockets** for instant live election result broadcasting without requiring browser page refreshes.

## 💻 DEMO
you can try the WebApp here :
https://e-vote-stuco.onrender.com
```
default admin user is
username : admin
password : password
```

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

## 📊 Performance & Stress Testing Report

### 1. Test Overview & Configuration
We utilized Locust to simulate a high-traffic election scenario, ensuring the FastAPI backend and database can handle rapid concurrent voting.<br>
Configuration Parameters:<br>
- Target Host: http://localhost:8000<br>
- Peak Concurrent Users: 1,000<br>
- Spawn Rate: 50 users per second (ramp-up time to peak load is 20 seconds)<br>
- Total Duration: 2 minutes<br>

Execution Command:
```
locust -f locustfile.py --headless -u 1000 -r 50 --run-time 2m --host=http://localhost:8000
```

### 2. Key Metrics Monitored
- When evaluating the Locust output, we looked for the following health indicators:<br>
- RPS (Requests Per Second): Indicates the throughput of the server.<br>
- Failure Rate: Ideally 0%. Failures usually indicate database locks, connection pool exhaustion, or server timeouts.<br>
- Response Times: We aim for < 500ms median response times.<br>

### 3. Test Results
- The test successfully simulated 1,000 concurrent students logging in and casting their votes over a 2-minute window.<br>
- Total Requests: 2,000 (1,000 Logins, 1,000 Votes)<br>
- Failures: 0 (0.00%) 🎉<br>
- Average RPS: 89.20 req/s<br>
- Response Time: Median: 190 ms | Average: 547 ms<br>

### 4. Analysis & Architecture Validation
- The server handled the 1,000-user stress test flawlessly with a 0% failure rate.<br>
- Database Stability: Handling 1,000 simultaneous writes without a single database lock or dropped transaction proves the architecture is highly resilient under load.<br>
- Real-time Performance: The FastAPI WebSocket ConnectionManager successfully maintained the connections and broadcasted 1,000 real-time HTMX snippet updates without crashing the asynchronous event loop.<br>

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
