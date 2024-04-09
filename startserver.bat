@echo off
:Start
python -m flask --app Server/CSEFlask.py run
:: Wait 1 hour before restarting.
TIMEOUT /T 3600
GOTO:Start