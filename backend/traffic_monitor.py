import psutil
import time
import threading
from datetime import datetime
from database import save_history_entry, update_device_usage, get_device_limits, get_high_usage_devices, get_blocked_devices
from models import History

# Global dictionary that the WebSocket will read from
device_stats = {
    "upload": 0,
    "download": 0,
    "total_bandwidth": 0,
    "devices": [],
    "high_usage_alerts": 0,
    "blocked_devices": []
}

def start_monitor():
    def monitor():
        global device_stats
        # Get initial counters
        old = psutil.net_io_counters()
        history_counter = 0
        
        # Default devices to track
        known_devices = [
            {"name": "Workstation-01", "ip": "192.168.1.10"},
            {"name": "Mobile-Device", "ip": "192.168.1.15"},
        ]

        while True:
            time.sleep(1)
            new = psutil.net_io_counters()

            # Calculate differences in bytes
            bytes_up = new.bytes_sent - old.bytes_sent
            bytes_down = new.bytes_recv - old.bytes_recv

            # Conversion: (Bytes * 8) / 1,000,000 = Mbps
            upload_mbps = (bytes_up * 8) / 1000000
            download_mbps = (bytes_down * 8) / 1000000
            total_mbps = upload_mbps + download_mbps

            # Update the global dictionary with rounded values
            device_stats["upload"] = round(upload_mbps, 2)
            device_stats["download"] = round(download_mbps, 2)
            device_stats["total_bandwidth"] = round(total_mbps, 2)

            # Get device limits from database
            device_limits = get_device_limits()
            
            # Update devices list with status and usage
            devices_list = []
            for dev in known_devices:
                device_name = dev["name"]
                device_ip = dev["ip"]
                
                # Check if device has a limit set
                limit_info = next((d for d in device_limits if d["device_name"] == device_name), None)
                
                is_blocked = False
                usage_percent = 0
                if limit_info:
                    is_blocked = limit_info["is_blocked"]
                    if limit_info["data_limit_mb"] > 0:
                        usage_percent = (limit_info["current_usage_mb"] / limit_info["data_limit_mb"]) * 100
                
                devices_list.append({
                    "name": device_name,
                    "ip": device_ip,
                    "status": "Blocked" if is_blocked else "Online",
                    "is_blocked": is_blocked,
                    "usage_percent": round(usage_percent, 1)
                })
                
                # Update device usage (convert Mbps to MB for the interval)
                # Assuming 1 second interval, MB = Mbps / 8
                download_mb = download_mbps / 8
                upload_mb = upload_mbps / 8
                blocked, new_usage = update_device_usage(device_name, download_mb, upload_mb)
                
                if blocked:
                    print(f"Device {device_name} has been blocked due to data limit exceeded!")
            
            device_stats["devices"] = devices_list
            
            # Get high usage alerts (devices using >80% of their limit)
            high_usage = get_high_usage_devices(80.0)
            device_stats["high_usage_alerts"] = len(high_usage)
            
            # Get blocked devices
            blocked = get_blocked_devices()
            device_stats["blocked_devices"] = blocked

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
