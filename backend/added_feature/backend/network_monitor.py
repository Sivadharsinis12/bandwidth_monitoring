import psutil
import time

previous = psutil.net_io_counters()

def get_network_speed():
    global previous
    current = psutil.net_io_counters()

    download = (current.bytes_recv - previous.bytes_recv) / 1024 / 1024
    upload = (current.bytes_sent - previous.bytes_sent) / 1024 / 1024

    previous = current

    return {
        "download": round(download, 2),
        "upload": round(upload, 2),
        "total_bandwidth": round((current.bytes_recv + current.bytes_sent) / (1024**4), 2)
    }


def get_devices():
    connections = psutil.net_connections()
    devices = []

    for conn in connections[:10]:
        devices.append({
            "device": f"Device-{conn.fd}",
            "ip": str(conn.laddr.ip) if conn.laddr else "N/A",
            "status": conn.status
        })

    return devices
