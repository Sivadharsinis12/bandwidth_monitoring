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
