"""
Database operations for device management
"""
import sqlite3
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager
from config import DATABASE_CONFIG

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database operations for devices"""
    
    def __init__(self):
        self.db_path = DATABASE_CONFIG.db_path
        self.connection_timeout = DATABASE_CONFIG.connection_timeout
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the database with schema"""
        try:
            with self._get_connection() as conn:
                # Read and execute schema
                with open('database_schema.sql', 'r') as f:
                    schema = f.read()
                conn.executescript(schema)
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path, 
                timeout=self.connection_timeout,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _normalize_device_data(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize device data field names from API to database schema
        """
        normalized = {
            'carlicense': device_data.get('carlicence') or device_data.get('carlicense') or 'Unknown',
            'terid': device_data.get('terid') or device_data.get('deviceid'),
            'sim': device_data.get('sim') or 'Unknown',
            'channel': device_data.get('channel') or device_data.get('channelcount') or 0,
            'platecolor': device_data.get('platecolor') or 0,
            'groupid': device_data.get('groupid') or 0,
            'cname': device_data.get('cname') or '',
            'devicetype': device_data.get('devicetype') or '0',
            'linktype': device_data.get('linktype') or '0',
            'deviceusername': device_data.get('deviceusername') or '',
            'devicepassword': device_data.get('devicepassword') or '',
            'registerip': device_data.get('registerip') or '',
            'registerport': device_data.get('registerport') or 0,
            'transmitip': device_data.get('transmitip') or '',
            'transmitport': device_data.get('transmitport') or 0,
            'en': device_data.get('en') or 0,
            'companybranch': device_data.get('companybranch') or '',
            'companyname': device_data.get('companyname') or ''
        }
        return normalized

    def upsert_device(self, device_data: Dict[str, Any]) -> bool:
        """
        Insert or update a device record
        Returns True if successful, False otherwise
        """
        try:
            # Normalize the device data
            normalized_data = self._normalize_device_data(device_data)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if device exists
                cursor.execute("SELECT id FROM devices WHERE terid = ?", (normalized_data.get('terid'),))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing record
                    update_sql = """
                    UPDATE devices SET 
                        car_license = ?, sim = ?, channel = ?, plate_color = ?,
                        group_id = ?, cname = ?, device_type = ?, link_type = ?,
                        device_username = ?, device_password = ?, register_ip = ?,
                        register_port = ?, transmit_ip = ?, transmit_port = ?,
                        channel_enable = ?, company_branch = ?, company_name = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE terid = ?
                    """
                    values = (
                        normalized_data.get('carlicense'),
                        normalized_data.get('sim'),
                        normalized_data.get('channel'),
                        normalized_data.get('platecolor'),
                        normalized_data.get('groupid'),
                        normalized_data.get('cname'),
                        normalized_data.get('devicetype'),
                        normalized_data.get('linktype'),
                        normalized_data.get('deviceusername'),
                        normalized_data.get('devicepassword'),
                        normalized_data.get('registerip'),
                        normalized_data.get('registerport'),
                        normalized_data.get('transmitip'),
                        normalized_data.get('transmitport'),
                        normalized_data.get('en'),
                        normalized_data.get('companybranch'),
                        normalized_data.get('companyname'),
                        normalized_data.get('terid')
                    )
                    cursor.execute(update_sql, values)
                    logger.debug(f"Updated device {device_data.get('terid')}")
                else:
                    # Insert new record
                    insert_sql = """
                    INSERT INTO devices (
                        car_license, terid, sim, channel, plate_color, group_id,
                        cname, device_type, link_type, device_username,
                        device_password, register_ip, register_port, transmit_ip,
                        transmit_port, channel_enable, company_branch, company_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    values = (
                        normalized_data.get('carlicense'),
                        normalized_data.get('terid'),
                        normalized_data.get('sim'),
                        normalized_data.get('channel'),
                        normalized_data.get('platecolor'),
                        normalized_data.get('groupid'),
                        normalized_data.get('cname'),
                        normalized_data.get('devicetype'),
                        normalized_data.get('linktype'),
                        normalized_data.get('deviceusername'),
                        normalized_data.get('devicepassword'),
                        normalized_data.get('registerip'),
                        normalized_data.get('registerport'),
                        normalized_data.get('transmitip'),
                        normalized_data.get('transmitport'),
                        normalized_data.get('en'),
                        normalized_data.get('companybranch'),
                        normalized_data.get('companyname')
                    )
                    cursor.execute(insert_sql, values)
                    logger.debug(f"Inserted new device {device_data.get('terid')}")
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to upsert device {device_data.get('terid', 'unknown')}: {e}")
            return False
    
    def upsert_devices_batch(self, devices: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Batch upsert multiple devices
        Returns dict with counts of inserted/updated/failed records
        """
        results = {'inserted': 0, 'updated': 0, 'failed': 0}
        
        for device in devices:
            try:
                # Normalize the device data
                normalized_device = self._normalize_device_data(device)
                
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Check if device exists
                    cursor.execute("SELECT id FROM devices WHERE terid = ?", (normalized_device.get('terid'),))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing record
                        update_sql = """
                        UPDATE devices SET 
                            car_license = ?, sim = ?, channel = ?, plate_color = ?,
                            group_id = ?, cname = ?, device_type = ?, link_type = ?,
                            device_username = ?, device_password = ?, register_ip = ?,
                            register_port = ?, transmit_ip = ?, transmit_port = ?,
                            channel_enable = ?, company_branch = ?, company_name = ?,
                            last_updated = CURRENT_TIMESTAMP
                        WHERE terid = ?
                        """
                        values = (
                            normalized_device.get('carlicense'),
                            normalized_device.get('sim'),
                            normalized_device.get('channel'),
                            normalized_device.get('platecolor'),
                            normalized_device.get('groupid'),
                            normalized_device.get('cname'),
                            normalized_device.get('devicetype'),
                            normalized_device.get('linktype'),
                            normalized_device.get('deviceusername'),
                            normalized_device.get('devicepassword'),
                            normalized_device.get('registerip'),
                            normalized_device.get('registerport'),
                            normalized_device.get('transmitip'),
                            normalized_device.get('transmitport'),
                            normalized_device.get('en'),
                            normalized_device.get('companybranch'),
                            normalized_device.get('companyname'),
                            normalized_device.get('terid')
                        )
                        cursor.execute(update_sql, values)
                        results['updated'] += 1
                    else:
                        # Insert new record
                        insert_sql = """
                        INSERT INTO devices (
                            car_license, terid, sim, channel, plate_color, group_id,
                            cname, device_type, link_type, device_username,
                            device_password, register_ip, register_port, transmit_ip,
                            transmit_port, channel_enable, company_branch, company_name
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        values = (
                            normalized_device.get('carlicense'),
                            normalized_device.get('terid'),
                            normalized_device.get('sim'),
                            normalized_device.get('channel'),
                            normalized_device.get('platecolor'),
                            normalized_device.get('groupid'),
                            normalized_device.get('cname'),
                            normalized_device.get('devicetype'),
                            normalized_device.get('linktype'),
                            normalized_device.get('deviceusername'),
                            normalized_device.get('devicepassword'),
                            normalized_device.get('registerip'),
                            normalized_device.get('registerport'),
                            normalized_device.get('transmitip'),
                            normalized_device.get('transmitport'),
                            normalized_device.get('en'),
                            normalized_device.get('companybranch'),
                            normalized_device.get('companyname')
                        )
                        cursor.execute(insert_sql, values)
                        results['inserted'] += 1
                    
                    conn.commit()
                    
            except Exception as e:
                logger.error(f"Failed to process device {device.get('terid', 'unknown')}: {e}")
                results['failed'] += 1
        
        logger.info(f"Batch operation completed: {results}")
        return results
    
    def get_all_devices(self) -> List[Dict[str, Any]]:
        """Get all devices from database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM devices ORDER BY car_license")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch devices: {e}")
            return []
    
    def get_device_by_terid(self, terid: str) -> Optional[Dict[str, Any]]:
        """Get a specific device by terminal ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM devices WHERE terid = ?", (terid,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to fetch device {terid}: {e}")
            return None
    
    def get_device_count(self) -> int:
        """Get total number of devices"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM devices")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get device count: {e}")
            return 0
    
    def get_last_update_time(self) -> Optional[str]:
        """Get the timestamp of the most recent update"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(last_updated) FROM devices")
                result = cursor.fetchone()[0]
                return result
        except Exception as e:
            logger.error(f"Failed to get last update time: {e}")
            return None
    
    def get_all_device_terids(self) -> List[str]:
        """Get all device terminal IDs for alarm monitoring"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT terid FROM devices ORDER BY terid")
                rows = cursor.fetchall()
                return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch device terids: {e}")
            return []
    
    # Alarm-related methods
    
    def insert_alarm(self, alarm_data: Dict[str, Any]) -> bool:
        """
        Insert a new alarm record (ignore duplicates)
        Returns True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                insert_sql = """
                INSERT OR IGNORE INTO alarms (
                    terid, gps_time, altitude, direction, gps_lat, gps_lng,
                    speed, record_speed, state, server_time, alarm_type,
                    alarm_content, cmd_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                values = (
                    alarm_data.get('terid'),
                    alarm_data.get('gpstime'),
                    alarm_data.get('altitude'),
                    alarm_data.get('direction'),
                    alarm_data.get('gpslat'),
                    alarm_data.get('gpslng'),
                    alarm_data.get('speed'),
                    alarm_data.get('recordspeed'),
                    alarm_data.get('state'),
                    alarm_data.get('time'),
                    alarm_data.get('type'),
                    alarm_data.get('content'),
                    alarm_data.get('cmdtype')
                )
                
                cursor.execute(insert_sql, values)
                
                # Check if the row was actually inserted (not a duplicate)
                rows_affected = cursor.rowcount
                conn.commit()
                
                if rows_affected > 0:
                    logger.debug(f"Inserted new alarm for device {alarm_data.get('terid')}")
                else:
                    logger.debug(f"Duplicate alarm ignored for device {alarm_data.get('terid')}")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to insert alarm for device {alarm_data.get('terid', 'unknown')}: {e}")
            return False
    
    def insert_alarms_batch(self, alarms: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Batch insert multiple alarm records (ignore duplicates)
        Returns dict with counts of inserted/duplicates/failed records
        """
        results = {'inserted': 0, 'duplicates': 0, 'failed': 0}
        
        for alarm in alarms:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    insert_sql = """
                    INSERT OR IGNORE INTO alarms (
                        terid, gps_time, altitude, direction, gps_lat, gps_lng,
                        speed, record_speed, state, server_time, alarm_type,
                        alarm_content, cmd_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    
                    values = (
                        alarm.get('terid'),
                        alarm.get('gpstime'),
                        alarm.get('altitude'),
                        alarm.get('direction'),
                        alarm.get('gpslat'),
                        alarm.get('gpslng'),
                        alarm.get('speed'),
                        alarm.get('recordspeed'),
                        alarm.get('state'),
                        alarm.get('time'),
                        alarm.get('type'),
                        alarm.get('content'),
                        alarm.get('cmdtype')
                    )
                    
                    cursor.execute(insert_sql, values)
                    
                    # Check if the row was actually inserted (not a duplicate)
                    rows_affected = cursor.rowcount
                    conn.commit()
                    
                    if rows_affected > 0:
                        results['inserted'] += 1
                    else:
                        results['duplicates'] += 1
                    
            except Exception as e:
                logger.error(f"Failed to insert alarm for device {alarm.get('terid', 'unknown')}: {e}")
                results['failed'] += 1
        
        logger.info(f"Alarm batch operation completed: {results}")
        return results
    
    def get_alarms_by_terid(self, terid: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent alarms for a specific device"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM alarms WHERE terid = ? ORDER BY created_at DESC LIMIT ?", 
                    (terid, limit)
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch alarms for device {terid}: {e}")
            return []
    
    def get_recent_alarms(self, hours: int = 24, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get recent alarms within specified hours"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT * FROM alarms 
                       WHERE gps_time >= datetime('now', '-{} hours')
                       ORDER BY gps_time DESC LIMIT ?""".format(hours),
                    (limit,)
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch recent alarms: {e}")
            return []
    
    def get_alarm_count(self) -> int:
        """Get total number of alarms"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM alarms")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get alarm count: {e}")
            return 0
    
    def get_alarms_last_update_time(self) -> Optional[str]:
        """Get the timestamp of the most recent alarm update"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(last_updated) FROM alarms")
                result = cursor.fetchone()[0]
                return result
        except Exception as e:
            logger.error(f"Failed to get alarms last update time: {e}")
            return None
    
    def cleanup_old_alarms(self, days_to_keep: int = 30) -> int:
        """
        Clean up alarms older than specified days
        Returns number of records deleted
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM alarms WHERE created_at < datetime('now', '-{} days')".format(days_to_keep)
                )
                deleted_count = cursor.rowcount
                conn.commit()
                logger.info(f"Cleaned up {deleted_count} old alarm records")
                return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup old alarms: {e}")
            return 0
    
    def get_alarm_by_id(self, alarm_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific alarm by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM alarms WHERE id = ?", (alarm_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to fetch alarm {alarm_id}: {e}")
            return None
    
    def get_alarms_by_date_range(self, start_date: str, end_date: str, limit: int = 1000,
                                alarm_types: Optional[List[int]] = None, 
                                device_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get alarms within a date range with optional filtering"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT * FROM alarms 
                WHERE gps_time >= ? AND gps_time <= ?
                """
                params = [start_date, end_date]
                
                # Add alarm type filter
                if alarm_types:
                    placeholders = ','.join(['?' for _ in alarm_types])
                    query += f" AND alarm_type IN ({placeholders})"
                    params.extend(alarm_types)
                
                # Add device filter
                if device_id:
                    query += " AND terid = ?"
                    params.append(device_id)
                
                query += " ORDER BY gps_time DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to fetch alarms by date range: {e}")
            return []
    
    def get_distinct_alarm_types(self) -> List[Dict[str, Any]]:
        """Get distinct alarm types from the database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT alarm_type, COUNT(*) as count
                    FROM alarms 
                    WHERE alarm_type IS NOT NULL
                    GROUP BY alarm_type
                    ORDER BY count DESC
                """)
                rows = cursor.fetchall()
                
                # Map alarm types to descriptions based on API documentation Appendix 2
                alarm_type_names = {
                    1: "Video Loss", 2: "Motion Detection", 3: "Blind Detection", 4: "HDD/SD Error",
                    5: "IO 1", 6: "IO 2", 7: "IO 3", 8: "IO 4", 9: "IO 5", 10: "IO 6", 11: "IO 7", 12: "IO 8",
                    13: "Panic Button", 14: "Low Speed", 15: "High Speed", 16: "Low Voltage", 17: "G-Force",
                    18: "Geo-Fence", 19: "Unauthorised Ignition", 20: "Unauthorised Shutdown", 21: "GPS Fail",
                    22: "GPS Antenna Short", 23: "GPS Antenna Open", 24: "Overspeed", 25: "Idle Time",
                    26: "Harsh Acceleration", 27: "Harsh Cornering", 28: "Harsh Braking", 29: "Temperature Alarm",
                    30: "Fuel Alarm", 31: "Fuel Theft", 32: "Fuel Fill", 33: "Power Disconnected", 34: "Power Connected",
                    35: "Battery Low", 36: "Impact Alarm", 37: "SOS", 38: "Man Down", 39: "External Device Alarm",
                    40: "External Power On", 41: "External Power Off", 42: "System Power On", 43: "System Power Off",
                    44: "White List", 45: "Black List", 46: "RFID Card", 47: "Temperature Error",
                    48: "Acceleration Sensor Error", 49: "TTS Error", 50: "Camera Error", 51: "Voltage Error",
                    52: "Speed Limit", 53: "Route Deviation", 54: "Enter Area", 55: "Exit Area", 56: "Road Limit",
                    57: "Dangerous Driving", 58: "Driver Fatigue", 59: "No Driver", 60: "Phone Detection",
                    61: "Smoking Detection", 62: "Driver Distraction", 63: "Lane Departure", 64: "Forward Collision Warning",
                    65: "Pedestrian Collision Warning", 66: "Blind Spot", 67: "Driver Change", 68: "Abnormal Fuel Consumption",
                    69: "VSS Speed", 70: "Oil Pressure", 71: "Water Temperature", 72: "Neutral Safety Switch",
                    73: "Handbrake", 74: "Door Open", 75: "Seat Belt", 76: "Key Switch", 77: "Reverse Gear",
                    78: "Left Turn", 79: "Right Turn", 80: "Work Light", 81: "Retarder", 82: "Air Pressure",
                    83: "Engine Error", 84: "Auxiliary Battery", 85: "Emergency Button", 86: "Loading",
                    87: "Unloading", 88: "Driving Without License", 89: "Cumulative Driving Time", 90: "Road Maintenance",
                    91: "Fatigue Driving", 92: "Overtime Parking", 93: "Route Change", 94: "VSS Failure",
                    95: "Oil Shortage", 96: "Vehicle Theft", 97: "Illegal Ignition", 98: "Illegal Displacement",
                    99: "Collision Rollover", 100: "Side Rollover", 134: "Picture Upload", 135: "Video Upload",
                    136: "IC Card", 137: "Fingerprint", 138: "Retina", 139: "Face Recognition", 140: "Voice",
                    141: "Weight", 142: "Trailer Connection", 143: "Trailer Disconnection", 144: "Passenger Up",
                    145: "Passenger Down", 146: "School Bus", 147: "Emergency Evacuation", 148: "Anti-Theft",
                    149: "Refueling", 150: "Driver Hours", 151: "Custom Alarm", 152: "Maintenance",
                    153: "Diagnostic", 154: "Eco Driving", 155: "Green Band", 156: "Cruise Control",
                    157: "Lane Change", 158: "Tailgating", 159: "Cornering", 160: "Acceleration",
                    161: "Deceleration", 162: "Following Distance Monitoring", 163: "Speeding", 164: "Yawning Detection",
                    165: "Eyes Closed", 166: "Looking Away", 167: "Head Down", 168: "Using Phone"
                }
                
                result = []
                for row in rows:
                    alarm_type = row[0]
                    count = row[1]
                    result.append({
                        'type': alarm_type,
                        'name': alarm_type_names.get(alarm_type, f"Unknown ({alarm_type})"),
                        'count': count
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to fetch distinct alarm types: {e}")
            return []
    
    def store_gps_data(self, terid: str, car_license: Optional[str] = None,
                      gps_time: Optional[datetime] = None, latitude: float = 0,
                      longitude: float = 0, altitude: Optional[int] = None,
                      speed: Optional[int] = None, recordspeed: Optional[int] = None,
                      direction: Optional[int] = None, state: Optional[int] = None,
                      address: Optional[str] = None) -> bool:
        """
        Store GPS tracking data for a device.
        Uses REPLACE to update existing record for the device.
        
        Returns True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Use REPLACE to insert or update based on unique constraint
                sql = """
                    REPLACE INTO gps (
                        terid, car_license, gps_time, latitude, longitude,
                        altitude, speed, recordspeed, direction, state, address,
                        last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """
                
                cursor.execute(sql, (
                    terid,
                    car_license,
                    gps_time,
                    latitude,
                    longitude,
                    altitude,
                    speed,
                    recordspeed,
                    direction,
                    state,
                    address
                ))
                
                conn.commit()
                logger.debug(f"Stored GPS data for device {terid}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store GPS data: {e}")
            return False
    
    def get_all_gps_positions(self) -> List[Dict[str, Any]]:
        """
        Get the latest GPS positions for all devices
        
        Returns list of GPS position data
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                    SELECT 
                        g.id, g.terid, g.car_license, g.gps_time,
                        g.latitude, g.longitude, g.altitude, g.speed,
                        g.recordspeed, g.direction, g.state, g.address,
                        g.last_updated,
                        d.company_name, d.company_branch
                    FROM gps g
                    LEFT JOIN devices d ON g.terid = d.terid
                    ORDER BY g.last_updated DESC
                """
                
                cursor.execute(sql)
                rows = cursor.fetchall()
                
                result = []
                for row in rows:
                    result.append(dict(row))
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to fetch GPS positions: {e}")
            return []
    
    def get_gps_by_terid(self, terid: str) -> Optional[Dict[str, Any]]:
        """
        Get GPS position for a specific device
        
        Returns GPS data or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                    SELECT 
                        g.*, d.company_name, d.company_branch
                    FROM gps g
                    LEFT JOIN devices d ON g.terid = d.terid
                    WHERE g.terid = ?
                """
                
                cursor.execute(sql, (terid,))
                row = cursor.fetchone()
                
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Failed to fetch GPS position for {terid}: {e}")
            return None