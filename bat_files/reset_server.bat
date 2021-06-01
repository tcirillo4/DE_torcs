@echo OFF
taskkill /F /IM "wtorcs.exe"
start /MIN py.exe -3.9 race_problem.py --nodes %1