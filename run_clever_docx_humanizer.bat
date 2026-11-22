@echo off
setlocal enabledelayedexpansion
title Clever AI DOCX Humanizer

echo ========================================================
echo     Clever AI Document Humanizer (Auto Word Engine)
echo   Mode: Clear ^^& Structured (Academic Style)
echo ========================================================
echo.

if "%~1"=="" (
    echo [Prompt] You can drag and drop your .docx file onto this .bat file,
    echo          or enter the full path to your .docx file below:
    echo.
    set /p DOCX_PATH="Enter .docx path: "
) else (
    set DOCX_PATH=%~1
)

if not exist "!DOCX_PATH!" (
    echo [Error] File not found: !DOCX_PATH!
    pause
    exit /b 1
)

echo.
echo Starting Clever AI Humanizer engine...
python scripts\humanize_docx_clever.py "!DOCX_PATH!"

echo.
echo Press any key to exit.
pause >nul
