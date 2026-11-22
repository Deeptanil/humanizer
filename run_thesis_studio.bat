@echo off
setlocal enabledelayedexpansion
title Thesis Document Restructure Studio

echo ========================================================
echo       Thesis Restructure Studio & Chunker Engine
echo   Preserves Headings, Bold Titles, Lists ^& Tables
echo ========================================================
echo.

if "%~1"=="" (
    echo [Prompt] You can drag and drop your thesis .docx file onto this .bat,
    echo          or paste the path to your .docx file below:
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
echo Parsing document and starting Studio at http://127.0.0.1:5050 ...
python scripts\thesis_studio.py "!DOCX_PATH!"

pause
