#!/usr/bin/env python3
"""
Brigade Electronics Monitoring System
Unified launcher for GPS tracking and web services
"""
import os
import sys
import time
import signal
import argparse
import threading
import subprocess
from logging_config import setup_logging
import logging

logger = logging.getLogger(__name__)

class BrigadeMonitoringSystem:
    """Main system controller"""
    
    def __init__(self, host='127.0.0.1', port=5000, gps_interval=30, debug=False):
        self.host = host
        self.port = port
        self.gps_interval = gps_interval
        self.debug = debug
        self.processes = []
        self.threads = []
        self.shutdown_event = threading.Event()
        
    def start_gps_tracking_service(self):
        """Start GPS tracking service in a separate thread"""
        def run_gps_service():
            try:
                from gps_tracking_service import GPSTrackingService
                
                logger.info("Starting GPS tracking service...")
                service = GPSTrackingService()
                
                while not self.shutdown_event.is_set():
                    try:
                        logger.info("Syncing GPS data...")
                        success = service.sync_gps_data()
                        
                        if success:
                            logger.info("GPS sync completed successfully")
                        else:
                            logger.warning("GPS sync failed")
                        
                        # Wait for next interval or shutdown signal
                        if self.shutdown_event.wait(timeout=self.gps_interval):
                            break
                            
                    except Exception as e:
                        logger.error(f"Error in GPS sync loop: {e}")
                        if self.shutdown_event.wait(timeout=30):
                            break
                
                logger.info("GPS tracking service stopped")
                
            except Exception as e:
                logger.error(f"Failed to start GPS tracking service: {e}")
        
        gps_thread = threading.Thread(target=run_gps_service, daemon=True)
        gps_thread.start()
        self.threads.append(gps_thread)
        
    def start_web_server(self):
        """Start web server in a separate thread"""
        def run_web_server():
            try:
                from web_server import AlarmHeatmapServer
                
                logger.info(f"Starting web server on {self.host}:{self.port}...")
                server = AlarmHeatmapServer(host=self.host, port=self.port, debug=self.debug)
                server.run()
                
            except Exception as e:
                logger.error(f"Failed to start web server: {e}")
        
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()
        self.threads.append(web_thread)
    
    def start_device_sync_service(self):
        """Start device synchronization service"""
        def run_device_sync():
            try:
                from device_sync_service import DeviceSyncService
                
                logger.info("Starting device sync service...")
                service = DeviceSyncService()
                
                # Initial sync
                service.sync_devices()
                
                # Periodic sync every hour
                while not self.shutdown_event.is_set():
                    if self.shutdown_event.wait(timeout=3600):  # 1 hour
                        break
                    
                    try:
                        logger.info("Syncing devices...")
                        service.sync_devices()
                    except Exception as e:
                        logger.error(f"Error in device sync: {e}")
                
                logger.info("Device sync service stopped")
                
            except Exception as e:
                logger.error(f"Failed to start device sync service: {e}")
        
        device_thread = threading.Thread(target=run_device_sync, daemon=True)
        device_thread.start()
        self.threads.append(device_thread)
    
    def start_alarm_sync_service(self):
        """Start alarm synchronization service"""
        def run_alarm_sync():
            try:
                from alarm_sync_service import AlarmSyncService
                
                logger.info("Starting alarm sync service...")
                service = AlarmSyncService()
                
                while not self.shutdown_event.is_set():
                    try:
                        logger.info("Syncing alarms...")
                        service.sync_alarms()
                        
                        # Wait 5 minutes between alarm syncs
                        if self.shutdown_event.wait(timeout=300):
                            break
                            
                    except Exception as e:
                        logger.error(f"Error in alarm sync: {e}")
                        if self.shutdown_event.wait(timeout=60):
                            break
                
                logger.info("Alarm sync service stopped")
                
            except Exception as e:
                logger.error(f"Failed to start alarm sync service: {e}")
        
        alarm_thread = threading.Thread(target=run_alarm_sync, daemon=True)
        alarm_thread.start()
        self.threads.append(alarm_thread)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown all services"""
        logger.info("Shutting down Brigade Monitoring System...")
        
        # Signal all threads to stop
        self.shutdown_event.set()
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=5)
        
        # Terminate any remaining processes
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                logger.error(f"Error terminating process: {e}")
        
        logger.info("System shutdown complete")
    
    def run(self):
        """Start all services"""
        logger.info("Starting Brigade Electronics Monitoring System")
        logger.info(f"Web interface will be available at: http://{self.host}:{self.port}")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # Start all services
            self.start_device_sync_service()
            time.sleep(2)  # Give device sync time to complete initial sync
            
            self.start_gps_tracking_service()
            self.start_alarm_sync_service()
            self.start_web_server()
            
            logger.info("All services started successfully")
            logger.info("System is running. Press Ctrl+C to stop.")
            
            # Keep main thread alive
            try:
                while not self.shutdown_event.is_set():
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                
        except Exception as e:
            logger.error(f"Error starting system: {e}")
        finally:
            self.shutdown()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Brigade Electronics Monitoring System")
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind web server to')
    parser.add_argument('--port', type=int, default=5000, help='Port for web server')
    parser.add_argument('--gps-interval', type=int, default=30, 
                       help='GPS update interval in seconds')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Set logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Create and run system
    system = BrigadeMonitoringSystem(
        host=args.host,
        port=args.port,
        gps_interval=args.gps_interval,
        debug=args.debug
    )
    
    system.run()

if __name__ == "__main__":
    main()