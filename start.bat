@echo off
title AI Video Highlight Clipper
echo ===================================================
echo     Starting AI Video Highlight Clipper Web App...
echo ===================================================
echo.
echo Opening Web App at http://localhost:5000
start http://localhost:5000
echo.
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" app.py
pause

