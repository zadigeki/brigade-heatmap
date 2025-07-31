"""
Scheduler for periodic device synchronization
"""
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Optional
from device_sync_service import DeviceSyncService
from config import SCHEDULER_CONFIG

logger = logging.getLogger(__name__)

class DeviceSyncScheduler:
    """Scheduler for periodic device synchronization"""
    
    def __init__(self):
        self.sync_service = DeviceSyncService()
        self.update_interval_minutes = SCHEDULER_CONFIG.update_interval_minutes
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._next_run_time: Optional[datetime] = None
    
    def start(self) -> bool:
        """Start the scheduler"""
        if self._running:
            logger.warning("Scheduler is already running")
            return False
        
        logger.info(f"Starting device sync scheduler (interval: {self.update_interval_minutes} minutes)")
        
        # Validate API connection before starting
        if not self.sync_service.validate_api_connection():
            logger.error("Cannot start scheduler: API connection validation failed")
            return False
        
        self._running = True
        self._stop_event.clear()
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        
        # Perform initial sync
        logger.info("Performing initial device sync...")
        initial_sync_success = self.sync_service.sync_devices()
        if not initial_sync_success:
            logger.warning("Initial sync failed, but scheduler will continue running")
        
        return True
    
    def stop(self) -> bool:
        """Stop the scheduler"""
        if not self._running:
            logger.warning("Scheduler is not running")
            return False
        
        logger.info("Stopping device sync scheduler...")
        self._running = False
        self._stop_event.set()
        
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=10)  # Wait up to 10 seconds
            
            if self._scheduler_thread.is_alive():
                logger.warning("Scheduler thread did not stop gracefully")
                return False
        
        logger.info("Device sync scheduler stopped")
        return True
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self._running and not self._stop_event.is_set():
            try:
                # Calculate next run time
                self._next_run_time = datetime.now() + timedelta(minutes=self.update_interval_minutes)
                
                # Wait for the interval or stop event
                if self._stop_event.wait(timeout=self.update_interval_minutes * 60):
                    # Stop event was set
                    break
                
                if not self._running:
                    break
                
                # Perform sync
                logger.info("Scheduled device sync starting...")
                success = self.sync_service.sync_devices()
                
                if success:
                    logger.info("Scheduled device sync completed successfully")
                else:
                    logger.error("Scheduled device sync failed")
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                # Continue running even if there's an error
                time.sleep(60)  # Wait 1 minute before retrying
    
    def get_status(self) -> dict:
        """Get scheduler status"""
        sync_status = self.sync_service.get_sync_status()
        
        return {
            'scheduler_running': self._running,
            'update_interval_minutes': self.update_interval_minutes,
            'next_run_time': self._next_run_time.isoformat() if self._next_run_time else None,
            'sync_status': sync_status
        }
    
    def force_sync(self) -> bool:
        """Force an immediate sync"""
        return self.sync_service.force_sync()
    
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._running