import sqlite3
import os
from models import History

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
