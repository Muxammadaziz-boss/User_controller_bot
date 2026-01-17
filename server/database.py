# database.py - ASYNC SQLITE DATABASE (v3.0.5 Production)
"""
🚀 Production-Grade Async Database
- aiosqlite for non-blocking operations
- Connection pooling simulation
- WAL mode for concurrent access
- Proper error handling
"""

import aiosqlite
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class AsyncDatabase:
    """
    Fully Async SQLite Database Manager
    All operations are non-blocking - perfect for Telethon
    """
    
    def __init__(self, db_path: str = "server_bot.db"):
        self.db_path = Path(db_path)
        self.db: Optional[aiosqlite.Connection] = None
        self._connected = False
    
    # ==================== CONNECTION ====================
    async def connect(self) -> bool:
        """Connect to database asynchronously"""
        try:
            self.db = await aiosqlite.connect(
                str(self.db_path),
                isolation_level=None  # Auto-commit mode
            )
            
            # Enable WAL mode for better concurrency
            await self.db.execute("PRAGMA journal_mode=WAL")
            await self.db.execute("PRAGMA synchronous=NORMAL")
            await self.db.execute("PRAGMA cache_size=-64000")  # 64MB cache
            await self.db.execute("PRAGMA temp_store=MEMORY")
            await self.db.execute("PRAGMA foreign_keys=ON")
            
            # Row factory for dict-like access
            self.db.row_factory = aiosqlite.Row
            
            await self._create_tables()
            await self._create_indices()
            await self._run_migrations()
            
            self._connected = True
            logger.info(f"✅ Async database connected: {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connect error: {e}")
            return False
    
    async def disconnect(self):
        """Close database connection"""
        try:
            if self.db:
                await self.db.close()
                self.db = None
                self._connected = False
                logger.info("Database disconnected")
        except Exception as e:
            logger.error(f"Database disconnect error: {e}")
    
    @property
    def is_connected(self) -> bool:
        return self._connected and self.db is not None
    
    # ==================== SCHEMA ====================
    async def _create_tables(self):
        """Create all required tables"""
        try:
            # Devices table
            await self.db.execute('''
                CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY,
                    hostname TEXT,
                    username TEXT,
                    os TEXT,
                    os_version TEXT,
                    ip_address TEXT,
                    mac_address TEXT,
                    status TEXT DEFAULT 'offline',
                    version TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    heartbeat_count INTEGER DEFAULT 0,
                    total_uptime INTEGER DEFAULT 0,
                    metadata TEXT
                )
            ''')
            
            # Activity logs
            await self.db.execute('''
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    action TEXT,
                    details TEXT,
                    status TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices (device_id)
                )
            ''')
            
            # Commands history
            await self.db.execute('''
                CREATE TABLE IF NOT EXISTS commands_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    command TEXT,
                    result TEXT,
                    execution_time REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices (device_id)
                )
            ''')
            
            # Statistics
            await self.db.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT,
                    metric_value TEXT,
                    device_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Errors
            await self.db.execute('''
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    error_type TEXT,
                    error_message TEXT,
                    stack_trace TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            logger.info("Tables created/verified")
            
        except Exception as e:
            logger.error(f"Create tables error: {e}")
            raise
    
    async def _create_indices(self):
        """Create indices for frequent queries"""
        try:
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status)",
                "CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices(last_seen)",
                "CREATE INDEX IF NOT EXISTS idx_devices_hostname ON devices(hostname)",
                "CREATE INDEX IF NOT EXISTS idx_activity_device ON activity_logs(device_id)",
                "CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_logs(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_commands_device ON commands_history(device_id)",
                "CREATE INDEX IF NOT EXISTS idx_errors_device ON errors(device_id)",
            ]
            
            for sql in indices:
                await self.db.execute(sql)
            
            logger.info("Indices created/verified")
            
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    async def _run_migrations(self):
        """Simple migration system"""
        try:
            # Create schema_version table
            await self.db.execute('''
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            ''')
            
            # Get current version
            async with self.db.execute("SELECT MAX(version) FROM schema_version") as cursor:
                row = await cursor.fetchone()
                current_version = row[0] if row[0] else 0
            
            # Migrations
            migrations = [
                (1, "Initial schema", []),
                (2, "Add indices", []),
                (3, "Add signature column", [
                    "ALTER TABLE devices ADD COLUMN signature TEXT DEFAULT NULL"
                ]),
            ]
            
            for version, desc, sql_list in migrations:
                if version > current_version:
                    for sql in sql_list:
                        try:
                            await self.db.execute(sql)
                        except Exception as e:
                            if "duplicate column" not in str(e).lower():
                                raise
                    
                    await self.db.execute(
                        "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                        (version, desc)
                    )
                    logger.info(f"Migration {version}: {desc}")
                    
        except Exception as e:
            logger.warning(f"Migration warning: {e}")
    
    # ==================== DEVICES ====================
    async def add_device(self, device_id: str, device_info: Dict[str, Any]) -> bool:
        """Add or update device"""
        try:
            metadata = json.dumps(device_info, ensure_ascii=False)
            
            await self.db.execute('''
                INSERT OR REPLACE INTO devices 
                (device_id, hostname, username, os, os_version, ip_address, mac_address, 
                 status, version, last_seen, metadata, heartbeat_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        COALESCE((SELECT heartbeat_count FROM devices WHERE device_id = ?), 0) + 1)
            ''', (
                device_id,
                device_info.get('hostname', 'Unknown'),
                device_info.get('username', 'Unknown'),
                device_info.get('os', 'Unknown'),
                device_info.get('os_version', 'Unknown'),
                device_info.get('local_ip', 'Unknown'),
                device_info.get('mac_address', 'Unknown'),
                'online',
                device_info.get('version', '1.0.0'),
                datetime.now().isoformat(),
                metadata,
                device_id  # For subquery
            ))
            
            logger.info(f"Device added/updated: {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Add device error: {e}")
            return False
    
    async def update_heartbeat(self, device_id: str) -> bool:
        """Update device heartbeat timestamp"""
        try:
            await self.db.execute('''
                UPDATE devices 
                SET last_seen = ?, status = 'online', heartbeat_count = heartbeat_count + 1
                WHERE device_id = ?
            ''', (datetime.now().isoformat(), device_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Update heartbeat error: {e}")
            return False
    
    async def mark_offline(self, device_id: str) -> bool:
        """Mark device as offline"""
        try:
            await self.db.execute(
                "UPDATE devices SET status = 'offline' WHERE device_id = ?",
                (device_id,)
            )
            return True
        except Exception as e:
            logger.error(f"Mark offline error: {e}")
            return False
    
    async def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get single device"""
        try:
            async with self.db.execute(
                "SELECT * FROM devices WHERE device_id = ?", (device_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_device(row)
            return None
        except Exception as e:
            logger.error(f"Get device error: {e}")
            return None
    
    async def get_all_devices(self) -> List[Dict[str, Any]]:
        """Get all devices"""
        try:
            async with self.db.execute(
                "SELECT * FROM devices ORDER BY last_seen DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_device(row) for row in rows]
        except Exception as e:
            logger.error(f"Get all devices error: {e}")
            return []
    
    async def get_online_devices(self) -> List[Dict[str, Any]]:
        """Get online devices only"""
        try:
            async with self.db.execute(
                "SELECT * FROM devices WHERE status = 'online' ORDER BY last_seen DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_device(row) for row in rows]
        except Exception as e:
            logger.error(f"Get online devices error: {e}")
            return []
    
    def _row_to_device(self, row) -> Dict[str, Any]:
        """Convert row to device dict"""
        try:
            metadata = {}
            if row['metadata']:
                try:
                    metadata = json.loads(row['metadata'])
                except:
                    pass
            
            return {
                'device_id': row['device_id'],
                'hostname': row['hostname'],
                'username': row['username'],
                'os': row['os'],
                'os_version': row['os_version'],
                'ip_address': row['ip_address'],
                'mac_address': row['mac_address'],
                'status': row['status'],
                'version': row['version'],
                'first_seen': row['first_seen'],
                'last_seen': row['last_seen'],
                'heartbeat_count': row['heartbeat_count'],
                'total_uptime': row['total_uptime'],
                'metadata': metadata,
                # For compatibility
                'info': metadata
            }
        except Exception as e:
            logger.error(f"Row to device error: {e}")
            return {}
    
    # ==================== ACTIVITY LOGS ====================
    async def log_activity(self, device_id: str, action: str, 
                           details: str, status: str = 'success') -> bool:
        """Log activity"""
        try:
            await self.db.execute('''
                INSERT INTO activity_logs (device_id, action, details, status)
                VALUES (?, ?, ?, ?)
            ''', (device_id, action, details, status))
            return True
        except Exception as e:
            logger.error(f"Log activity error: {e}")
            return False
    
    async def get_activity_logs(self, device_id: str = None, 
                                 limit: int = 100) -> List[Dict[str, Any]]:
        """Get activity logs"""
        try:
            if device_id:
                sql = "SELECT * FROM activity_logs WHERE device_id = ? ORDER BY timestamp DESC LIMIT ?"
                params = (device_id, limit)
            else:
                sql = "SELECT * FROM activity_logs ORDER BY timestamp DESC LIMIT ?"
                params = (limit,)
            
            async with self.db.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Get activity logs error: {e}")
            return []
    
    # ==================== COMMANDS HISTORY ====================
    async def log_command(self, device_id: str, command: str, 
                          result: str, execution_time: float) -> bool:
        """Log command execution"""
        try:
            await self.db.execute('''
                INSERT INTO commands_history (device_id, command, result, execution_time)
                VALUES (?, ?, ?, ?)
            ''', (device_id, command, result, execution_time))
            return True
        except Exception as e:
            logger.error(f"Log command error: {e}")
            return False
    
    async def get_command_history(self, device_id: str = None, 
                                   limit: int = 50) -> List[Dict[str, Any]]:
        """Get command history"""
        try:
            if device_id:
                sql = "SELECT * FROM commands_history WHERE device_id = ? ORDER BY timestamp DESC LIMIT ?"
                params = (device_id, limit)
            else:
                sql = "SELECT * FROM commands_history ORDER BY timestamp DESC LIMIT ?"
                params = (limit,)
            
            async with self.db.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Get command history error: {e}")
            return []
    
    # ==================== ERRORS ====================
    async def log_error(self, device_id: str, error_type: str,
                        error_message: str, stack_trace: str = None) -> bool:
        """Log error"""
        try:
            await self.db.execute('''
                INSERT INTO errors (device_id, error_type, error_message, stack_trace)
                VALUES (?, ?, ?, ?)
            ''', (device_id, error_type, error_message, stack_trace))
            return True
        except Exception as e:
            logger.error(f"Log error failed: {e}")
            return False
    
    async def get_errors(self, device_id: str = None, 
                         limit: int = 50) -> List[Dict[str, Any]]:
        """Get error logs"""
        try:
            if device_id:
                sql = "SELECT * FROM errors WHERE device_id = ? ORDER BY timestamp DESC LIMIT ?"
                params = (device_id, limit)
            else:
                sql = "SELECT * FROM errors ORDER BY timestamp DESC LIMIT ?"
                params = (limit,)
            
            async with self.db.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Get errors failed: {e}")
            return []
    
    # ==================== DASHBOARD STATS ====================
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            stats = {}
            
            # Total devices
            async with self.db.execute("SELECT COUNT(*) FROM devices") as cursor:
                row = await cursor.fetchone()
                stats['total_devices'] = row[0]
            
            # Online devices
            async with self.db.execute(
                "SELECT COUNT(*) FROM devices WHERE status = 'online'"
            ) as cursor:
                row = await cursor.fetchone()
                stats['online_devices'] = row[0]
            
            # Total heartbeats
            async with self.db.execute(
                "SELECT COALESCE(SUM(heartbeat_count), 0) FROM devices"
            ) as cursor:
                row = await cursor.fetchone()
                stats['total_heartbeats'] = row[0]
            
            # Total commands
            async with self.db.execute("SELECT COUNT(*) FROM commands_history") as cursor:
                row = await cursor.fetchone()
                stats['total_commands'] = row[0]
            
            # Total errors
            async with self.db.execute("SELECT COUNT(*) FROM errors") as cursor:
                row = await cursor.fetchone()
                stats['total_errors'] = row[0]
            
            # Most active device
            async with self.db.execute('''
                SELECT device_id, hostname, heartbeat_count 
                FROM devices ORDER BY heartbeat_count DESC LIMIT 1
            ''') as cursor:
                row = await cursor.fetchone()
                if row:
                    stats['most_active_device'] = {
                        'device_id': row[0],
                        'hostname': row[1],
                        'heartbeats': row[2]
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"Get dashboard stats error: {e}")
            return {
                'total_devices': 0,
                'online_devices': 0,
                'total_heartbeats': 0,
                'total_commands': 0,
                'total_errors': 0
            }


# ==================== BACKWARD COMPATIBILITY ====================
# For code that still uses old Database class
Database = AsyncDatabase