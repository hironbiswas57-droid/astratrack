@echo off
setlocal
pushd "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo Run commands\setup.bat first.
  popd
  exit /b 1
)
".venv\Scripts\python.exe" run_server.py %*
set "result=%errorlevel%"
popd
exit /b %result%
