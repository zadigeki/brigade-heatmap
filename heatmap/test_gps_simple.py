#!/usr/bin/env python3
"""
Simple test to verify GPS tracking functionality
"""
import time
import threading
import requests
from database import DatabaseManager

def test_gps_tracking():
    """Test if GPS tracking shows vehicles"""
    print("GPS Tracking Test")
    print("=" * 30)
    
    # Check database first
    print("1. Checking database...")
    db = DatabaseManager()
    devices = db.get_all_devices()
    gps_positions = db.get_all_gps_positions()
    
    print(f"   Devices in database: {len(devices)}")
    print(f"   GPS positions: {len(gps_positions)}")
    
    if len(gps_positions) == 0:
        print("   ERROR: No GPS data found. Run 'python sync_gps_once.py' first.")
        return False
    
    # Show GPS data
    print("\n2. GPS positions found:")
    for i, pos in enumerate(gps_positions):
        print(f"   {i+1}. {pos.get('car_license', pos.get('terid'))}: "
              f"Lat {pos.get('latitude'):.6f}, Lng {pos.get('longitude'):.6f}")
    
    # Start web server in background
    print("\n3. Starting web server...")
    
    def start_server():
        from web_server import AlarmHeatmapServer
        server = AlarmHeatmapServer(host='127.0.0.1', port=5002, debug=False)
        server.run()
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(3)  # Wait for server to start
    
    # Test API endpoint
    print("4. Testing GPS API endpoint...")
    try:
        response = requests.get('http://127.0.0.1:5002/api/gps/positions', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                positions = data.get('positions', [])
                print(f"   SUCCESS: API returned {len(positions)} GPS positions")
                
                if positions:
                    print("   Sample position:")
                    pos = positions[0]
                    print(f"     Vehicle: {pos.get('car_license', pos.get('terid'))}")
                    print(f"     Location: {pos.get('latitude')}, {pos.get('longitude')}")
                    print(f"     Speed: {pos.get('speed', 0)} km/h")
                else:
                    print("   WARNING: API returned success but no positions")
                    return False
            else:
                print(f"   ERROR: API returned error: {data.get('error')}")
                return False
        else:
            print(f"   ERROR: API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ERROR: Failed to test API: {e}")
        return False
    
    # Test GPS tracking page
    print("\n5. Testing GPS tracking page...")
    try:
        response = requests.get('http://127.0.0.1:5002/gps-tracking', timeout=10)
        if response.status_code == 200:
            content = response.text
            if 'leaflet' in content.lower() and 'gps' in content.lower():
                print("   SUCCESS: GPS tracking page loaded with map")
            else:
                print("   WARNING: GPS tracking page loaded but may be missing map components")
        else:
            print(f"   ERROR: GPS tracking page returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ERROR: Failed to test GPS tracking page: {e}")
        return False
    
    print("\n" + "=" * 30)
    print("SUCCESS: GPS tracking is working!")
    print("Navigate to: http://127.0.0.1:5002/gps-tracking")
    print(f"You should see {len(gps_positions)} vehicles on the map.")
    
    return True

if __name__ == "__main__":
    success = test_gps_tracking()
    if success:
        print("\nTo start the full system:")
        print("  python run_system.py")
        print("  or use start_system.bat / start_system.sh")
    else:
        print("\nThere were issues with GPS tracking. Check the errors above.")