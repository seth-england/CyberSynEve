@echo off
:Start
python -m flask --app "./Server/CSEFlask.py:Start(\"cse_mode_default\")" run --no-debugger --no-reload --host=0.0.0.0
:: Wait 1 hour before restarting.
TIMEOUT /T 3600
GOTO:Start