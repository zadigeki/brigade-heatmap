"""
Device synchronization service
Handles periodic fetching and updating of device data
"""
import logging
import time
from datetime import datetime
from typing import Optional
from threading import Lock
from api_client import BrigadeAPIClient
from database import DatabaseManager

logger = logging.getLogger(__name__)

class DeviceSyncService:
    """Service to synchronize device data from API to database"""
    
    def __init__(self):
        self.api_client = BrigadeAPIClient()
        self.db_manager = DatabaseManager()
        self._sync_lock = Lock()
        self._last_sync_time: Optional[datetime] = None
        self._sync_in_progress = False
    
    def sync_devices(self) -> bool:
        """
        Synchronize devices from API to database
        Returns True if successful, False otherwise
        """
        if self._sync_in_progress:
            logger.warning("Sync already in progress, skipping...")
            return False
        
        with self._sync_lock:
            self._sync_in_progress = True
            
            try:
                logger.info("Starting device synchronization...")
                start_time = time.time()
                
                # Fetch devices from API
                devices = self.api_client.get_devices()
                if devices is None:
                    logger.error("Failed to fetch devices from API")
                    return False
                
                if not devices:
                    logger.warning("No devices returned from API")
                    return True
                
                # Batch update database
                results = self.db_manager.upsert_devices_batch(devices)
                
                # Log results
                total_processed = results['inserted'] + results['updated'] + results['failed']
                sync_duration = time.time() - start_time
                
                logger.info(
                    f"Device sync completed in {sync_duration:.2f}s: "
                    f"{total_processed} total, {results['inserted']} inserted, "
                    f"{results['updated']} updated, {results['failed']} failed"
                )
                
                self._last_sync_time = datetime.now()
                
                # Return True if no failures or only minor failures
                return results['failed'] == 0 or results['failed'] < (total_processed * 0.1)
                
            except Exception as e:
                logger.error(f"Unexpected error during device sync: {e}")
                return False
            
            finally:
                self._sync_in_progress = False
    
    def get_sync_status(self) -> dict:
        """Get current sync status information"""
        device_count = self.db_manager.get_device_count()
        last_db_update = self.db_manager.get_last_update_time()
        
        return {
            'last_sync_time': self._last_sync_time.isoformat() if self._last_sync_time else None,
            'sync_in_progress': self._sync_in_progress,
            'total_devices': device_count,
            'last_db_update': last_db_update
        }
    
    def force_sync(self) -> bool:
        """Force an immediate sync regardless of schedule"""
        logger.info("Force sync requested")
        return self.sync_devices()
    
    def validate_api_connection(self) -> bool:
        """Test API connection and authentication"""
        try:
            return self.api_client.authenticate()
        except Exception as e:
            logger.error(f"API validation failed: {e}")
            return False