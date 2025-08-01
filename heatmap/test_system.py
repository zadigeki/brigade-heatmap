#!/usr/bin/env python3
"""
System Integration Test
Tests all components of the Brigade Monitoring System
"""
import time
import requests
import threading
from logging_config import setup_logging
import logging

logger = logging.getLogger(__name__)

def test_api_connection():
    """Test Brigade API connection"""
    print("🔍 Testing Brigade API connection...")
    try:
        from api_client import BrigadeAPIClient
        
        client = BrigadeAPIClient()
        if client.authenticate():
            print("✅ Brigade API authentication successful")
            
            # Test device fetch
            devices = client.get_devices()
            if devices:
                print(f"✅ Retrieved {len(devices)} devices from API")
                return True
            else:
                print("⚠️  No devices found in API")
                return False
        else:
            print("❌ Brigade API authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False

def test_database():
    """Test database operations"""
    print("🔍 Testing database operations...")
    try:
        from database import DatabaseManager
        
        db = DatabaseManager()
        
        # Test device operations
        devices = db.get_all_devices()
        print(f"✅ Database contains {len(devices)} devices")
        
        # Test GPS operations
        gps_positions = db.get_all_gps_positions()
        print(f"✅ Database contains {len(gps_positions)} GPS positions")
        
        # Test alarm operations
        alarms = db.get_recent_alarms(hours=24)
        print(f"✅ Database contains {len(alarms)} recent alarms")
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_gps_sync():
    """Test GPS synchronization"""
    print("🔍 Testing GPS synchronization...")
    try:
        from gps_tracking_service import GPSTrackingService
        
        service = GPSTrackingService()
        success = service.sync_gps_data()
        
        if success:
            print("✅ GPS synchronization successful")
            return True
        else:
            print("⚠️  GPS synchronization completed with warnings")
            return False
            
    except Exception as e:
        print(f"❌ GPS sync error: {e}")
        return False

def test_web_server():
    """Test web server endpoints"""
    print("🔍 Testing web server...")
    
    # Start web server in background
    def start_server():
        from web_server import AlarmHeatmapServer
        server = AlarmHeatmapServer(host='127.0.0.1', port=5001, debug=False)
        server.run()
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        base_url = "http://127.0.0.1:5001"
        
        # Test main page
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Main heatmap page accessible")
        else:
            print(f"⚠️  Main page returned status {response.status_code}")
        
        # Test GPS tracking page
        response = requests.get(f"{base_url}/gps-tracking", timeout=5)
        if response.status_code == 200:
            print("✅ GPS tracking page accessible")
        else:
            print(f"⚠️  GPS tracking page returned status {response.status_code}")
        
        # Test API endpoints
        endpoints = [
            "/api/devices",
            "/api/gps/positions",
            "/api/alarm-types",
            "/api/stats"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success', True):
                        print(f"✅ API endpoint {endpoint} working")
                    else:
                        print(f"⚠️  API endpoint {endpoint} returned error: {data.get('error', 'Unknown')}")
                else:
                    print(f"⚠️  API endpoint {endpoint} returned status {response.status_code}")
            except Exception as e:
                print(f"❌ API endpoint {endpoint} error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Web server test error: {e}")
        return False

def main():
    """Run all tests"""
    setup_logging('INFO')
    
    print("🚀 Brigade Electronics Monitoring System - Integration Test")
    print("=" * 60)
    
    tests = [
        ("API Connection", test_api_connection),
        ("Database Operations", test_database), 
        ("GPS Synchronization", test_gps_sync),
        ("Web Server", test_web_server)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to run.")
        print("\nTo start the system, run:")
        print("  python run_system.py")
        print("  or")
        print("  start_system.bat (Windows)")
        print("  ./start_system.sh (Linux/Mac)")
    else:
        print("⚠️  Some tests failed. Please check the configuration and try again.")
        print("\nCommon issues:")
        print("  - Check API credentials in config.py")
        print("  - Ensure Brigade API server is accessible")
        print("  - Verify all Python dependencies are installed")

if __name__ == "__main__":
    main()