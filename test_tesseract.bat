@echo off
echo Testing Tesseract OCR installation...

:: Check standard locations
set DEFAULT_PATH="C:\Program Files\Tesseract-OCR\tesseract.exe"
set ALTERNATE_PATH1="C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
set ALTERNATE_PATH2="C:\Tesseract-OCR\tesseract.exe"

if exist %DEFAULT_PATH% (
    set TESSERACT_PATH=%DEFAULT_PATH%
    goto :found
)

if exist %ALTERNATE_PATH1% (
    set TESSERACT_PATH=%ALTERNATE_PATH1%
    goto :found
)

if exist %ALTERNATE_PATH2% (
    set TESSERACT_PATH=%ALTERNATE_PATH2%
    goto :found
)

:: Prompt for custom path
echo Tesseract not found in standard locations.
echo Please enter the full path to tesseract.exe (including the filename):
set /p TESSERACT_PATH="> "

if not exist %TESSERACT_PATH% (
    echo ERROR: Tesseract not found at %TESSERACT_PATH%
    echo Please make sure Tesseract is installed correctly.
    goto :eof
)

:found
echo Tesseract found at %TESSERACT_PATH%
echo Checking version:
%TESSERACT_PATH% --version

echo.
echo If you see version information above, Tesseract is installed correctly!
echo Updating the .env file with the correct path...

:: Parse the path for .env file (escaping backslashes)
set ENV_PATH=%TESSERACT_PATH:\=\\%
:: Remove quotes for .env file
set ENV_PATH=%ENV_PATH:"=%

set ENV_FILE=backend\.env
set TESSERACT_LINE=TESSERACT_PATH=%ENV_PATH%

:: Check if the line already exists in the .env file
findstr /c:"TESSERACT_PATH=" %ENV_FILE% > nul
if %errorlevel% equ 0 (
    :: Update the existing line
    powershell -Command "(Get-Content %ENV_FILE%) -replace 'TESSERACT_PATH=.*', 'TESSERACT_PATH=%ENV_PATH%' | Set-Content %ENV_FILE%"
) else (
    :: Add the new line
    echo %TESSERACT_LINE% >> %ENV_FILE%
)

echo .env file updated.

echo.
echo Tesseract OCR is now ready to use with your Manga Translator application!
pause 