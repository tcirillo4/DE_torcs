@echo OFF
cd "./TORCS/torcs_%1%"
start "wtorcs_%1%" /MIN wtorcs.exe -T "config/raceman/quickrace.xml"