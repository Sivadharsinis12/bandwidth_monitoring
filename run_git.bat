@echo off
cd c:\project\bandwidth_monitoring-main\bandwidth_monitoring-main
git init
git add .
git commit -m "Added data limit feature - set daily/monthly GB limits, track cumulative usage, and block network when limits reached"
git branch -M main
git remote add origin https://github.com/Sivadharsinis12/bandwidth_monitoring.git
git push -u origin main

