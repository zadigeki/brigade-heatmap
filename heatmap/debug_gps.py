#!/usr/bin/env python3
"""
Debug script to check GPS tracking data flow
"""
import logging
from logging_config import setup_logging
from database import DatabaseManager
from api_client import BrigadeAPIClient
from gps_tracking_service import GPSTrackingService

def check_database_gps():
    """Check what GPS data is in the database"""
    print("🔍 Checking GPS data in database...")
    try:
        db = DatabaseManager()
        
        # Check GPS table
        positions = db.get_all_gps_positions()
        print(f"  Found {len(positions)} GPS positions in database")
        
        if positions:
            print("  Recent GPS entries:")
            for i, pos in enumerate(positions[:5]):
                print(f"    {i+1}. Device: {pos.get('car_license', pos.get('terid'))}")
                print(f"       Location: {pos.get('latitude')}, {pos.get('longitude')}")
                print(f"       Speed: {pos.get('speed')} km/h")
                print(f"       Last Update: {pos.get('last_updated')}")
                print()
        else:
            print("  ❌ No GPS positions found in database")
            return False
            
        return len(positions) > 0
        
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def check_devices():
    """Check if devices exist in database"""
    print("🔍 Checking devices in database...")
    try:
        db = DatabaseManager()
        devices = db.get_all_devices()
        print(f"  Found {len(devices)} devices in database")
        
        if devices:
            print("  Devices:")
            for device in devices[:5]:
                print(f"    - {device.get('car_license', 'No License')} ({device.get('terid')})")
        else:
            print("  ❌ No devices found in database")
            return False
            
        return len(devices) > 0
        
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def test_api_gps_fetch():
    """Test fetching GPS data from API"""
    print("🔍 Testing GPS data fetch from Brigade API...")
    try:
        client = BrigadeAPIClient()
        
        # Test authentication
        if not client.authenticate():
            print("  ❌ API authentication failed")
            return False
        print("  ✅ API authentication successful")
        
        # Get devices first
        devices = client.get_devices()
        if not devices:
            print("  ❌ No devices found in API")
            return False
        print(f"  Found {len(devices)} devices in API")
        
        # Get device IDs
        device_ids = [device.get('terid') for device in devices if device.get('terid')]
        print(f"  Device IDs: {device_ids[:5]}...")
        
        # Test GPS fetch
        gps_data = client.get_last_gps_positions(device_ids)
        if not gps_data:
            print("  ❌ No GPS data returned from API")
            return False
            
        print(f"  ✅ Retrieved GPS data for {len(gps_data)} devices")
        
        # Show sample GPS data
        print("  Sample GPS data:")
        for i, gps in enumerate(gps_data[:3]):
            lat = gps.get('gpslat', 0)
            lng = gps.get('gpslng', 0)
            speed = gps.get('speed', 0)
            terid = gps.get('terid', 'Unknown')
            print(f"    {i+1}. Device: {terid}")
            print(f"       GPS: {lat}, {lng}")
            print(f"       Speed: {speed} km/h")
            print()
            
        return True
        
    except Exception as e:
        print(f"  ❌ API test error: {e}")
        return False

def test_gps_sync():
    """Test GPS synchronization service"""
    print("🔍 Testing GPS synchronization...")
    try:
        service = GPSTrackingService()
        success = service.sync_gps_data()
        
        if success:
            print("  ✅ GPS sync completed successfully")
            
            # Check database again
            db = DatabaseManager()
            positions = db.get_all_gps_positions()
            print(f"  Database now has {len(positions)} GPS positions")
            return True
        else:
            print("  ❌ GPS sync failed")
            return False
            
    except Exception as e:
        print(f"  ❌ GPS sync error: {e}")
        return False

def check_gps_api_endpoint():
    """Test the web API endpoint"""
    print("🔍 Testing GPS API endpoint...")
    try:
        import requests
        import time
        import threading
        
        # Start web server in background
        def start_server():
            from web_server import AlarmHeatmapServer
            server = AlarmHeatmapServer(host='127.0.0.1', port=5003, debug=False)
            server.run()
        
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        time.sleep(3)
        
        response = requests.get('http://127.0.0.1:5003/api/gps/positions', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                positions = data.get('positions', [])
                print(f"  ✅ API returned {len(positions)} GPS positions")
                
                if positions:
                    print("  Sample positions from API:")
                    for i, pos in enumerate(positions[:3]):
                        print(f"    {i+1}. {pos.get('car_license', pos.get('terid'))}: {pos.get('latitude')}, {pos.get('longitude')}")
                else:
                    print("  ⚠️  API returned success but no positions")
                
                return len(positions) > 0
            else:
                print(f"  ❌ API returned error: {data.get('error')}")
                return False
        else:
            print(f"  ❌ API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ API endpoint test error: {e}")
        return False

def main():
    """Run all GPS debugging checks"""
    setup_logging('INFO')
    
    print("🚀 Brigade GPS Tracking Debug")
    print("=" * 50)
    
    checks = [
        ("Database Devices", check_devices),
        ("Database GPS Data", check_database_gps),
        ("API GPS Fetch", test_api_gps_fetch),
        ("GPS Sync Service", test_gps_sync),
        ("Web API Endpoint", check_gps_api_endpoint)
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n📋 Running {check_name} check...")
        try:
            if check_func():
                passed += 1
                print(f"✅ {check_name} - PASSED")
            else:
                print(f"❌ {check_name} - FAILED")
        except Exception as e:
            print(f"❌ {check_name} - ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"🏁 Debug Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All checks passed! GPS tracking should work.")
    else:
        print("⚠️  Some checks failed. Recommendations:")
        
        if passed == 0:
            print("  1. Check API configuration in config.py")
            print("  2. Ensure Brigade API server is accessible")
            print("  3. Run device sync first: python device_sync_service.py --once")
        elif passed < 3:
            print("  1. Run GPS sync: python gps_tracking_service.py --once")
            print("  2. Check API connectivity and device data")
        else:
            print("  1. Clear browser cache and refresh the GPS tracking page")
            print("  2. Check browser console for JavaScript errors")

if __name__ == "__main__":
    main()