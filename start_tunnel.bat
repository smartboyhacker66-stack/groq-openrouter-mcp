@echo off
chcp 65001 >nul
cd /d "%~dp0"

where cloudflared >nul 2>&1
if errorlevel 1 (
  echo cloudflared install ho raha hai ^(sirf pehli baar^)...
  winget install --id Cloudflare.cloudflared -e --accept-source-agreements --accept-package-agreements
  echo.
  echo Install ho gaya to ye window band karo aur start_tunnel.bat DOBARA chalao.
  echo Agar winget na chale: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
  pause
  exit /b 0
)

echo.
echo Neeche jo https://....trycloudflare.com link aayega use copy karo.
echo Pehle start_server.bat chal raha hona chahiye. Ye window band mat karna.
echo.
cloudflared tunnel --url http://localhost:8000
pause
