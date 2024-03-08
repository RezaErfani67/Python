@echo off
setlocal enabledelayedexpansion

rem Get the current directory path
set "CURRENT_DIRECTORY=%~dp0"

rem Get the parent directory path (one folder above)
for %%A in ("%CURRENT_DIRECTORY%\..") do set "PARENT_DIRECTORY=%%~fA"

rem Get the name of the current directory
rem for %%B in ("%CURRENT_DIRECTORY%") do set "CURRENT_FOLDER=%%~nxB"
for /f "delims=" %%A in ('cd') do set "CURRENT_FOLDER=%%~nxA"


rem Define the new directory path
set "NEW_PATH=%PARENT_DIRECTORY%\%CURRENT_FOLDER%2"

echo NEW_PATH: %NEW_PATH%

rem Define the old directory path
set "OLD_PATH=%CURRENT_DIRECTORY%env"

echo OLD_PATH: %OLD_PATH%

rem Check if the new directory exists, if not, create it
if not exist "%NEW_PATH%" (
    mkdir "%NEW_PATH%"
)

rem Copy all files from the current directory to the new directory
xcopy /s /e /y "%CURRENT_DIRECTORY%*" "%NEW_PATH%"

rem Update all paths in the new directory recursively
for /r "%NEW_PATH%" %%I in (*) do (
    if %%~dpI NEQ "%NEW_PATH%\" (
        call :update_script "%%I"
    )
)

echo Done.
pause
exit /b

:update_script
set "FILE_PATH=%~1"
set "TEMP_FILE=%TEMP%\temp.txt"

echo Updating file: %FILE_PATH%

rem Read the file content and replace old path with new path while preserving formatting
(
    for /f "usebackq delims=" %%J in ("%FILE_PATH%") do (
        set "LINE=%%J"
        rem Check if the line contains the old path and update it
        set "LINE=!LINE:%OLD_PATH%=%NEW_PATH%!"
        echo !LINE!
    )
) > "%TEMP_FILE%"

rem Overwrite the original file with the updated content
move /y "%TEMP_FILE%" "%FILE_PATH%" >nul

exit /b
