@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

REM Usage: deploy_to_render.bat [repo-name]
set "REPO=%~1"
if "%REPO%"=="" set "REPO=groq-openrouter-mcp"

where git >nul 2>&1
if errorlevel 1 (
  echo [ERROR] git nahi mila. Install karo: https://git-scm.com/download/win
  pause
  exit /b 1
)
where gh >nul 2>&1
if errorlevel 1 (
  echo [ERROR] GitHub CLI ^(gh^) nahi mila. Install karo: https://cli.github.com
  pause
  exit /b 1
)

gh auth status >nul 2>&1
if errorlevel 1 (
  echo GitHub login karna hoga. Jo options aaye unme GitHub.com aur HTTPS chuno.
  gh auth login
)
gh auth status >nul 2>&1
if errorlevel 1 (
  echo [ERROR] GitHub login nahi hua.
  pause
  exit /b 1
)

for /f "delims=" %%u in ('gh api user --jq .login') do set "GHUSER=%%u"
if "%GHUSER%"=="" (
  echo [ERROR] GitHub username nahi mila.
  pause
  exit /b 1
)

REM git commit ke liye naam/email na ho to apne aap set karo
set "GN="
for /f "delims=" %%n in ('git config user.name') do set "GN=%%n"
if "%GN%"=="" git config user.name "%GHUSER%"
set "GE="
for /f "delims=" %%e in ('git config user.email') do set "GE=%%e"
if "%GE%"=="" git config user.email "%GHUSER%@users.noreply.github.com"

if not exist .git git init -b main
git branch -M main
git add .
git commit -m "Initial commit: FastMCP Groq+OpenRouter+kotlinc server"

git remote get-url origin >nul 2>&1
if errorlevel 1 (
  echo Repo bana raha hoon: %GHUSER%/%REPO% ^(public, .env push nahi hoti^)
  gh repo create "%REPO%" --public --source=. --remote=origin --push
  if errorlevel 1 (
    echo [ERROR] Repo nahi bana. Is naam se pehle se ho to doosra naam do: deploy_to_render.bat mera-naam
    pause
    exit /b 1
  )
) else (
  git push -u origin main
  if errorlevel 1 (
    echo [ERROR] Push fail hua.
    pause
    exit /b 1
  )
)

set "REPO_URL=https://github.com/%GHUSER%/%REPO%"
echo.
echo GitHub par code pahunch gaya: %REPO_URL%
echo.
echo ===== Ab Render par ^(browser khul raha hai^) =====
echo 1. Render me login/sign-up karo ^(GitHub se ho jata hai^)
echo 2. Page par GROQ_API_KEY aur OPENROUTER_API_KEY maangega - yahin keys paste karo
echo 3. "Deploy Blueprint" / "Apply" dabao, 5-10 minute ruko
echo 4. Service ke Environment tab me MCP_SECRET copy karo
echo.
start "" "https://render.com/deploy?repo=%REPO_URL%"
pause
