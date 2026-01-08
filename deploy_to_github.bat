@echo off
title Deploy to GitHub
echo Deploy Kerala Lottery Results to GitHub
echo =====================================
echo.
echo This script will help you deploy your code to GitHub.
echo.
echo Before running this script, please:
echo 1. Create a new repository on GitHub (https://github.com/new)
echo 2. Name it something like "kerala-lottery-results"
echo 3. Don't initialize it with a README
echo 4. Copy the repository URL
echo.
echo After creating the repository, enter the URL below:
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
echo Deployment complete!
echo Your code has been pushed to GitHub.
echo.
echo To enable automatic updates:
echo 1. Create a GitHub personal access token
echo 2. Set it as GITHUB_TOKEN environment variable
echo.
pause