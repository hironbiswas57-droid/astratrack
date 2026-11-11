@echo off
setlocal
pushd "%~dp0.."
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" run_server.py --init-certs
if errorlevel 1 goto failed
echo Setup complete. Use commands\astratrack.bat to launch AstraTrack.
popd
exit /b 0
:failed
echo Setup failed. Review the command output above.
popd
exit /b 1
