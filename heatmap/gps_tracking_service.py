"""
GPS Tracking Service for Brigade Electronics Devices
Fetches real-time GPS data from Brigade API and stores in database
"""
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from api_client import BrigadeAPIClient
from database import DatabaseManager
from config import API_CONFIG

logger = logging.getLogger(__name__)

class GPSTrackingService:
    """Service to fetch and store GPS tracking data"""
    
    def __init__(self):
        self.api_client = BrigadeAPIClient()
        self.db_manager = DatabaseManager()
        
    def sync_gps_data(self) -> bool:
        """Fetch latest GPS positions for all devices and store in database"""
        try:
            # Get all devices from database
            devices = self.db_manager.get_all_devices()
            if not devices:
                logger.warning("No devices found in database")
                return False
            
            # Extract device IDs (terids)
            device_ids = [device['terid'] for device in devices]
            logger.info(f"Fetching GPS data for {len(device_ids)} devices")
            
            # Get last GPS positions from API
            gps_data = self.api_client.get_last_gps_positions(device_ids)
            if not gps_data:
                logger.warning("No GPS data received from API")
                return False
            
            # Store GPS data in database
            success_count = 0
            for gps_point in gps_data:
                if self._store_gps_data(gps_point):
                    success_count += 1
            
            logger.info(f"Successfully stored GPS data for {success_count}/{len(gps_data)} devices")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error syncing GPS data: {e}")
            return False
    
    def _store_gps_data(self, gps_point: Dict[str, Any]) -> bool:
        """Store single GPS data point in database"""
        try:
            # Extract and validate GPS data
            terid = gps_point.get('terid')
            if not terid:
                logger.warning(f"Missing terid in GPS data: {gps_point}")
                return False
            
            # Get device info for car_license
            device = self.db_manager.get_device_by_terid(terid)
            car_license = device['car_license'] if device else None
            
            # Parse GPS coordinates
            try:
                latitude = float(gps_point.get('gpslat', 0))
                longitude = float(gps_point.get('gpslng', 0))
                
                # Skip invalid coordinates
                if latitude == 0 and longitude == 0:
                    logger.debug(f"Skipping GPS data with zero coordinates for {terid}")
                    return False
                    
                if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                    logger.warning(f"Invalid GPS coordinates for {terid}: lat={latitude}, lng={longitude}")
                    return False
                    
            except (ValueError, TypeError):
                logger.warning(f"Invalid GPS coordinates for {terid}")
                return False
            
            # Parse other fields
            altitude = self._safe_int(gps_point.get('altitude'))
            speed = self._safe_int(gps_point.get('speed'))
            recordspeed = self._safe_int(gps_point.get('recordspeed'))
            direction = self._safe_int(gps_point.get('direction'))
            state = self._safe_int(gps_point.get('state'))
            
            # Parse timestamps
            gps_time = self._parse_timestamp(gps_point.get('gpstime'))
            
            # Store in database (will update if exists due to unique constraint)
            self.db_manager.store_gps_data(
                terid=terid,
                car_license=car_license,
                gps_time=gps_time,
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                speed=speed,
                recordspeed=recordspeed,
                direction=direction,
                state=state
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing GPS data: {e}")
            return False
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to integer"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse timestamp string to datetime object"""
        if not timestamp_str:
            return None
        
        try:
            # Expected format: "2017-06-19 00:00:00"
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            logger.warning(f"Invalid timestamp format: {timestamp_str}")
            return None
    
    def run_continuous(self, interval_seconds: int = 30):
        """Run GPS sync continuously with specified interval"""
        logger.info(f"Starting continuous GPS tracking (interval: {interval_seconds}s)")
        
        while True:
            try:
                logger.info("Starting GPS data sync...")
                self.sync_gps_data()
                
                logger.info(f"GPS sync completed. Sleeping for {interval_seconds} seconds...")
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("GPS tracking service stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in GPS tracking loop: {e}")
                logger.info(f"Retrying in {interval_seconds} seconds...")
                time.sleep(interval_seconds)

def main():
    """Run the GPS tracking service"""
    import argparse
    from logging_config import setup_logging
    
    parser = argparse.ArgumentParser(description="Brigade Electronics GPS Tracking Service")
    parser.add_argument('--interval', type=int, default=30, 
                       help='Update interval in seconds (default: 30)')
    parser.add_argument('--once', action='store_true', 
                       help='Run once and exit instead of continuous mode')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Set logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Create and run service
    service = GPSTrackingService()
    
    if args.once:
        logger.info("Running GPS sync once...")
        if service.sync_gps_data():
            logger.info("GPS sync completed successfully")
        else:
            logger.error("GPS sync failed")
    else:
        service.run_continuous(interval_seconds=args.interval)

if __name__ == "__main__":
    main()