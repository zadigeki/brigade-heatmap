#!/usr/bin/env python3
"""
Test script for GPS tracking functionality
"""
import logging
from gps_tracking_service import GPSTrackingService
from logging_config import setup_logging

def test_gps_sync():
    """Test GPS data synchronization"""
    # Setup logging
    setup_logging('INFO')
    
    # Create GPS tracking service
    service = GPSTrackingService()
    
    # Test GPS sync
    print("Testing GPS data synchronization...")
    success = service.sync_gps_data()
    
    if success:
        print("✓ GPS sync completed successfully")
        
        # Check database for GPS data
        from database import DatabaseManager
        db = DatabaseManager()
        positions = db.get_all_gps_positions()
        
        print(f"\nFound {len(positions)} GPS positions in database:")
        for pos in positions[:5]:  # Show first 5
            print(f"  - {pos.get('car_license', pos.get('terid'))}: "
                  f"lat={pos.get('latitude'):.6f}, lng={pos.get('longitude'):.6f}, "
                  f"speed={pos.get('speed')} km/h")
        
        if len(positions) > 5:
            print(f"  ... and {len(positions) - 5} more")
    else:
        print("✗ GPS sync failed")

if __name__ == "__main__":
    test_gps_sync()