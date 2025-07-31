# Brigade Electronics Alarm Heatmap System

**Interactive web-based alarm visualization system for Brigade Electronics vehicle monitoring with real-time data synchronization and multi-select filtering.**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-green.svg)

## 🌟 Features

### 🗺️ Interactive Heatmap
- **Multi-select alarm type filtering** supporting all 168+ alarm codes
- **Clickable alarm datapoints** with detailed modal popups
- **Dual view modes**: Toggle between heatmap and individual markers
- **Advanced filtering**: Date ranges, devices, alarm types, record limits
- **Real-time statistics** and data updates
- **Mobile responsive** design for all device sizes

### 🔄 Data Synchronization
- **Real-time sync** from Brigade Electronics API
- **Automated scheduling**: Devices (10min), Alarms (5min)
- **Duplicate prevention**: Automatic deduplication of alarm records  
- **Error handling**: Comprehensive retry logic and fault tolerance
- **Background processing**: Non-blocking data collection

### 🐳 Production Ready
- **Docker containerization** for easy deployment
- **Health monitoring** with automatic restart
- **Persistent storage** with SQLite database
- **Security hardening** with non-root execution
- **Comprehensive logging** with rotation

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

## 📋 Requirements

- **Python 3.8+**
- **Network access** to Brigade Electronics API server
- **2GB+ RAM** (for Docker deployment)
- **Modern web browser** with JavaScript enabled

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Brigade Electronics API
BRIGADE_API_URL=http://your-api-server:12056
BRIGADE_USERNAME=your_username  
BRIGADE_PASSWORD=your_password

# Sync Settings
UPDATE_INTERVAL_MINUTES=10
ALARM_UPDATE_INTERVAL_MINUTES=5
ALARM_LOOKBACK_MINUTES=10
ALARM_BATCH_SIZE=50
ALARM_CLEANUP_DAYS=30

# Database
DATABASE_PATH=devices.db
LOG_LEVEL=INFO
```

## 🏗️ System Architecture

```
├── 🌐 Web Interface (Flask)
│   ├── Interactive Heatmap (Leaflet.js)
│   ├── REST API Endpoints
│   └── Real-time Statistics
│
├── 🔄 Background Services
│   ├── Device Sync (10min intervals)
│   ├── Alarm Sync (5min intervals)
│   └── Data Cleanup (automated)
│
├── 🗄️ Data Storage
│   ├── SQLite Database
│   ├── Device Information
│   └── Alarm Records (deduplicated)
│
└── 🐳 Docker Container
    ├── Production Ready
    ├── Health Monitoring
    └── Persistent Volumes
```

## 📊 Supported Alarm Types

The system supports all Brigade Electronics alarm codes including:

### 🚨 Emergency Alarms
- **13**: Panic Button
- **37**: SOS
- **85**: Emergency Button

### 👤 Driver Behavior  
- **58**: Driver Fatigue
- **60**: Phone Detection
- **61**: Smoking Detection
- **168**: Using Phone

### 🚗 Vehicle Monitoring
- **24**: Overspeed
- **17**: G-Force  
- **64**: Forward Collision Warning
- **63**: Lane Departure

### ⚙️ System Alerts
- **4**: HDD/SD Error
- **16**: Low Voltage
- **21**: GPS Fail

*...and 160+ additional alarm types covering all monitoring scenarios*

## 🛠️ Management Commands

### Basic Operations
```bash
# Start background sync
python main.py --command start

# Check system status  
python main.py --command status

# Force manual sync
python main.py --command sync

# Start web server
python web_server.py
```

### Docker Operations
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Update system
docker-compose pull && docker-compose up -d
```

## 🔍 API Endpoints

- `GET /` - Interactive heatmap interface
- `GET /api/alarms` - Filtered alarm data  
- `GET /api/alarm/<id>` - Detailed alarm information
- `GET /api/devices` - Device list for filtering
- `GET /api/alarm-types` - Available alarm types
- `GET /api/stats` - System statistics

## 📁 Project Structure

```
├── heatmap/                    # Core application
│   ├── web_server.py          # Flask web server
│   ├── main.py                # Application controller
│   ├── database.py            # Database operations
│   ├── api_client.py          # Brigade API integration
│   ├── templates/             # Web interface
│   └── *.py                   # Service modules
│
├── docker/                    # Docker deployment
│   ├── Dockerfile            # Container definition
│   ├── docker-compose.yml    # Development config
│   ├── docker-compose.prod.yml # Production config  
│   ├── deploy.sh             # Deployment automation
│   └── documentation/        # Deployment guides
│
└── documentation/            # Project documentation
    ├── README.md            # This file
    ├── DEPLOYMENT.md        # Deployment guide
    └── API.md              # API documentation
```

## 🧪 Testing

```bash
# Test API connection
python test_api_connection.py

# Test complete functionality  
python test_complete_heatmap.py

# Test Docker build
python test-docker.py

# Run all tests
python -m pytest tests/
```

## 🔒 Security Features

- **Non-root container execution**
- **Environment variable secrets**
- **Input validation** and SQL injection prevention
- **CORS configuration** for web security
- **Health monitoring** with automatic restart
- **Database constraints** preventing data corruption

## 📈 Performance

### Resource Requirements
- **Minimum**: 1 CPU, 512MB RAM, 1GB disk
- **Recommended**: 2 CPU, 1GB RAM, 5GB disk  
- **Heavy Load**: 4 CPU, 2GB RAM, 10GB disk

### Optimization Features
- **Database indexing** for fast queries
- **Connection pooling** for API efficiency
- **Batch processing** for alarm collection
- **Automatic cleanup** of old records
- **Caching** for frequently accessed data

## 🐛 Troubleshooting

### Common Issues

**API Connection Failed:**
```bash
# Test connection
python test_api_connection.py

# Check configuration
cat .env

# Verify network access
curl http://your-api-server:12056/api/v1/basic/key
```

**Database Issues:**
```bash
# Reset database
rm devices.db
python main.py --command sync

# Check database
python -c "from database import DatabaseManager; db = DatabaseManager(); print(f'Devices: {db.get_device_count()}')"
```

**Docker Problems:**
```bash
# Check container logs
docker-compose logs -f

# Rebuild containers
docker-compose up -d --build

# Check resources
docker stats
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Brigade Electronics** for API access and documentation
- **Leaflet.js** for interactive mapping capabilities
- **Flask** framework for web server functionality
- **Docker** for containerization platform

---

## 🎯 Key Achievements

✅ **Complete Implementation**: All requested features implemented and tested  
✅ **Multi-Select Filtering**: Support for complex alarm type combinations  
✅ **Interactive Experience**: Clickable datapoints with detailed modals  
✅ **Production Ready**: Docker deployment with monitoring and security  
✅ **Duplicate Prevention**: Automatic deduplication of alarm records  
✅ **Mobile Responsive**: Works on all device sizes  
✅ **Real-Time Data**: Live updates and comprehensive statistics  

**The Brigade Electronics Alarm Heatmap System provides complete vehicle monitoring visualization with enterprise-grade reliability and performance.** 🚀