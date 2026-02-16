import psutil
import time
import threading
from datetime import datetime
from database import save_history_entry
from models import History

# Global dictionary that the WebSocket will read from
device_stats = {
    "upload": 0,
    "download": 0,
    "total_bandwidth": 0,
    "devices": []
}

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

            # Conversion: (Bytes * 8) / 1,000,000 = Mbps
            upload_mbps = (bytes_up * 8) / 1000000
            download_mbps = (bytes_down * 8) / 1000000
            total_mbps = upload_mbps + download_mbps

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
