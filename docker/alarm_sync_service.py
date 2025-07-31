"""
Alarm synchronization service
Handles periodic fetching and updating of alarm data from all devices
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, List
from threading import Lock
from api_client import BrigadeAPIClient
from database import DatabaseManager

logger = logging.getLogger(__name__)

class AlarmSyncService:
    """Service to synchronize alarm data from API to database"""
    
    def __init__(self):
        self.api_client = BrigadeAPIClient()
        self.db_manager = DatabaseManager()
        self._sync_lock = Lock()
        self._last_sync_time: Optional[datetime] = None
        self._sync_in_progress = False
        
        # Configuration for alarm fetching
        self.lookback_minutes = 10  # How far back to look for alarms
        self.batch_size = 50  # Max devices to process per API call
    
    def sync_alarms(self) -> bool:
        """
        Synchronize alarms from all devices in the database
        Returns True if successful, False otherwise
        """
        if self._sync_in_progress:
            logger.warning("Alarm sync already in progress, skipping...")
            return False
        
        with self._sync_lock:
            self._sync_in_progress = True
            
            try:
                logger.info("Starting alarm synchronization...")
                start_time = time.time()
                
                # Get all device terminal IDs from database
                device_terids = self.db_manager.get_all_device_terids()
                if not device_terids:
                    logger.warning("No devices found in database for alarm monitoring")
                    return True
                
                logger.info(f"Monitoring alarms for {len(device_terids)} devices")
                
                # Calculate time range for alarm query
                end_time = datetime.now()
                start_time_query = end_time - timedelta(minutes=self.lookback_minutes)
                
                start_time_str = start_time_query.strftime("%Y-%m-%d %H:%M:%S")
                end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
                
                total_alarms = 0
                total_inserted = 0
                total_failed = 0
                
                # Process devices in batches to avoid overwhelming the API
                for i in range(0, len(device_terids), self.batch_size):
                    batch_terids = device_terids[i:i + self.batch_size]
                    
                    logger.debug(f"Processing alarm batch {i//self.batch_size + 1}: {len(batch_terids)} devices")
                    
                    # Fetch alarms for this batch
                    alarms = self.api_client.get_alarm_details(
                        terid_list=batch_terids,
                        start_time=start_time_str,
                        end_time=end_time_str
                    )
                    
                    if alarms is None:
                        logger.error(f"Failed to fetch alarms for batch {i//self.batch_size + 1}")
                        total_failed += len(batch_terids)
                        continue
                    
                    if alarms:
                        # Insert alarms into database
                        results = self.db_manager.insert_alarms_batch(alarms)
                        total_alarms += len(alarms)
                        total_inserted += results['inserted']
                        total_failed += results['failed']
                        
                        logger.debug(f"Batch {i//self.batch_size + 1}: {len(alarms)} alarms found, "
                                   f"{results['inserted']} inserted, {results['failed']} failed")
                    else:
                        logger.debug(f"Batch {i//self.batch_size + 1}: No alarms found")
                    
                    # Small delay between batches to be API-friendly
                    time.sleep(0.5)
                
                # Log results
                sync_duration = time.time() - start_time
                
                logger.info(
                    f"Alarm sync completed in {sync_duration:.2f}s: "
                    f"{total_alarms} total alarms, {total_inserted} inserted, "
                    f"{total_failed} failed"
                )
                
                self._last_sync_time = datetime.now()
                
                # Clean up old alarms periodically (once per hour)
                if (self._last_sync_time.minute == 0 or 
                    (self._last_sync_time - datetime.now().replace(second=0, microsecond=0)).total_seconds() < 300):
                    self._cleanup_old_alarms()
                
                # Return True if no major failures
                return total_failed == 0 or total_failed < (len(device_terids) * 0.1)
                
            except Exception as e:
                logger.error(f"Unexpected error during alarm sync: {e}")
                return False
            
            finally:
                self._sync_in_progress = False
    
    def _cleanup_old_alarms(self):
        """Clean up old alarm records to prevent database bloat"""
        try:
            logger.debug("Performing alarm cleanup...")
            deleted_count = self.db_manager.cleanup_old_alarms(days_to_keep=30)
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old alarm records")
        except Exception as e:
            logger.error(f"Failed to cleanup old alarms: {e}")
    
    def sync_alarms_for_device(self, terid: str, lookback_hours: int = 1) -> bool:
        """
        Sync alarms for a specific device
        
        Args:
            terid: Device terminal ID
            lookback_hours: How many hours back to fetch alarms
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Calculate time range
            end_time = datetime.now()
            start_time_query = end_time - timedelta(hours=lookback_hours)
            
            start_time_str = start_time_query.strftime("%Y-%m-%d %H:%M:%S")
            end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
            
            logger.debug(f"Fetching alarms for device {terid} from {start_time_str} to {end_time_str}")
            
            # Fetch alarms
            alarms = self.api_client.get_alarm_details_for_device(
                terid=terid,
                start_time=start_time_str,
                end_time=end_time_str
            )
            
            if alarms is None:
                logger.error(f"Failed to fetch alarms for device {terid}")
                return False
            
            if not alarms:
                logger.debug(f"No alarms found for device {terid}")
                return True
            
            # Insert alarms
            results = self.db_manager.insert_alarms_batch(alarms)
            
            logger.info(f"Device {terid}: {len(alarms)} alarms found, "
                       f"{results['inserted']} inserted, {results['failed']} failed")
            
            return results['failed'] == 0
            
        except Exception as e:
            logger.error(f"Failed to sync alarms for device {terid}: {e}")
            return False
    
    def get_sync_status(self) -> dict:
        """Get current alarm sync status information"""
        device_count = self.db_manager.get_device_count()
        alarm_count = self.db_manager.get_alarm_count()
        last_alarm_update = self.db_manager.get_alarms_last_update_time()
        
        return {
            'last_sync_time': self._last_sync_time.isoformat() if self._last_sync_time else None,
            'sync_in_progress': self._sync_in_progress,
            'total_devices_monitored': device_count,
            'total_alarms': alarm_count,
            'last_alarm_update': last_alarm_update,
            'lookback_minutes': self.lookback_minutes,
            'batch_size': self.batch_size
        }
    
    def force_sync(self) -> bool:
        """Force an immediate alarm sync regardless of schedule"""
        logger.info("Force alarm sync requested")
        return self.sync_alarms()
    
    def get_recent_alarms(self, hours: int = 24, limit: int = 100) -> List[dict]:
        """Get recent alarms from the database"""
        try:
            return self.db_manager.get_recent_alarms(hours=hours, limit=limit)
        except Exception as e:
            logger.error(f"Failed to fetch recent alarms: {e}")
            return []
    
    def get_device_alarms(self, terid: str, limit: int = 50) -> List[dict]:
        """Get recent alarms for a specific device"""
        try:
            return self.db_manager.get_alarms_by_terid(terid=terid, limit=limit)
        except Exception as e:
            logger.error(f"Failed to fetch alarms for device {terid}: {e}")
            return []