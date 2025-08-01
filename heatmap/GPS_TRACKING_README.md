# Brigade GPS Tracking System

This GPS tracking system provides real-time vehicle location monitoring for Brigade Electronics devices.

## Features

- **Live Vehicle Tracking**: View real-time positions of all vehicles on an interactive map
- **Speed Monitoring**: See current speed displayed on vehicle icons
- **Vehicle Status**: Visual indicators for moving, stopped, and offline vehicles
- **Address Lookup**: Click on vehicles to see their current address using OpenStreetMap reverse geocoding
- **Auto-Refresh**: Map updates automatically every 30 seconds
- **Search & Filter**: Quickly find vehicles by license plate or device ID
- **Responsive Design**: Works on desktop and mobile devices

## Setup Instructions

### 1. Database Setup

The GPS tracking system uses the existing SQLite database with a new `gps` table. The schema is automatically created when the application starts.

### 2. Running the GPS Tracking Service

Start the GPS data synchronization service:

```bash
# Run once to test
python gps_tracking_service.py --once

# Run continuously (updates every 30 seconds)
python gps_tracking_service.py

# Custom update interval (e.g., 60 seconds)
python gps_tracking_service.py --interval 60
```

### 3. Starting the Web Server

```bash
python web_server.py
```

The web server runs on http://localhost:5000 by default.

### 4. Accessing the GPS Tracking Page

Open your browser and navigate to:
- GPS Tracking: http://localhost:5000/gps-tracking
- Alarm Heatmap: http://localhost:5000/

## API Endpoints

The system provides the following API endpoints:

- `GET /api/gps/positions` - Get all current vehicle positions
- `GET /api/gps/position/<terid>` - Get position for a specific vehicle

## System Architecture

```
Brigade API
    ↓
GPS Tracking Service (gps_tracking_service.py)
    ↓
SQLite Database (gps table)
    ↓
Web Server (web_server.py)
    ↓
Frontend (gps_tracking.html)
```

## Vehicle Status Indicators

- **Green**: Vehicle is moving (speed > 5 km/h)
- **Red**: Vehicle is stopped (speed ≤ 5 km/h)
- **Gray**: Vehicle is offline (no update for > 30 minutes)

## Troubleshooting

### No vehicles appearing on map
1. Check if the GPS tracking service is running
2. Verify API credentials in config.py
3. Check logs for any errors

### Address not loading
- OpenStreetMap Nominatim has rate limits. If too many requests are made, addresses may not load temporarily.

### Database errors
- Ensure the database file has write permissions
- Check that the gps table exists in the database

## Technical Details

- Uses Leaflet.js for interactive mapping
- OpenStreetMap tiles for map display
- OpenStreetMap Nominatim for reverse geocoding
- SQLite for data storage
- Flask for web server
- Updates GPS data from Brigade API every 30 seconds