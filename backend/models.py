import sqlite3
from datetime import datetime

class History:
    def __init__(self, timestamp, device, ip, download, upload, action, remarks):
        self.timestamp = timestamp
        self.device = device
        self.ip = ip
        self.download = download
        self.upload = upload
        self.action = action
        self.remarks = remarks

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "device": self.device,
            "ip": self.ip,
            "download": self.download,
            "upload": self.upload,
            "action": self.action,
            "remarks": self.remarks
        }

class DeviceLimit:
    def __init__(self, device_name, ip, data_limit_mb, current_usage_mb=0, is_blocked=False):
        self.device_name = device_name
        self.ip = ip
        self.data_limit_mb = data_limit_mb
        self.current_usage_mb = current_usage_mb
        self.is_blocked = is_blocked

    def to_dict(self):
        return {
            "device_name": self.device_name,
            "ip": self.ip,
            "data_limit_mb": self.data_limit_mb,
            "current_usage_mb": round(self.current_usage_mb, 2),
            "is_blocked": self.is_blocked,
            "usage_percentage": round((self.current_usage_mb / self.data_limit_mb) * 100, 1) if self.data_limit_mb > 0 else 0
        }
