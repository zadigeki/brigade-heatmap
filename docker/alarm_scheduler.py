"""
Scheduler for periodic alarm synchronization
"""
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Optional
from alarm_sync_service import AlarmSyncService

logger = logging.getLogger(__name__)

class AlarmSyncScheduler:
    """Scheduler for periodic alarm synchronization every 5 minutes"""
    
    def __init__(self, update_interval_minutes: int = 5):
        self.alarm_sync_service = AlarmSyncService()
        self.update_interval_minutes = update_interval_minutes
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._next_run_time: Optional[datetime] = None
    
    def start(self) -> bool:
        """Start the alarm scheduler"""
        if self._running:
            logger.warning("Alarm scheduler is already running")
            return False
        
        logger.info(f"Starting alarm sync scheduler (interval: {self.update_interval_minutes} minutes)")
        
        self._running = True
        self._stop_event.clear()
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        
        # Perform initial sync
        logger.info("Performing initial alarm sync...")
        initial_sync_success = self.alarm_sync_service.sync_alarms()
        if not initial_sync_success:
            logger.warning("Initial alarm sync failed, but scheduler will continue running")
        
        return True
    
    def stop(self) -> bool:
        """Stop the alarm scheduler"""
        if not self._running:
            logger.warning("Alarm scheduler is not running")
            return False
        
        logger.info("Stopping alarm sync scheduler...")
        self._running = False
        self._stop_event.set()
        
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=10)  # Wait up to 10 seconds
            
            if self._scheduler_thread.is_alive():
                logger.warning("Alarm scheduler thread did not stop gracefully")
                return False
        
        logger.info("Alarm sync scheduler stopped")
        return True
    
    def _scheduler_loop(self):
        """Main alarm scheduler loop"""
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
                
                # Perform alarm sync
                logger.info("Scheduled alarm sync starting...")
                success = self.alarm_sync_service.sync_alarms()
                
                if success:
                    logger.info("Scheduled alarm sync completed successfully")
                else:
                    logger.error("Scheduled alarm sync failed")
                
            except Exception as e:
                logger.error(f"Error in alarm scheduler loop: {e}")
                # Continue running even if there's an error
                time.sleep(60)  # Wait 1 minute before retrying
    
    def get_status(self) -> dict:
        """Get alarm scheduler status"""
        alarm_sync_status = self.alarm_sync_service.get_sync_status()
        
        return {
            'scheduler_running': self._running,
            'update_interval_minutes': self.update_interval_minutes,
            'next_run_time': self._next_run_time.isoformat() if self._next_run_time else None,
            'alarm_sync_status': alarm_sync_status
        }
    
    def force_sync(self) -> bool:
        """Force an immediate alarm sync"""
        return self.alarm_sync_service.force_sync()
    
    def is_running(self) -> bool:
        """Check if alarm scheduler is running"""
        return self._running
    
    def get_recent_alarms(self, hours: int = 24, limit: int = 100) -> list:
        """Get recent alarms"""
        return self.alarm_sync_service.get_recent_alarms(hours=hours, limit=limit)
    
    def get_device_alarms(self, terid: str, limit: int = 50) -> list:
        """Get alarms for a specific device"""
        return self.alarm_sync_service.get_device_alarms(terid=terid, limit=limit)