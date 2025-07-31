# Brigade Electronics Alarm Heatmap System

**Interactive web-based alarm visualization system for Brigade Electronics vehicle monitoring with real-time data synchronization and multi-select filtering.**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-green.svg)

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)
```bash
# Clone repository
git clone https://github.com/yourusername/brigade-heatmap.git
cd brigade-heatmap/docker

# Configure environment
cp .env.example .env
nano .env  # Add your API credentials

# Deploy with one command
./deploy.sh
```

**Access:** http://localhost:5000

### Option 2: Manual Installation
```bash
# Clone and setup
git clone https://github.com/yourusername/brigade-heatmap.git
cd brigade-heatmap/heatmap

# Install dependencies
pip install -r requirements.txt

# Configure API settings
cp .env.example .env
nano .env  # Add your API credentials

# Initialize database
python main.py --command sync

# Start services
python main.py --command start &  # Background sync
python web_server.py              # Web interface
```

## 🌟 Key Features

- **Interactive Heatmap** with multi-select alarm type filtering (168+ alarm codes)
- **Clickable alarm datapoints** with detailed modal popups
- **Real-time synchronization** from Brigade Electronics API
- **Docker containerization** for easy deployment
- **Duplicate prevention** of alarm records
- **Mobile responsive** design

## 📁 Project Structure

```
├── heatmap/                    # Core application
│   ├── web_server.py          # Flask web server
│   ├── main.py                # Application controller
│   ├── database.py            # Database operations
│   └── templates/             # Web interface
│
├── docker/                    # Docker deployment
│   ├── Dockerfile            # Container definition
│   ├── docker-compose.yml    # Development config
│   └── deploy.sh             # Deployment automation
│
└── PROJECT_README.md         # Detailed documentation
```

## 📋 Requirements

- **Python 3.8+**
- **Network access** to Brigade Electronics API server
- **Modern web browser** with JavaScript enabled

## 🔧 Configuration

Create `.env` file based on `.env.example`:

```bash
# Brigade Electronics API
BRIGADE_API_URL=http://your-api-server:12056
BRIGADE_USERNAME=your_username  
BRIGADE_PASSWORD=your_password

# Sync Settings
UPDATE_INTERVAL_MINUTES=10
ALARM_UPDATE_INTERVAL_MINUTES=5
```

## 📖 Documentation

For complete documentation including system architecture, API endpoints, troubleshooting, and deployment guides, see [PROJECT_README.md](PROJECT_README.md).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**The Brigade Electronics Alarm Heatmap System provides complete vehicle monitoring visualization with enterprise-grade reliability and performance.** 🚀