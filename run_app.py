import subprocess
import os

os.chdir("c:/projects/bandwidth-system/backend")
subprocess.run(["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"])
