"""
Web server for Brigade Electronics Alarm Heatmap
"""
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from database import DatabaseManager

logger = logging.getLogger(__name__)

class AlarmHeatmapServer:
    """Web server for alarm heatmap visualization"""
    
    def __init__(self, host='127.0.0.1', port=5000, debug=False):
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='static')
        CORS(self.app)
        
        self.host = host
        self.port = port
        self.debug = debug
        self.db_manager = DatabaseManager()
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main heatmap page"""
            return render_template('heatmap.html')
        
        @self.app.route('/api/alarms')
        def get_alarms():
            """Get alarm data for heatmap"""
            try:
                # Get query parameters
                hours = request.args.get('hours', default=24, type=int)
                limit = request.args.get('limit', default=1000, type=int)
                start_date = request.args.get('start_date')
                end_date = request.args.get('end_date')
                alarm_types = request.args.get('alarm_types')
                device_id = request.args.get('device_id')
                
                # Build alarm data query
                alarms = self._get_alarm_data(
                    hours=hours,
                    limit=limit,
                    start_date=start_date,
                    end_date=end_date,
                    alarm_types=alarm_types,
                    device_id=device_id
                )
                
                # Convert to heatmap format
                heatmap_data = self._convert_to_heatmap_format(alarms)
                
                return jsonify({
                    'success': True,
                    'data': heatmap_data,
                    'count': len(alarms),
                    'query_params': {
                        'hours': hours,
                        'limit': limit,
                        'start_date': start_date,
                        'end_date': end_date,
                        'alarm_types': alarm_types,
                        'device_id': device_id
                    }
                })
                
            except Exception as e:
                logger.error(f"Error fetching alarm data: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/alarm/<int:alarm_id>')
        def get_alarm_detail(alarm_id):
            """Get detailed information for a specific alarm"""
            try:
                alarm = self.db_manager.get_alarm_by_id(alarm_id)
                if not alarm:
                    return jsonify({
                        'success': False,
                        'error': 'Alarm not found'
                    }), 404
                
                # Get device information
                device = self.db_manager.get_device_by_terid(alarm['terid'])
                
                return jsonify({
                    'success': True,
                    'alarm': alarm,
                    'device': device
                })
                
            except Exception as e:
                logger.error(f"Error fetching alarm detail: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/devices')
        def get_devices():
            """Get list of all devices for filtering"""
            try:
                devices = self.db_manager.get_all_devices()
                device_list = [
                    {
                        'terid': device['terid'],
                        'car_license': device['car_license'],
                        'company_name': device.get('company_name', '')
                    }
                    for device in devices
                ]
                
                return jsonify({
                    'success': True,
                    'devices': device_list
                })
                
            except Exception as e:
                logger.error(f"Error fetching devices: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/alarm-types')
        def get_alarm_types():
            """Get distinct alarm types for filtering"""
            try:
                alarm_types = self.db_manager.get_distinct_alarm_types()
                return jsonify({
                    'success': True,
                    'alarm_types': alarm_types
                })
                
            except Exception as e:
                logger.error(f"Error fetching alarm types: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/stats')
        def get_stats():
            """Get alarm statistics"""
            try:
                stats = self._get_alarm_stats()
                return jsonify({
                    'success': True,
                    'stats': stats
                })
                
            except Exception as e:
                logger.error(f"Error fetching stats: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
    
    def _get_alarm_data(self, hours: int = 24, limit: int = 1000, 
                       start_date: Optional[str] = None, end_date: Optional[str] = None,
                       alarm_types: Optional[str] = None, device_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get alarm data with filtering"""
        
        if start_date and end_date:
            # Use custom date range
            return self.db_manager.get_alarms_by_date_range(
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                alarm_types=[int(t.strip()) for t in alarm_types.split(',')] if alarm_types else None,
                device_id=device_id
            )
        else:
            # Use hours parameter with filtering
            from datetime import datetime, timedelta
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            return self.db_manager.get_alarms_by_date_range(
                start_date=start_time.strftime('%Y-%m-%d %H:%M:%S'),
                end_date=end_time.strftime('%Y-%m-%d %H:%M:%S'),
                limit=limit,
                alarm_types=[int(t.strip()) for t in alarm_types.split(',')] if alarm_types else None,
                device_id=device_id
            )
    
    def _convert_to_heatmap_format(self, alarms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert alarm data to heatmap format"""
        heatmap_data = []
        
        for alarm in alarms:
            # Skip alarms without valid GPS coordinates
            if not alarm.get('gps_lat') or not alarm.get('gps_lng'):
                continue
            
            try:
                lat = float(alarm['gps_lat'])
                lng = float(alarm['gps_lng'])
                
                # Skip invalid coordinates
                if lat == 0 and lng == 0:
                    continue
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    continue
                
                heatmap_point = {
                    'id': alarm['id'],
                    'lat': lat,
                    'lng': lng,
                    'intensity': self._get_alarm_intensity(alarm['alarm_type']),
                    'terid': alarm['terid'],
                    'alarm_type': alarm['alarm_type'],
                    'alarm_content': alarm.get('alarm_content', ''),
                    'gps_time': alarm.get('gps_time', ''),
                    'speed': alarm.get('speed', 0),
                    'altitude': alarm.get('altitude', 0),
                    'direction': alarm.get('direction', 0)
                }
                
                heatmap_data.append(heatmap_point)
                
            except (ValueError, TypeError) as e:
                logger.debug(f"Skipping alarm with invalid coordinates: {e}")
                continue
        
        return heatmap_data
    
    def _get_alarm_intensity(self, alarm_type: int) -> float:
        """Get intensity value for alarm type (for heatmap visualization)"""
        # Map alarm types to intensity values (0.1 to 1.0)
        intensity_map = {
            1: 0.3,   # Video Loss
            2: 0.2,   # Motion Detection
            3: 0.2,   # Blind Detection
            4: 0.4,   # HDD/SD Error
            5: 0.5,   # IO 1
            6: 0.5,   # IO 2
            13: 1.0,  # Panic Button
            14: 0.6,  # Low Speed
            15: 0.8,  # High Speed
            16: 0.7,  # Low Voltage
            17: 0.9,  # G-Force
            18: 0.6,  # Geo-Fence
            19: 0.8,  # Unauthorised Ignition
            29: 0.7,  # Temperature Alarm
            36: 0.9,  # Impact Alarm
            58: 0.8,  # Driver Fatigue
            59: 0.9,  # No Driver
            60: 0.4,  # Phone Detection
            61: 0.4,  # Smoking Detection
            62: 0.6,  # Driver Distraction
            63: 0.7,  # Lane Departure
            64: 0.8,  # Forward Collision Warning
        }
        
        return intensity_map.get(alarm_type, 0.5)  # Default intensity
    
    def _get_alarm_stats(self) -> Dict[str, Any]:
        """Get alarm statistics"""
        try:
            total_alarms = self.db_manager.get_alarm_count()
            total_devices = self.db_manager.get_device_count()
            
            # Get recent alarm counts by type
            recent_alarms = self.db_manager.get_recent_alarms(hours=24, limit=10000)
            alarm_type_counts = {}
            
            for alarm in recent_alarms:
                alarm_type = alarm.get('alarm_type', 0)
                alarm_type_counts[alarm_type] = alarm_type_counts.get(alarm_type, 0) + 1
            
            # Get device with most alarms
            device_alarm_counts = {}
            for alarm in recent_alarms:
                terid = alarm.get('terid')
                if terid:
                    device_alarm_counts[terid] = device_alarm_counts.get(terid, 0) + 1
            
            most_active_device = max(device_alarm_counts.items(), key=lambda x: x[1]) if device_alarm_counts else None
            
            return {
                'total_alarms': total_alarms,
                'total_devices': total_devices,
                'recent_alarms_24h': len(recent_alarms),
                'alarm_type_counts': alarm_type_counts,
                'most_active_device': {
                    'terid': most_active_device[0],
                    'alarm_count': most_active_device[1]
                } if most_active_device else None,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating alarm stats: {e}")
            return {}
    
    def run(self):
        """Start the web server"""
        logger.info(f"Starting Alarm Heatmap Server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=self.debug)

def main():
    """Run the web server"""
    import argparse
    from logging_config import setup_logging
    
    parser = argparse.ArgumentParser(description="Brigade Electronics Alarm Heatmap Server")
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Set logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Create and run server
    server = AlarmHeatmapServer(host=args.host, port=args.port, debug=args.debug)
    server.run()

if __name__ == "__main__":
    main()