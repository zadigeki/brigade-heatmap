#!/usr/bin/env python3
"""
One-time GPS sync script to populate initial data
"""
import logging
from logging_config import setup_logging
from gps_tracking_service import GPSTrackingService
from device_sync_service import DeviceSyncService

def main():
    """Sync devices and GPS data once"""
    setup_logging('INFO')
    
    print("Brigade GPS Data Sync")
    print("=" * 30)
    
    try:
        # First sync devices
        print("Syncing devices from Brigade API...")
        device_service = DeviceSyncService()
        device_success = device_service.sync_devices()
        
        if device_success:
            print("Device sync completed")
        else:
            print("Device sync completed with warnings")
        
        # Then sync GPS data
        print("\nSyncing GPS positions from Brigade API...")
        gps_service = GPSTrackingService()
        gps_success = gps_service.sync_gps_data()
        
        if gps_success:
            print("GPS sync completed")
        else:
            print("GPS sync completed with warnings")
        
        # Show results
        from database import DatabaseManager
        db = DatabaseManager()
        
        devices = db.get_all_devices()
        gps_positions = db.get_all_gps_positions()
        
        print(f"\nResults:")
        print(f"  Devices in database: {len(devices)}")
        print(f"  GPS positions: {len(gps_positions)}")
        
        if gps_positions:
            print(f"\nRecent GPS positions:")
            for i, pos in enumerate(gps_positions[:5]):
                print(f"  {i+1}. {pos.get('car_license', pos.get('terid'))}: "
                      f"{pos.get('latitude'):.6f}, {pos.get('longitude'):.6f} "
                      f"({pos.get('speed', 0)} km/h)")
        
        if len(gps_positions) > 0:
            print(f"\nSuccess! GPS tracking should now show {len(gps_positions)} vehicles on the map.")
            print(f"   Start the web server and navigate to: http://localhost:5000/gps-tracking")
        else:
            print(f"\nNo GPS data found. Possible issues:")
            print(f"   - Check API configuration in config.py")
            print(f"   - Ensure devices are online and sending GPS data")
            print(f"   - Check Brigade API server connectivity")
        
    except Exception as e:
        print(f"Error during sync: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()