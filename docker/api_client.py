"""
Brigade Electronics API Client
Handles authentication and API requests
"""
import hashlib
import requests
import time
import logging
from typing import Optional, Dict, Any, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import API_CONFIG

logger = logging.getLogger(__name__)

class BrigadeAPIClient:
    """Client for Brigade Electronics API"""
    
    def __init__(self):
        self.base_url = API_CONFIG.base_url
        self.username = API_CONFIG.username
        self.password = API_CONFIG.password
        self.timeout = API_CONFIG.timeout
        self.session = self._create_session()
        self._auth_key: Optional[str] = None
        self._key_expires_at: float = 0
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=API_CONFIG.retry_attempts,
            backoff_factor=API_CONFIG.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _md5_hash(self, text: str) -> str:
        """Generate MD5 hash for password"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _is_key_valid(self) -> bool:
        """Check if current auth key is still valid"""
        # Assume key expires after 1 hour if not specified
        return self._auth_key is not None and time.time() < self._key_expires_at
    
    def authenticate(self) -> bool:
        """
        Authenticate with the API and get verification key
        Returns True if successful, False otherwise
        """
        try:
            hashed_password = self._md5_hash(self.password)
            auth_url = f"{self.base_url}/api/v1/basic/key"
            
            params = {
                'username': self.username,
                'password': hashed_password
            }
            
            logger.info("Attempting API authentication...")
            response = self.session.get(auth_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('errorcode') == 200:
                self._auth_key = data.get('data', {}).get('key')
                # Set expiration to 50 minutes from now (assuming 1-hour validity)
                self._key_expires_at = time.time() + (50 * 60)
                logger.info("API authentication successful")
                return True
            else:
                logger.error(f"Authentication failed: {data}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication request failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            return False
    
    def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid authentication key"""
        if not self._is_key_valid():
            return self.authenticate()
        return True
    
    def get_devices(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch device list from the API
        Returns list of devices or None if failed
        """
        if not self._ensure_authenticated():
            logger.error("Failed to authenticate before fetching devices")
            return None
        
        try:
            devices_url = f"{self.base_url}/api/v1/basic/devices"
            params = {'key': self._auth_key}
            
            logger.info("Fetching device list from API...")
            response = self.session.get(devices_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('errorcode') == 200:
                devices = data.get('data', [])
                logger.info(f"Successfully fetched {len(devices)} devices")
                return devices
            else:
                logger.error(f"API returned error: {data}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch devices: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching devices: {e}")
            return None
    
    def get_device_groups(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch device groups from the API
        Returns list of groups or None if failed
        """
        if not self._ensure_authenticated():
            logger.error("Failed to authenticate before fetching groups")
            return None
        
        try:
            groups_url = f"{self.base_url}/api/v1/basic/groups"
            params = {'key': self._auth_key}
            
            logger.info("Fetching device groups from API...")
            response = self.session.get(groups_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('errorcode') == 200:
                groups = data.get('data', [])
                logger.info(f"Successfully fetched {len(groups)} groups")
                return groups
            else:
                logger.error(f"API returned error: {data}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch groups: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching groups: {e}")
            return None
    
    def get_alarm_details(self, terid_list: List[str], start_time: str, end_time: str, 
                         alarm_types: Optional[List[int]] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch alarm detail information for specific devices
        
        Args:
            terid_list: List of device terminal IDs
            start_time: Start time in format "YYYY-MM-DD HH:MM:SS"
            end_time: End time in format "YYYY-MM-DD HH:MM:SS" 
            alarm_types: Optional list of alarm type IDs to filter (empty for all)
            
        Returns:
            List of alarm details or None if failed
        """
        if not self._ensure_authenticated():
            logger.error("Failed to authenticate before fetching alarms")
            return None
        
        try:
            alarm_url = f"{self.base_url}/api/v1/basic/alarm/detail"
            
            payload = {
                "key": self._auth_key,
                "terid": terid_list,
                "type": alarm_types or [],  # Empty list for all alarm types
                "starttime": start_time,
                "endtime": end_time
            }
            
            logger.debug(f"Fetching alarm details for {len(terid_list)} devices...")
            response = self.session.post(
                alarm_url, 
                json=payload, 
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('errorcode') == 200:
                alarms = data.get('data', [])
                logger.debug(f"Successfully fetched {len(alarms)} alarm records")
                return alarms
            else:
                logger.error(f"API returned error for alarm details: {data}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch alarm details: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching alarm details: {e}")
            return None
    
    def get_alarm_details_for_device(self, terid: str, start_time: str, end_time: str) -> Optional[List[Dict[str, Any]]]:
        """
        Convenience method to fetch alarm details for a single device
        
        Args:
            terid: Device terminal ID
            start_time: Start time in format "YYYY-MM-DD HH:MM:SS"
            end_time: End time in format "YYYY-MM-DD HH:MM:SS"
            
        Returns:
            List of alarm details for the device or None if failed
        """
        return self.get_alarm_details([terid], start_time, end_time)