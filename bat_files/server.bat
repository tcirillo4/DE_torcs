@echo OFF
cd "./TORCS/torcs_%1%"
start /MIN wtorcs.exe -T "config/raceman/quickrace.xml"