@echo off
title Setup and Push to GitHub
echo Setup and Push Kerala Lottery Results to GitHub
echo =============================================
echo.
echo This script will help you set up your GitHub repository and push all code.
echo.
echo Step 1: Please enter your GitHub repository URL
echo (Format: https://github.com/yourusername/repository-name.git)
echo.
set /p repo_url="Enter your GitHub repository URL: "
echo.
echo Setting up Git remote...
git remote add origin %repo_url%
echo.
echo Setting main branch...
git branch -M main
echo.
echo Pushing to GitHub...
git push -u origin main
echo.
echo Verifying push...
git status
echo.
echo Setup and push complete!
echo Your code has been pushed to GitHub.
echo.
echo To verify your GitHub token is working:
echo 1. Run check_github_token.bat
echo 2. Start the scheduler with run_lottery_scheduler.bat
echo.
pause