import threading
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from odoo import models, fields, api, tools
import logging

_logger = logging.getLogger(__name__)

class TeableAPIClientEnhanced:
    """Enhanced Teable API client with connection pooling"""
    
    def __init__(self, api_key: str, base_id: str):
        self.api_key = api_key
        self.base_id = base_id
        self.base_url = "https://api.teable.ai/v1"
        
        # Create session with connection pooling
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PATCH", "DELETE"]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,      # Connection pool size
            pool_maxsize=10,          # Maximum connections
            pool_block=False          # Don't block when pool is full
        )
        
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"ZerviAzia-Odoo/19.0"
        }

class TeableConnectionManager(models.AbstractModel):
    """
    Production-ready Teable connection manager for Zervi Azia
    
    This follows Odoo best practices and provides:
    1. Connection pooling
    2. Thread safety
    3. Configuration via Odoo settings
    4. Automatic reconnection
    5. Performance monitoring
    """
    
    _name = 'teable.connection.manager'
    _description = 'Teable Connection Manager'
    
    # Thread-safe connection storage
    _connections = {}
    _connection_lock = threading.RLock()
    
    @api.model
    def get_connection(self, force_new: bool = False):
        """
        Get Teable connection with pooling
        
        Args:
            force_new: Force new connection (for testing or reconnection)
            
        Returns:
            TeableAPIClientEnhanced instance or None
        """
        # Get credentials from Odoo parameters
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'teable.api_key', 
            default=''
        )
        base_id = self.env['ir.config_parameter'].sudo().get_param(
            'teable.base_id', 
            default=''
        )
        
        if not api_key or not base_id:
            _logger.error("Teable API credentials not configured")
            return None
        
        connection_key = f"{api_key}:{base_id}"
        
        with self._connection_lock:
            if force_new or connection_key not in self._connections:
                try:
                    # Create new connection
                    connection = TeableAPIClientEnhanced(api_key, base_id)
                    
                    # Test connection
                    if self._test_connection(connection):
                        self._connections[connection_key] = {
                            'connection': connection,
                            'created_at': fields.Datetime.now(),
                            'usage_count': 0,
                            'last_used': fields.Datetime.now()
                        }
                        _logger.info(f"Created new Teable connection: {connection_key}")
                    else:
                        _logger.error(f"Failed to connect to Teable: {connection_key}")
                        return None
                except Exception as e:
                    _logger.error(f"Error creating Teable connection: {e}")
                    return None
            
            # Update usage stats
            conn_data = self._connections[connection_key]
            conn_data['usage_count'] += 1
            conn_data['last_used'] = fields.Datetime.now()
            
            return conn_data['connection']
    
    def _test_connection(self, connection):
        """Test if connection is working"""
        try:
            # Simple API call to test connection
            url = f"{connection.base_url}/bases/{connection.base_id}/tables"
            response = connection.session.get(
                url, 
                headers=connection.headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            _logger.warning(f"Connection test failed: {e}")
            return False
    
    @api.model
    def get_connection_stats(self):
        """Get connection statistics"""
        with self._connection_lock:
            stats = {
                'total_connections': len(self._connections),
                'connections': []
            }
            
            for key, data in self._connections.items():
                stats['connections'].append({
                    'key': key,
                    'created_at': data['created_at'],
                    'usage_count': data['usage_count'],
                    'last_used': data['last_used']
                })
            
            return stats
    
    @api.model
    def cleanup_old_connections(self, hours_old: int = 24):
        """Clean up connections older than specified hours"""
        with self._connection_lock:
            current_time = fields.Datetime.now()
            removed = 0
            
            keys_to_remove = []
            for key, data in self._connections.items():
                age = (current_time - data['created_at']).total_seconds() / 3600
                if age > hours_old:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._connections[key]
                removed += 1
            
            _logger.info(f"Cleaned up {removed} old Teable connections")
            return removed
