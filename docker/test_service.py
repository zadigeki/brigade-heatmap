"""
Test script for Brigade Electronics Device Sync Service
"""
import sys
import logging
from unittest.mock import patch, MagicMock
from logging_config import setup_logging
from api_client import BrigadeAPIClient
from database import DatabaseManager
from device_sync_service import DeviceSyncService
from alarm_sync_service import AlarmSyncService

def test_api_client():
    """Test API client functionality"""
    print("Testing API Client...")
    
    # Mock API responses
    mock_auth_response = {
        'errorcode': 200,
        'data': {'key': 'test_key_123'}
    }
    
    mock_devices_response = {
        'errorcode': 200,
        'data': [
            {
                'carlicense': 'TEST123',
                'terid': 'TEST001',
                'sim': '1234567890',
                'channel': 4,
                'platecolor': 1,
                'groupid': 1,
                'devicetype': '4',
                'linktype': '124'
            }
        ]
    }
    
    with patch('requests.Session.get') as mock_get:
        mock_get.side_effect = [
            MagicMock(json=lambda: mock_auth_response, raise_for_status=lambda: None),
            MagicMock(json=lambda: mock_devices_response, raise_for_status=lambda: None)
        ]
        
        client = BrigadeAPIClient()
        
        # Test authentication
        auth_success = client.authenticate()
        print(f"  Authentication test: {'PASS' if auth_success else 'FAIL'}")
        
        # Test device fetching
        devices = client.get_devices()
        print(f"  Device fetch test: {'PASS' if devices and len(devices) == 1 else 'FAIL'}")
        
    return auth_success and devices

def test_database():
    """Test database operations"""
    print("Testing Database Manager...")
    
    try:
        # Use in-memory database for testing
        import tempfile
        import os
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        # Patch the database path
        from config import DATABASE_CONFIG
        original_path = DATABASE_CONFIG.db_path
        DATABASE_CONFIG.db_path = temp_db.name
        
        db_manager = DatabaseManager()
        
        # Test device insertion
        test_device = {
            'carlicense': 'TEST123',
            'terid': 'TEST001',
            'sim': '1234567890',
            'channel': 4,
            'platecolor': 1,
            'groupid': 1,
            'devicetype': '4',
            'linktype': '124'
        }
        
        insert_success = db_manager.upsert_device(test_device)
        print(f"  Device insert test: {'PASS' if insert_success else 'FAIL'}")
        
        # Test device retrieval
        retrieved_device = db_manager.get_device_by_terid('TEST001')
        retrieve_success = retrieved_device is not None
        print(f"  Device retrieve test: {'PASS' if retrieve_success else 'FAIL'}")
        
        # Test device count
        count = db_manager.get_device_count()
        count_success = count == 1
        print(f"  Device count test: {'PASS' if count_success else 'FAIL'}")
        
        # Cleanup
        DATABASE_CONFIG.db_path = original_path
        os.unlink(temp_db.name)
        
        return insert_success and retrieve_success and count_success
        
    except Exception as e:
        print(f"  Database test failed: {e}")
        return False

def test_sync_service():
    """Test sync service"""
    print("Testing Device Sync Service...")
    
    mock_devices = [
        {
            'carlicense': 'TEST123',
            'terid': 'TEST001',
            'sim': '1234567890',
            'channel': 4,
            'platecolor': 1,
            'groupid': 1,
            'devicetype': '4',
            'linktype': '124'
        }
    ]
    
    with patch.object(BrigadeAPIClient, 'get_devices', return_value=mock_devices):
        with patch.object(DatabaseManager, 'upsert_devices_batch', 
                         return_value={'inserted': 1, 'updated': 0, 'failed': 0}):
            
            sync_service = DeviceSyncService()
            sync_success = sync_service.sync_devices()
            print(f"  Sync operation test: {'PASS' if sync_success else 'FAIL'}")
            
            # Test status
            status = sync_service.get_sync_status()
            status_success = 'last_sync_time' in status
            print(f"  Status check test: {'PASS' if status_success else 'FAIL'}")
            
            return sync_success and status_success

def test_alarm_sync_service():
    """Test alarm sync service"""
    print("Testing Alarm Sync Service...")
    
    mock_alarms = [
        {
            'terid': 'TEST001',
            'gpstime': '2023-01-01 12:00:00',
            'altitude': 100,
            'direction': 90,
            'gpslat': '40.7589',
            'gpslng': '-73.9851',
            'speed': 50,
            'recordspeed': 50,
            'state': 0,
            'time': '2023-01-01 12:00:01',
            'type': 4,
            'content': 'IO alarm',
            'cmdtype': 2
        }
    ]
    
    with patch.object(BrigadeAPIClient, 'get_alarm_details', return_value=mock_alarms):
        with patch.object(DatabaseManager, 'get_all_device_terids', return_value=['TEST001']):
            with patch.object(DatabaseManager, 'insert_alarms_batch', 
                             return_value={'inserted': 1, 'failed': 0}):
                
                alarm_service = AlarmSyncService()
                sync_success = alarm_service.sync_alarms()
                print(f"  Alarm sync operation test: {'PASS' if sync_success else 'FAIL'}")
                
                # Test status
                status = alarm_service.get_sync_status()
                status_success = 'last_sync_time' in status
                print(f"  Alarm status check test: {'PASS' if status_success else 'FAIL'}")
                
                return sync_success and status_success

def test_alarm_database():
    """Test alarm database operations"""
    print("Testing Alarm Database Operations...")
    
    try:
        # Use in-memory database for testing
        import tempfile
        import os
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        # Patch the database path
        from config import DATABASE_CONFIG
        original_path = DATABASE_CONFIG.db_path
        DATABASE_CONFIG.db_path = temp_db.name
        
        db_manager = DatabaseManager()
        
        # Test alarm insertion
        test_alarm = {
            'terid': 'TEST001',
            'gpstime': '2023-01-01 12:00:00',
            'altitude': 100,
            'direction': 90,
            'gpslat': '40.7589',
            'gpslng': '-73.9851',
            'speed': 50,
            'recordspeed': 50,
            'state': 0,
            'time': '2023-01-01 12:00:01',
            'type': 4,
            'content': 'IO alarm',
            'cmdtype': 2
        }
        
        insert_success = db_manager.insert_alarm(test_alarm)
        print(f"  Alarm insert test: {'PASS' if insert_success else 'FAIL'}")
        
        # Test alarm retrieval
        alarms = db_manager.get_alarms_by_terid('TEST001')
        retrieve_success = len(alarms) > 0
        print(f"  Alarm retrieve test: {'PASS' if retrieve_success else 'FAIL'}")
        
        # Test alarm count
        count = db_manager.get_alarm_count()
        count_success = count == 1
        print(f"  Alarm count test: {'PASS' if count_success else 'FAIL'}")
        
        # Cleanup
        DATABASE_CONFIG.db_path = original_path
        os.unlink(temp_db.name)
        
        return insert_success and retrieve_success and count_success
        
    except Exception as e:
        print(f"  Alarm database test failed: {e}")
        return False

def main():
    """Run all tests"""
    setup_logging('ERROR')  # Suppress logs during testing
    
    print("=== Brigade Electronics Device and Alarm Sync Service Tests ===\n")
    
    tests = [
        test_api_client,
        test_database,
        test_sync_service,
        test_alarm_database,
        test_alarm_sync_service
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  Test failed with exception: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=== Test Results ===")
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("All tests passed! ✅")
        return 0
    else:
        print("Some tests failed! ❌")
        return 1

if __name__ == "__main__":
    sys.exit(main())