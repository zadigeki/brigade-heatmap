# Brigade Electronics Monitoring System

A comprehensive monitoring solution for Brigade Electronics devices featuring alarm heatmaps and real-time GPS tracking.

## Features

### 🔥 Alarm Heatmap
- Visual heatmap of vehicle alarm incidents
- Time-based filtering (24h, 48h, week, custom)
- Device and alarm type filtering
- Real-time statistics and analytics
- Interactive map with alarm details

### 📍 GPS Tracking
- Real-time vehicle location monitoring
- Speed and status indicators
- Address lookup via OpenStreetMap
- Auto-refresh every 30 seconds
- Vehicle search and filtering

### 🔄 Automated Services
- Device synchronization from Brigade API
- GPS position updates every 30 seconds
- Alarm data synchronization every 5 minutes
- Automatic database management

## Quick Start

### Option 1: Use the Start Scripts (Recommended)

**Windows:**
```cmd
# Double-click or run from command prompt
start_system.bat
```

**Linux/Mac:**
```bash
# Make executable and run
chmod +x start_system.sh
./start_system.sh
```

### Option 2: Manual Start

```bash
# Start the complete system
python run_system.py

# Or with custom options
python run_system.py --host 0.0.0.0 --port 8080 --gps-interval 60
```

## Accessing the System

Once started, the system will be available at:

- **Main Interface**: http://localhost:5000
- **Alarm Heatmap**: http://localhost:5000/
- **GPS Tracking**: http://localhost:5000/gps-tracking
- **API Endpoints**: http://localhost:5000/api/

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Brigade Electronics API                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Data Services                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │Device Sync  │ │ GPS Tracking│ │    Alarm Sync           ││
│  │(Hourly)     │ │(30 seconds) │ │  (5 minutes)            ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                SQLite Database                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │   devices   │ │     gps     │ │       alarms            ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Web Server (Flask)                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │    HTML     │ │    API      │ │     Static Files        ││
│  │  Templates  │ │ Endpoints   │ │                         ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Web Browser                                  │
│  ┌─────────────┐ ┌─────────────┐                           │
│  │  Heatmap    │ │GPS Tracking │                           │
│  │   Page      │ │    Page     │                           │
│  └─────────────┘ └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### API Configuration

Update `config.py` with your Brigade API settings:

```python
API_CONFIG = {
    'base_url': 'http://your-brigade-server:12056',
    'username': 'your-username',
    'password': 'your-password',
    'timeout': 30,
    'retry_attempts': 3,
    'retry_delay': 1
}
```

### Database Configuration

The system uses SQLite by default. The database is automatically created in the `heatmap` directory.

## Command Line Options

```bash
python run_system.py --help

Options:
  --host HOST              Host to bind web server to (default: 127.0.0.1)
  --port PORT              Port for web server (default: 5000)
  --gps-interval SECONDS   GPS update interval (default: 30)
  --debug                  Enable debug mode
  --log-level LEVEL        Set logging level (DEBUG/INFO/WARNING/ERROR)
```

## API Endpoints

### Device Information
- `GET /api/devices` - List all devices
- `GET /api/device-groups` - List device groups

### Alarm Data
- `GET /api/alarms` - Get alarm data for heatmap
- `GET /api/alarm/<id>` - Get specific alarm details
- `GET /api/alarm-types` - Get available alarm types
- `GET /api/stats` - Get system statistics

### GPS Data
- `GET /api/gps/positions` - Get all current GPS positions
- `GET /api/gps/position/<terid>` - Get position for specific device

## Navigation

The system includes a unified navigation bar that allows easy switching between:

- **Alarm Heatmap**: Visual representation of alarm incidents
- **GPS Tracking**: Real-time vehicle location monitoring
- **API Access**: Direct access to API endpoints

## Status Indicators

### GPS Tracking Status
- 🟢 **Green**: Vehicle is moving (speed > 5 km/h)
- 🔴 **Red**: Vehicle is stopped (speed ≤ 5 km/h)
- ⚫ **Gray**: Vehicle is offline (no update for > 30 minutes)

### System Status
- The footer shows real-time system status including API connection and database health
- Auto-updates to show last refresh time

## Troubleshooting

### System Won't Start
1. Check that all required Python packages are installed: `pip install -r requirements.txt`
2. Verify API configuration in `config.py`
3. Check that the port is not already in use
4. Review logs for detailed error messages

### No Data Appearing
1. Verify Brigade API credentials and connectivity
2. Check that devices exist in the Brigade system
3. Ensure GPS data is being received from devices
4. Check database for stored data: Look for `devices.db` file

### JavaScript Errors in Browser
1. The system now uses a simplified alarm type filter that doesn't require external libraries
2. If you see "alarmTypeMultiSelect.getSelectedValues is not a function" errors, clear your browser cache
3. The new system uses standard HTML select elements with multiple selection (Hold Ctrl to select multiple items)

### Performance Issues
1. Reduce GPS update interval: `--gps-interval 60`
2. Limit alarm data range in heatmap filters
3. Check system resources (CPU, memory)

### Network Access Issues
1. Use `--host 0.0.0.0` to bind to all network interfaces
2. Check firewall settings for the web port
3. Ensure Brigade API server is accessible from the monitoring system

## Security Considerations

- The system binds to localhost by default for security
- Use `--host 0.0.0.0` only in trusted network environments
- Ensure Brigade API credentials are kept secure
- Consider using HTTPS in production deployments

## Support

For issues and support:
1. Check the logs for detailed error messages
2. Verify Brigade API connectivity with `test_api_connection.py`
3. Test individual components separately if needed