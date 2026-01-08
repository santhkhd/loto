@echo off
echo Checking for GitHub token...
echo.
if "%GITHUB_TOKEN%"=="" (
    echo GitHub token is NOT set.
    echo.
    echo Please set your GitHub token using one of these methods:
    echo.
    echo Method 1 (Temporary - for current session only):
    echo    set GITHUB_TOKEN=your_token_here
    echo.
    echo Method 2 (Permanent - system-wide):
    echo    1. Press Win + R, type "sysdm.cpl", press Enter
    echo    2. Click "Advanced" tab
    echo    3. Click "Environment Variables"
    echo    4. Under "User variables", click "New"
    echo    5. Variable name: GITHUB_TOKEN
    echo    6. Variable value: your_actual_token_here
    echo    7. Click "OK" to save
) else (
    echo GitHub token is set!
    echo.
    echo The scheduler will automatically push updates to GitHub.
    echo Token preview: %GITHUB_TOKEN:~0,5%******
)
echo.
pause