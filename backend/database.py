import sqlite3
import os
from models import History, DeviceLimit
from datetime import datetime, timedelta

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'bandwidth.db')

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            device TEXT,
            ip TEXT,
            download REAL,
            upload REAL,
            action TEXT,
            remarks TEXT
        )
    ''')
    # Create device_limits table for data limit management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT UNIQUE,
            ip TEXT,
            data_limit_mb REAL,
            current_usage_mb REAL DEFAULT 0,
            is_blocked INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    # Create device_usage_log for tracking usage over time
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_usage_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT,
            ip TEXT,
            download_mb REAL,
            upload_mb REAL,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_history_entry(entry: History):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO history (timestamp, device, ip, download, upload, action, remarks)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (entry.timestamp, entry.device, entry.ip, entry.download, entry.upload, entry.action, entry.remarks))
    conn.commit()
    conn.close()

def get_history(limit=10):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, device, ip, download, upload, action, remarks FROM history ORDER BY timestamp DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [History(*row).to_dict() for row in rows]

def get_analytics():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    # Daily peak (simplified, assuming recent data)
    cursor.execute('SELECT MAX(download + upload) FROM history WHERE timestamp >= date("now", "-7 days")')
    daily_peak = cursor.fetchone()[0] or 0
    # Top consumers (simplified)
    cursor.execute('SELECT device, SUM(download + upload) as total FROM history GROUP BY device ORDER BY total DESC LIMIT 5')
    top_consumers = [{'name': row[0], 'usage': round(row[1], 2)} for row in cursor.fetchall()]
    # Total 30D
    cursor.execute('SELECT SUM(download + upload) FROM history WHERE timestamp >= date("now", "-30 days")')
    total_bandwidth_30d = cursor.fetchone()[0] or 0
    conn.close()
    return {
        'daily_peak': [daily_peak] * 5,
        'top_consumers': top_consumers,
        'total_bandwidth_30d': round(total_bandwidth_30d, 2)
    }

# Device Limit Management Functions
def set_device_limit(device_name: str, ip: str, data_limit_mb: float):
    """Set or update data limit for a device"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO device_limits (device_name, ip, data_limit_mb, current_usage_mb, is_blocked, created_at, updated_at)
        VALUES (?, ?, ?, 0, 0, ?, ?)
        ON CONFLICT(device_name) DO UPDATE SET
            data_limit_mb = excluded.data_limit_mb,
            updated_at = excluded.updated_at
    ''', (device_name, ip, data_limit_mb, now, now))
    conn.commit()
    conn.close()

def get_device_limits():
    """Get all device limits"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT device_name, ip, data_limit_mb, current_usage_mb, is_blocked FROM device_limits')
    rows = cursor.fetchall()
    conn.close()
    return [DeviceLimit(row[0], row[1], row[2], row[3], bool(row[4])).to_dict() for row in rows]

def get_device_limit(device_name: str):
    """Get limit for a specific device"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT device_name, ip, data_limit_mb, current_usage_mb, is_blocked FROM device_limits WHERE device_name = ?', (device_name,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return DeviceLimit(row[0], row[1], row[2], row[3], bool(row[4])).to_dict()
    return None

def update_device_usage(device_name: str, download_mb: float, upload_mb: float):
    """Update device usage and check if limit exceeded"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    # Get current usage and limit
    cursor.execute('SELECT current_usage_mb, data_limit_mb, is_blocked FROM device_limits WHERE device_name = ?', (device_name,))
    row = cursor.fetchone()
    
    if row:
        current_usage = row[0]
        data_limit = row[1]
        is_blocked = bool(row[2])
        
        new_usage = current_usage + download_mb + upload_mb
        
        # Check if limit exceeded
        if data_limit > 0 and new_usage >= data_limit and not is_blocked:
            # Block the device
            cursor.execute('UPDATE device_limits SET current_usage_mb = ?, is_blocked = 1, updated_at = ? WHERE device_name = ?', 
                          (new_usage, now, device_name))
            blocked = True
        else:
            cursor.execute('UPDATE device_limits SET current_usage_mb = ?, updated_at = ? WHERE device_name = ?', 
                          (new_usage, now, device_name))
            blocked = is_blocked
        
        # Log the usage
        cursor.execute('''
            INSERT INTO device_usage_log (device_name, ip, download_mb, upload_mb, timestamp)
            VALUES (?, (SELECT ip FROM device_limits WHERE device_name = ?), ?, ?, ?)
        ''', (device_name, device_name, download_mb, upload_mb, now))
        
        conn.commit()
        conn.close()
        return blocked, new_usage
    else:
        conn.close()
        return False, 0

def unblock_device(device_name: str):
    """Unblock a device and reset usage"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('UPDATE device_limits SET is_blocked = 0, current_usage_mb = 0, updated_at = ? WHERE device_name = ?', 
                  (now, device_name))
    conn.commit()
    conn.close()

def get_high_usage_devices(threshold_percent: float = 80.0):
    """Get devices that have exceeded the threshold percentage of their data limit"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT device_name, ip, data_limit_mb, current_usage_mb, is_blocked,
               (current_usage_mb / data_limit_mb * 100) as usage_percent
        FROM device_limits 
        WHERE data_limit_mb > 0 AND (current_usage_mb / data_limit_mb * 100) >= ?
        ORDER BY usage_percent DESC
    ''', (threshold_percent,))
    rows = cursor.fetchall()
    conn.close()
    return [{
        'device_name': row[0],
        'ip': row[1],
        'data_limit_mb': row[2],
        'current_usage_mb': round(row[3], 2),
        'is_blocked': bool(row[4]),
        'usage_percentage': round(row[5], 1)
    } for row in rows]

def get_blocked_devices():
    """Get all blocked devices"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT device_name, ip, data_limit_mb, current_usage_mb, is_blocked FROM device_limits WHERE is_blocked = 1')
    rows = cursor.fetchall()
    conn.close()
    return [DeviceLimit(row[0], row[1], row[2], row[3], bool(row[4])).to_dict() for row in rows]
