import psutil
import time
import threading
from datetime import datetime
from database import save_history_entry, update_bandwidth_usage, get_setting, is_blocked, set_blocked_status
from models import History

# Global dictionary that the WebSocket will read from
device_stats = {
    "upload": 0,
    "download": 0,
    "total_bandwidth": 0,
    "devices": [],
    "is_blocked": False,
    "data_limit": {"daily_limit_gb": 0, "monthly_limit_gb": 0},
    "usage": {"daily_bytes": 0, "daily_gb": 0, "monthly_bytes": 0, "monthly_gb": 0}
}

# Global variable to track if network is blocked
network_blocked = False

# Bytes per GB
BYTES_PER_GB = 1024 * 1024 * 1024

def get_data_limits():
    """Get the current data limits from settings"""
    daily_limit = get_setting('daily_limit_gb')
    monthly_limit = get_setting('monthly_limit_gb')
    return {
        'daily_limit_gb': float(daily_limit) if daily_limit else 0,
        'monthly_limit_gb': float(monthly_limit) if monthly_limit else 0
    }

def get_current_usage():
    """Get current usage from database"""
    from database import get_today_usage, get_monthly_usage
    daily_bytes = get_today_usage()
    monthly_bytes = get_monthly_usage()
    return {
        'daily_bytes': daily_bytes,
        'daily_gb': round(daily_bytes / BYTES_PER_GB, 2),
        'monthly_bytes': monthly_bytes,
        'monthly_gb': round(monthly_bytes / BYTES_PER_GB, 2)
    }

def check_and_update_limit(bytes_up, bytes_down):
    """Check if data limit is reached and update usage"""
    global network_blocked
    
    limits = get_data_limits()
    usage = get_current_usage()
    
    total_bytes = bytes_up + bytes_down
    total_gb = total_bytes / BYTES_PER_GB
    
    # Check if limits are set and if they've been reached
    daily_limit = limits['daily_limit_gb']
    monthly_limit = limits['monthly_limit_gb']
    
    new_daily_gb = usage['daily_gb'] + total_gb
    new_monthly_gb = usage['monthly_gb'] + total_gb
    
    should_block = False
    
    # Check daily limit
    if daily_limit > 0 and new_daily_gb >= daily_limit:
        should_block = True
        network_blocked = True
    # Check monthly limit
    elif monthly_limit > 0 and new_monthly_gb >= monthly_limit:
        should_block = True
        network_blocked = True
    else:
        # Update usage
        if total_bytes > 0:
            update_bandwidth_usage(total_bytes)
        network_blocked = False
    
    # Update blocked status in database
    set_blocked_status(should_block)
    
    # Update global device_stats
    device_stats["is_blocked"] = should_block
    device_stats["data_limit"] = limits
    device_stats["usage"] = get_current_usage()
    
    return should_block

def start_monitor():
    def monitor():
        global device_stats
        # Get initial counters
        old = psutil.net_io_counters()
        history_counter = 0

        while True:
            time.sleep(1)
            new = psutil.net_io_counters()

            # Calculate differences in bytes
            bytes_up = new.bytes_sent - old.bytes_sent
            bytes_down = new.bytes_recv - old.bytes_recv

            # Check and update data limit
            is_blocked = check_and_update_limit(bytes_up, bytes_down)
            
            # Conversion: (Bytes * 8) / 1,000,000 = Mbps
            upload_mbps = (bytes_up * 8) / 1000000
            download_mbps = (bytes_down * 8) / 1000000
            total_mbps = upload_mbps + download_mbps

            # If blocked, return 0 speed
            if is_blocked:
                upload_mbps = 0
                download_mbps = 0
                total_mbps = 0

            # Update the global dictionary with rounded values
            device_stats["upload"] = round(upload_mbps, 2)
            device_stats["download"] = round(download_mbps, 2)
            device_stats["total_bandwidth"] = round(total_mbps, 2)

            # Keep your device list logic here
            device_stats["devices"] = [
                {"name": "Workstation-01", "ip": "192.168.1.10", "status": "Online"},
                {"name": "Mobile-Device", "ip": "192.168.1.15", "status": "Online"},
            ]

            # Save history every 60 seconds (1 minute)
            history_counter += 1
            if history_counter >= 60:
                history_entry = History(
                    timestamp=datetime.now().isoformat(),
                    device="System",
                    ip="127.0.0.1",
                    download=round(download_mbps, 2),
                    upload=round(upload_mbps, 2),
                    action="Monitor",
                    remarks="Periodic bandwidth log"
                )
                save_history_entry(history_entry)
                history_counter = 0

            old = new

    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
