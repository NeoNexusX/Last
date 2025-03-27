- # Last

  [English](README.md) | [简体中文](README.zh-CN.md)

  ## Project Introduction

  A server monitoring and management tool built with FastAPI, designed to remotely monitor and manage small-to-medium-scale Linux **[supported]**, macOS **[to be supported]**, and Windows **[possibly supported, contributions welcome]** servers via SSH. It provides comprehensive hardware monitoring and account management features.

  ## ✨ Core Features

  ### 🖥️ **Server Monitoring**

  - **CPU**: Usage, core count, load status
  - **Memory**: Real-time usage, cache, swap space
  - **Disk**: Storage space, read/write speed, mount points
  - **GPU** (NVIDIA-only for now, no other devices): VRAM usage, temperature, utilization

  ### 🔐 **Security Management**

  - **SSH Key Management**
  - **Login Audit Logs**
  - **Server Account Management**
  - **Password Modification** (supports `passwd`)
  - **One-Click Unified Account Password** **[In Development]**
  - **Batch Server Account Deactivation** **[In Development]**
  - **Custom Command Batch Account Registration** **[In Development]**
  - **Encrypted Database Protection** **[In Development]**

  ### ⚙️ **Operations Tools**

  - **Service Status Check** (`systemd`/`service`)
  - **Log File Viewer** (integrated `tail`/`grep`) **[In Development]**
  - **Batch Command Execution** (supports `sudo`) **[In Development]**

  ### 📊 **Data Visualization**

  - See the frontend project：
  
  BioSerWeb https://github.com/NeoNexusX/BioSerWeb 
  
- **RESTful API** Data Interface
  
  ## Tech Stack 🛠️
  
  |     Category      |  Technology Stack   |
  | :---------------: | :-----------------: |
  | Backend Framework |       FastAPI       |
  |     Database      |  SQLite (SQLModel)  |
  |  SSH Connection   |   Paramiko/Fabric   |
|    Data Models    | Pydantic + SQLModel |
  |   Async Support   | Python async/await  |
|  Logging System   |   Python logging    |
  
## Quick Start 🚀
  
1. **Install Dependencies**
  
     ```bash
     pip install -r requirements.txt  
   ```
     
  2. **Configure Environment**
   Copy `.env.example` to `.env` and fill in your server details.
  
3. **Start the Service**
  
   ```bash
     uvicorn main:app --reload  
     ```
     
4. **Access API Documentation**
     Open `http://localhost:8000/docs` in your browser.
  
### Directory Structure
  
```bash
  # Project Root Directory  
├── LICENSE           # Open-source license file (e.g., MIT/GPL)  
  ├── README.md         # Project documentation  
  ├── api/              # API interface module  
  │   ├── __init__.py   # Python package initialization  
  │   ├── auth_api.py   # Authentication APIs (token-based auth, etc.)  
  │   ├── serverapi.py  # Server management APIs  
  │   └── userapi.py    # User management APIs (includes login/logout)  
  ├── database/         # Database-related files  
  │   ├── bionet.db     # SQLite database file (auto-created here)  
  │   └── db.py         # Database connection and operations  
  ├── logger.py         # Logging system configuration  
  ├── logs/             # Log storage directory  
  │   ├── app.log       # Application runtime logs  
  │   └── error.log     # Error logs  
  ├── main.py           # Program entry point  
  ├── models/           # Data models  
  │   ├── __init__.py  
  │   ├── auth.py       # Authentication models  
  │   ├── server_models.py  # Server data models  
  │   └── user_models.py    # User data models  
  ├── requirements.txt  # Python dependencies list  
  └── ssh/              # SSH functionality module  
      ├── __init__.py  
      └── ssh_manager.py  # SSH connection pool management  
  ```
  
  ## 🌟 Use Case Examples
  
- **IT Operations Teams**: Centralized monitoring of all development servers in small-to-medium enterprises.
  - **Researchers**: Real-time tracking of computing resource usage on small-to-medium-scale GPU servers for scientific research.
- **Individual Developers**: Managing multiple VPS and cloud instances.
  
  ## 🤝 Contribution Guidelines
  
### How to Contribute?
  
1. **Report Issues**: Submit detailed bug reports.
  2. **Develop Features**: Claim `Good First Issue` tasks.
3. **Improve Documentation**: Enhance README or contribute translations.
  
  ### Code Requirements
  
- Complies with **GPL-3.0** copyleft terms.
  - Passes `pre-commit` checks.
- Includes unit tests (`pytest`) **[To Be Supported]** (not required for now).
  
  ## 📜 License
  
**GNU General Public License v3.0 (GPL-3.0)**
  
- ✅ Allows free use, modification, and distribution.
  - ✅ Requires open-source derivative works.
- ❌ Prohibits closed-source commercialization.
