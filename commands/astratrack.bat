@echo off
setlocal
echo AstraTrack command center
echo 1. Setup Python environment and local HTTPS certificate
echo 2. Start HTTPS
echo 3. Start HTTP (local fallback)
echo 4. Trust localhost HTTPS for this Windows user
echo 5. Remove localhost HTTPS trust
echo 6. Run tests
set /p choice=Select an action [1-6]: 
if "%choice%"=="1" (
  call "%~dp0setup.bat"
  exit /b
)
if "%choice%"=="2" (
  call "%~dp0start_https.bat"
  exit /b
)
if "%choice%"=="3" (
  call "%~dp0start_http.bat"
  exit /b
)
if "%choice%"=="4" (
  call "%~dp0trust_https.bat"
  exit /b
)
if "%choice%"=="5" (
  call "%~dp0remove_https_trust.bat"
  exit /b
)
if "%choice%"=="6" (
  call "%~dp0run_tests.bat"
  exit /b
)
echo Invalid selection.
exit /b 1
