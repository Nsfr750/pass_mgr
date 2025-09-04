@echo off
echo Setting up Password Manager Master Password
echo ====================================

set PYTHONPATH=%~dp0
"%PYTHONPATH%venv\Scripts\python.exe" "%PYTHONPATH%scripts\set_master_pw_cli.py"
