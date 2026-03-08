@echo off
cd /d c:\projects\bandwidth-system\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
