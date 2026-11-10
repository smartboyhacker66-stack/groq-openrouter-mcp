@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"

set "PY=python"
where python >nul 2>&1 || set "PY=py"
where %PY% >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python nahi mila.
  echo https://www.python.org/downloads/ se install karo aur "Add python.exe to PATH" tick karna.
  pause
  exit /b 1
)

if not exist .env (
  echo.
  echo ===== Pehli baar setup: API keys =====
  echo Groq key yahan se banao      : https://console.groq.com/keys
  echo OpenRouter key yahan se banao: https://openrouter.ai/keys
  echo Jo key nahi hai us par sirf Enter dabao ^(baad me .env file me bhar sakte ho^).
  echo.
  set /p GROQ_KEY=Groq API key paste karo:
  set /p OR_KEY=OpenRouter API key paste karo:
  > .env echo GROQ_API_KEY=!GROQ_KEY!
  >> .env echo OPENROUTER_API_KEY=!OR_KEY!
  %PY% -c "import secrets;open('.env','a').write('MCP_SECRET='+secrets.token_urlsafe(24)+'\n')"
  echo.
  echo .env file ban gayi. Keys badalni ho to .env ko Notepad me kholo.
)

if not exist venv\Scripts\python.exe (
  echo Virtual environment ban raha hai...
  %PY% -m venv venv
)

echo Packages install ho rahe hain ^(pehli baar 1-2 minute lagte hain^)...
venv\Scripts\python.exe -m pip install -q -r requirements.txt
if errorlevel 1 (
  echo [ERROR] pip install fail hua. Internet check karo aur dobara chalao.
  pause
  exit /b 1
)

echo.
echo Server start ho raha hai. Ye window band mat karna.
venv\Scripts\python.exe server.py
pause
