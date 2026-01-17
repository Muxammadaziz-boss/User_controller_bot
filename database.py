# database.py - SQLITE DATABASE (v3.0.5)
"""
Database management:
- Device storage
- Activity logs
- Statistics
- History tracking
- WAL journaling (v3.0.5)
- Migration system (v3.0.5)
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ==================== DATABASE ====================
class Database:
    def __init__(self, db_file="bot_data.db"):
        self.db_file = Path(db_file)
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Database'ga ulanish"""
        try:
            self.conn = sqlite3.connect(str(self.db_file), check_same_thread=False)
            self.cursor = self.conn.cursor()
            
            # v3.0.5: WAL mode va optimizatsiyalar
            self._setup_pragmas()
            
            self.create_tables()
            self._create_indices()  # v3.0.5
            self._run_migrations()  # v3.0.5
            
            logger.info(f"Database connected: {self.db_file}")
            return True
        except Exception as e:
            logger.error(f"Database connect error: {e}")
            return False
    
    def _setup_pragmas(self):
        """v3.0.5: SQLite optimizatsiyalari"""
        try:
            # WAL mode - yaxshi concurrent read/write
            self.conn.execute("PRAGMA journal_mode=WAL")
            # Synchronous normal - balanced safety/speed
            self.conn.execute("PRAGMA synchronous=NORMAL")
            # Cache size (negative = KB)
            self.conn.execute("PRAGMA cache_size=-64000")  # 64MB
            # Temp store in memory
            self.conn.execute("PRAGMA temp_store=MEMORY")
            # Enable foreign keys
            self.conn.execute("PRAGMA foreign_keys=ON")
            logger.info("SQLite pragmas set (WAL mode enabled)")
        except Exception as e:
            logger.warning(f"Pragma setup warning: {e}")
    
    def disconnect(self):
        """Ulanishni yopish"""
        try:
            if self.conn:
                self.conn.close()
            logger.info("Database disconnected")
        except Exception as e:
            logger.error(f"Database disconnect error: {e}")
    
    def create_tables(self):
        """Tablelarni yaratish"""
        try:
            # Devices table
            self.cursor.execute('''
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
            
            # Activity logs table
            self.cursor.execute('''
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
            
            # Commands history table
            self.cursor.execute('''
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
            
            # Statistics table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT,
                    metric_value TEXT,
                    device_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Errors table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    error_type TEXT,
                    error_message TEXT,
                    stack_trace TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.conn.commit()
            logger.info("Tables created/verified")
            
        except Exception as e:
            logger.error(f"Create tables error: {e}")
    
    def _create_indices(self):
        """v3.0.5: Indekslar yaratish - tez qidirish uchun"""
        try:
            indices = [
                # Devices - tez-tez qidiriladigan ustunlar
                "CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status)",
                "CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices(last_seen)",
                "CREATE INDEX IF NOT EXISTS idx_devices_hostname ON devices(hostname)",
                
                # Activity logs - device va timestamp bo'yicha
                "CREATE INDEX IF NOT EXISTS idx_activity_device ON activity_logs(device_id)",
                "CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_logs(timestamp)",
                
                # Commands - device va timestamp
                "CREATE INDEX IF NOT EXISTS idx_commands_device ON commands_history(device_id)",
                "CREATE INDEX IF NOT EXISTS idx_commands_timestamp ON commands_history(timestamp)",
                
                # Errors - device va timestamp
                "CREATE INDEX IF NOT EXISTS idx_errors_device ON errors(device_id)",
                "CREATE INDEX IF NOT EXISTS idx_errors_timestamp ON errors(timestamp)",
            ]
            
            for idx_sql in indices:
                self.cursor.execute(idx_sql)
            
            self.conn.commit()
            logger.info("Indices created/verified")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    def _run_migrations(self):
        """v3.0.5: Oddiy migration system"""
        try:
            # Migration version table yaratish
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            ''')
            
            # Joriy versiyani olish
            self.cursor.execute("SELECT MAX(version) FROM schema_version")
            result = self.cursor.fetchone()
            current_version = result[0] if result[0] else 0
            
            # Migrations ro'yxati
            migrations = [
                # (version, description, sql_list)
                (1, "Initial schema", []),  # Tables allaqachon yaratilgan
                (2, "Add indices", []),     # Indices allaqachon yaratilgan
                (3, "Add signature column to devices", [
                    "ALTER TABLE devices ADD COLUMN signature TEXT DEFAULT NULL",
                ]),
            ]
            
            # Yangi migratsiyalarni bajarish
            for version, desc, sql_list in migrations:
                if version > current_version:
                    for sql in sql_list:
                        try:
                            self.cursor.execute(sql)
                        except sqlite3.OperationalError as e:
                            if "duplicate column" not in str(e).lower():
                                raise
                    
                    self.cursor.execute(
                        "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                        (version, desc)
                    )
                    logger.info(f"Migration {version}: {desc}")
            
            self.conn.commit()
        except Exception as e:
            logger.warning(f"Migration warning: {e}")
    
    # ==================== DEVICES ====================
    def add_device(self, device_id, device_info):
        """Device qo'shish"""
        try:
            metadata = json.dumps(device_info)
            
            self.cursor.execute('''
                INSERT OR REPLACE INTO devices 
                (device_id, hostname, username, os, os_version, ip_address, mac_address, 
                 status, version, last_seen, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                metadata
            ))
            
            self.conn.commit()
            logger.info(f"Device added: {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Add device error: {e}")
            return False
    
    def update_device_heartbeat(self, device_id):
        """Device heartbeat yangilash"""
        try:
            self.cursor.execute('''
                UPDATE devices 
                SET last_seen = ?, status = 'online', heartbeat_count = heartbeat_count + 1
                WHERE device_id = ?
            ''', (datetime.now().isoformat(), device_id))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Update heartbeat error: {e}")
            return False
    
    def mark_device_offline(self, device_id):
        """Device'ni offline qilish"""
        try:
            self.cursor.execute('''
                UPDATE devices SET status = 'offline' WHERE device_id = ?
            ''', (device_id,))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Mark offline error: {e}")
            return False
    
    def get_device(self, device_id):
        """Device ma'lumotini olish"""
        try:
            self.cursor.execute('''
                SELECT * FROM devices WHERE device_id = ?
            ''', (device_id,))
            
            row = self.cursor.fetchone()
            if row:
                return self._row_to_device_dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Get device error: {e}")
            return None
    
    def get_all_devices(self):
        """Barcha device'lar"""
        try:
            self.cursor.execute('SELECT * FROM devices ORDER BY last_seen DESC')
            rows = self.cursor.fetchall()
            return [self._row_to_device_dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Get all devices error: {e}")
            return []
    
    def get_online_devices(self):
        """Online device'lar"""
        try:
            self.cursor.execute('''
                SELECT * FROM devices WHERE status = 'online' ORDER BY last_seen DESC
            ''')
            rows = self.cursor.fetchall()
            return [self._row_to_device_dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Get online devices error: {e}")
            return []
    
    def _row_to_device_dict(self, row):
        """Row'ni dict'ga"""
        return {
            'device_id': row[0],
            'hostname': row[1],
            'username': row[2],
            'os': row[3],
            'os_version': row[4],
            'ip_address': row[5],
            'mac_address': row[6],
            'status': row[7],
            'version': row[8],
            'first_seen': row[9],
            'last_seen': row[10],
            'heartbeat_count': row[11],
            'total_uptime': row[12],
            'metadata': json.loads(row[13]) if row[13] else {}
        }
    
    # ==================== ACTIVITY LOGS ====================
    def log_activity(self, device_id, action, details, status='success'):
        """Activity log qo'shish"""
        try:
            self.cursor.execute('''
                INSERT INTO activity_logs (device_id, action, details, status)
                VALUES (?, ?, ?, ?)
            ''', (device_id, action, details, status))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Log activity error: {e}")
            return False
    
    def get_activity_logs(self, device_id=None, limit=100):
        """Activity log'larni olish"""
        try:
            if device_id:
                self.cursor.execute('''
                    SELECT * FROM activity_logs 
                    WHERE device_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (device_id, limit))
            else:
                self.cursor.execute('''
                    SELECT * FROM activity_logs 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
            
            rows = self.cursor.fetchall()
            return [{
                'id': row[0],
                'device_id': row[1],
                'action': row[2],
                'details': row[3],
                'status': row[4],
                'timestamp': row[5]
            } for row in rows]
            
        except Exception as e:
            logger.error(f"Get activity logs error: {e}")
            return []
    
    # ==================== COMMANDS HISTORY ====================
    def log_command(self, device_id, command, result, execution_time):
        """Command history'ga qo'shish"""
        try:
            self.cursor.execute('''
                INSERT INTO commands_history (device_id, command, result, execution_time)
                VALUES (?, ?, ?, ?)
            ''', (device_id, command, result, execution_time))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Log command error: {e}")
            return False
    
    def get_command_history(self, device_id=None, limit=50):
        """Command history"""
        try:
            if device_id:
                self.cursor.execute('''
                    SELECT * FROM commands_history 
                    WHERE device_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (device_id, limit))
            else:
                self.cursor.execute('''
                    SELECT * FROM commands_history 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
            
            rows = self.cursor.fetchall()
            return [{
                'id': row[0],
                'device_id': row[1],
                'command': row[2],
                'result': row[3],
                'execution_time': row[4],
                'timestamp': row[5]
            } for row in rows]
            
        except Exception as e:
            logger.error(f"Get command history error: {e}")
            return []
    
    # ==================== STATISTICS ====================
    def log_statistic(self, metric_name, metric_value, device_id=None):
        """Statistika qo'shish"""
        try:
            self.cursor.execute('''
                INSERT INTO statistics (metric_name, metric_value, device_id)
                VALUES (?, ?, ?)
            ''', (metric_name, str(metric_value), device_id))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Log statistic error: {e}")
            return False
    
    def get_statistics(self, metric_name=None, device_id=None, limit=100):
        """Statistika olish"""
        try:
            query = 'SELECT * FROM statistics WHERE 1=1'
            params = []
            
            if metric_name:
                query += ' AND metric_name = ?'
                params.append(metric_name)
            
            if device_id:
                query += ' AND device_id = ?'
                params.append(device_id)
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            return [{
                'id': row[0],
                'metric_name': row[1],
                'metric_value': row[2],
                'device_id': row[3],
                'timestamp': row[4]
            } for row in rows]
            
        except Exception as e:
            logger.error(f"Get statistics error: {e}")
            return []
    
    # ==================== ERRORS ====================
    def log_error(self, device_id, error_type, error_message, stack_trace=None):
        """Error log qo'shish"""
        try:
            self.cursor.execute('''
                INSERT INTO errors (device_id, error_type, error_message, stack_trace)
                VALUES (?, ?, ?, ?)
            ''', (device_id, error_type, error_message, stack_trace))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Log error failed: {e}")
            return False
    
    def get_errors(self, device_id=None, limit=50):
        """Error log'lar"""
        try:
            if device_id:
                self.cursor.execute('''
                    SELECT * FROM errors 
                    WHERE device_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (device_id, limit))
            else:
                self.cursor.execute('''
                    SELECT * FROM errors 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
            
            rows = self.cursor.fetchall()
            return [{
                'id': row[0],
                'device_id': row[1],
                'error_type': row[2],
                'error_message': row[3],
                'stack_trace': row[4],
                'timestamp': row[5]
            } for row in rows]
            
        except Exception as e:
            logger.error(f"Get errors failed: {e}")
            return []
    
    # ==================== ANALYTICS ====================
    def get_dashboard_stats(self):
        """Dashboard statistikasi"""
        try:
            stats = {}
            
            # Total devices
            self.cursor.execute('SELECT COUNT(*) FROM devices')
            stats['total_devices'] = self.cursor.fetchone()[0]
            
            # Online devices
            self.cursor.execute("SELECT COUNT(*) FROM devices WHERE status = 'online'")
            stats['online_devices'] = self.cursor.fetchone()[0]
            
            # Total heartbeats
            self.cursor.execute('SELECT SUM(heartbeat_count) FROM devices')
            stats['total_heartbeats'] = self.cursor.fetchone()[0] or 0
            
            # Total commands
            self.cursor.execute('SELECT COUNT(*) FROM commands_history')
            stats['total_commands'] = self.cursor.fetchone()[0]
            
            # Total errors
            self.cursor.execute('SELECT COUNT(*) FROM errors')
            stats['total_errors'] = self.cursor.fetchone()[0]
            
            # Most active device
            self.cursor.execute('''
                SELECT device_id, hostname, heartbeat_count 
                FROM devices 
                ORDER BY heartbeat_count DESC 
                LIMIT 1
            ''')
            row = self.cursor.fetchone()
            if row:
                stats['most_active_device'] = {
                    'device_id': row[0],
                    'hostname': row[1],
                    'heartbeats': row[2]
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Get dashboard stats error: {e}")
            return {}