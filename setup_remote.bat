@echo off
title Setup GitHub Remote
echo Setting up GitHub Remote Repository
echo ================================
echo.
echo Adding remote repository...
git remote add origin https://github.com/santhkhd/kerala_loto.git
echo.
echo Setting main branch...
git branch -M main
echo.
echo Remote setup complete!
echo.
echo To push your code to GitHub, run:
echo git push -u origin main
echo.
pause