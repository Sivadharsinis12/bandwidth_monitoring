import sqlite3
import os
from models import History
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
    # Create settings table for data limits
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE,
            setting_value TEXT,
            updated_at TEXT
        )
    ''')
    # Create bandwidth_usage table for tracking cumulative usage
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bandwidth_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            total_bytes REAL DEFAULT 0,
            is_blocked INTEGER DEFAULT 0
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
        'daily_peak': [daily_peak] * 5,  # Placeholder for 5 days
        'top_consumers': top_consumers,
        'total_bandwidth_30d': round(total_bandwidth_30d, 2)
    }

# Settings functions for data limits
def save_setting(key: str, value: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (setting_key, setting_value, updated_at)
        VALUES (?, ?, ?)
    ''', (key, value, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_setting(key: str) -> str:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT setting_value FROM settings WHERE setting_key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_all_settings():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT setting_key, setting_value FROM settings')
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def update_bandwidth_usage(bytes_used: float):
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bandwidth_usage (date, total_bytes, is_blocked)
        VALUES (?, ?, 0)
        ON CONFLICT(date) DO UPDATE SET total_bytes = total_bytes + ?
    ''', (today, bytes_used, bytes_used))
    conn.commit()
    conn.close()

def get_today_usage() -> float:
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT total_bytes FROM bandwidth_usage WHERE date = ?', (today,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0.0

def get_monthly_usage() -> float:
    first_of_month = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(total_bytes) FROM bandwidth_usage WHERE date >= ?', (first_of_month,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else 0.0

def set_blocked_status(blocked: bool):
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bandwidth_usage (date, total_bytes, is_blocked)
        VALUES (?, 0, ?)
        ON CONFLICT(date) DO UPDATE SET is_blocked = ?
    ''', (today, 1 if blocked else 0, 1 if blocked else 0))
    conn.commit()
    conn.close()

def is_blocked() -> bool:
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT is_blocked FROM bandwidth_usage WHERE date = ?', (today,))
    row = cursor.fetchone()
    conn.close()
    return row[0] == 1 if row else False

def reset_usage():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM bandwidth_usage')
    conn.commit()
    conn.close()
