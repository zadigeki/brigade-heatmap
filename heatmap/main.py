"""
Main application for Brigade Electronics device and alarm synchronization
"""
import sys
import signal
import time
import argparse
from typing import Optional
from logging_config import setup_logging, get_logger
from scheduler import DeviceSyncScheduler
from alarm_scheduler import AlarmSyncScheduler
from device_sync_service import DeviceSyncService
from alarm_sync_service import AlarmSyncService

logger = get_logger(__name__)

class BrigadeElectronicsApp:
    """Main application class for device and alarm synchronization"""
    
    def __init__(self):
        self.device_scheduler: Optional[DeviceSyncScheduler] = None
        self.alarm_scheduler: Optional[AlarmSyncScheduler] = None
        self._running = False
    
    def start(self) -> bool:
        """Start the application"""
        try:
            logger.info("Starting Brigade Electronics Device and Alarm Sync Service")
            
            # Initialize schedulers
            self.device_scheduler = DeviceSyncScheduler()
            self.alarm_scheduler = AlarmSyncScheduler()
            
            # Start device scheduler
            if not self.device_scheduler.start():
                logger.error("Failed to start device scheduler")
                return False
            
            # Start alarm scheduler
            if not self.alarm_scheduler.start():
                logger.error("Failed to start alarm scheduler")
                # Stop device scheduler if alarm scheduler fails
                self.device_scheduler.stop()
                return False
            
            self._running = True
            logger.info("Brigade Electronics Sync Service started successfully")
            logger.info("- Device sync: every 10 minutes")
            logger.info("- Alarm sync: every 5 minutes")
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            return False
    
    def stop(self):
        """Stop the application"""
        if not self._running:
            return
        
        logger.info("Stopping Brigade Electronics Sync Service...")
        self._running = False
        
        # Stop both schedulers
        if self.device_scheduler:
            self.device_scheduler.stop()
        
        if self.alarm_scheduler:
            self.alarm_scheduler.stop()
        
        logger.info("Brigade Electronics Sync Service stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def run(self):
        """Run the application"""
        if not self.start():
            logger.error("Failed to start application")
            return 1
        
        try:
            # Keep the main thread alive
            while self._running:
                time.sleep(5)
                
                # Check if schedulers are still running
                if self.device_scheduler and not self.device_scheduler.is_running():
                    logger.error("Device scheduler stopped unexpectedly")
                    break
                
                if self.alarm_scheduler and not self.alarm_scheduler.is_running():
                    logger.error("Alarm scheduler stopped unexpectedly")
                    break
                    
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.stop()
        
        return 0
    
    def status(self):
        """Show application status"""
        if not self.device_scheduler or not self.alarm_scheduler:
            print("Schedulers not initialized")
            return
        
        device_status = self.device_scheduler.get_status()
        alarm_status = self.alarm_scheduler.get_status()
        
        print("\n=== Brigade Electronics Sync Service Status ===")
        
        # Device sync status
        print("\n--- Device Sync Status ---")
        print(f"Scheduler Running: {device_status['scheduler_running']}")
        print(f"Update Interval: {device_status['update_interval_minutes']} minutes")
        print(f"Next Run Time: {device_status['next_run_time']}")
        print(f"Total Devices: {device_status['sync_status']['total_devices']}")
        print(f"Last Sync Time: {device_status['sync_status']['last_sync_time']}")
        print(f"Last DB Update: {device_status['sync_status']['last_db_update']}")
        print(f"Sync In Progress: {device_status['sync_status']['sync_in_progress']}")
        
        # Alarm sync status
        print("\n--- Alarm Sync Status ---")
        print(f"Scheduler Running: {alarm_status['scheduler_running']}")
        print(f"Update Interval: {alarm_status['update_interval_minutes']} minutes")
        print(f"Next Run Time: {alarm_status['next_run_time']}")
        print(f"Total Devices Monitored: {alarm_status['alarm_sync_status']['total_devices_monitored']}")
        print(f"Total Alarms: {alarm_status['alarm_sync_status']['total_alarms']}")
        print(f"Last Sync Time: {alarm_status['alarm_sync_status']['last_sync_time']}")
        print(f"Last Alarm Update: {alarm_status['alarm_sync_status']['last_alarm_update']}")
        print(f"Sync In Progress: {alarm_status['alarm_sync_status']['sync_in_progress']}")
        print(f"Lookback Minutes: {alarm_status['alarm_sync_status']['lookback_minutes']}")
        
        print("=" * 55)
    
    def force_sync(self, sync_type: str = 'both'):
        """Force an immediate sync"""
        if not self.device_scheduler or not self.alarm_scheduler:
            logger.error("Schedulers not initialized")
            return False
        
        success = True
        
        if sync_type in ['both', 'devices']:
            logger.info("Forcing immediate device sync...")
            device_success = self.device_scheduler.force_sync()
            if device_success:
                logger.info("Force device sync completed successfully")
            else:
                logger.error("Force device sync failed")
                success = False
        
        if sync_type in ['both', 'alarms']:
            logger.info("Forcing immediate alarm sync...")
            alarm_success = self.alarm_scheduler.force_sync()
            if alarm_success:
                logger.info("Force alarm sync completed successfully")
            else:
                logger.error("Force alarm sync failed")
                success = False
        
        return success

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Brigade Electronics Device and Alarm Sync Service")
    parser.add_argument(
        '--log-level', 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
        default='INFO',
        help='Set logging level'
    )
    parser.add_argument(
        '--command',
        choices=['start', 'status', 'sync'],
        default='start',
        help='Command to execute'
    )
    parser.add_argument(
        '--sync-type',
        choices=['both', 'devices', 'alarms'],
        default='both',
        help='Type of sync to perform (only used with sync command)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Create application instance
    app = BrigadeElectronicsApp()
    
    try:
        if args.command == 'start':
            # Run the service
            return app.run()
        
        elif args.command == 'status':
            # Show status
            app.device_scheduler = DeviceSyncScheduler()
            app.alarm_scheduler = AlarmSyncScheduler()
            app.status()
            return 0
        
        elif args.command == 'sync':
            # Force sync
            if args.sync_type in ['both', 'devices']:
                sync_service = DeviceSyncService()
                device_success = sync_service.sync_devices()
                if device_success:
                    logger.info("Manual device sync completed successfully")
                else:
                    logger.error("Manual device sync failed")
            
            if args.sync_type in ['both', 'alarms']:
                alarm_service = AlarmSyncService()
                alarm_success = alarm_service.sync_alarms()
                if alarm_success:
                    logger.info("Manual alarm sync completed successfully")
                else:
                    logger.error("Manual alarm sync failed")
            
            # Return success if all requested syncs succeeded
            overall_success = True
            if args.sync_type in ['both', 'devices']:
                overall_success = overall_success and device_success
            if args.sync_type in ['both', 'alarms']:
                overall_success = overall_success and alarm_success
            
            return 0 if overall_success else 1
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())