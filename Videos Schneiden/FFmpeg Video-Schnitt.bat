@echo off
title FFmpeg Video-Schnitt Tool
chcp 65001 >nul
color 0A

:: ----------------------------------------
::   FFmpeg aus Unterordner verwenden
:: ----------------------------------------
set "FFMPEG_DIR=%~dp0FFmpeg"
set "FFMPEG=%FFMPEG_DIR%\ffmpeg.exe"
set "FFPROBE=%FFMPEG_DIR%\ffprobe.exe"

:: Prüfen ob FFmpeg-Ordner existiert
if not exist "%FFMPEG_DIR%" (
    echo [FEHLER] Der Ordner "FFmpeg" wurde nicht gefunden!
    echo Bitte erstellen Sie einen Unterordner "FFmpeg" im aktuellen Verzeichnis.
    echo.
    pause
    exit /b 1
)

:: Prüfen ob ffmpeg.exe im FFmpeg-Ordner existiert
if not exist "%FFMPEG%" (
    echo [FEHLER] ffmpeg.exe wurde im FFmpeg-Ordner nicht gefunden!
    echo Bitte stellen Sie sicher, dass ffmpeg.exe im Ordner "FFmpeg" liegt.
    echo Erwarteter Pfad: %FFMPEG%
    echo.
    pause
    exit /b 1
)

echo [INFO] FFmpeg gefunden in: %FFMPEG_DIR%
if exist "%FFPROBE%" (
    echo [INFO] FFprobe gefunden - verwende erweiterte Funktionen
) else (
    echo [INFO] FFprobe nicht gefunden - verwende Basis-Funktionen
)
echo.

:: ----------------------------------------
::   Drag ^& Drop Unterstützung
:: ----------------------------------------
set "dropped_file="
if not "%~1"=="" (
    set "dropped_file=%~1"
    echo [INFO] Datei per Drag ^& Drop empfangen: %~nx1
    echo.
)
timeout /t 2 >nul

:: ----------------------------------------
::   FFmpeg Video-Schnitt Menü
:: ----------------------------------------

:START
cls
echo =====================================
echo     FFmpeg Video-Schnitt Tool
echo =====================================
echo.
echo Wähle eine Option:
echo [1] Anfang abschneiden
echo [2] Mittleren Teil (oder dazwischen) abschneiden
echo [3] Endstück abschneiden
echo [4] Beenden
echo.

set /p "choice=Deine Auswahl: "

if "%choice%"=="1" goto ANFANG
if "%choice%"=="2" goto MITTE
if "%choice%"=="3" goto ENDE
if "%choice%"=="4" exit
echo Ungültige Auswahl!
pause
goto START

:ANFANG
echo.
if not "%dropped_file%"=="" (
    set "input=%dropped_file%"
    echo Verwende Drag ^& Drop Datei: %dropped_file%
) else (
    set "input="
    echo Tipp: Du kannst auch Dateien per Drag ^& Drop ins Fenster ziehen!
    set /p "input=Bitte gib den Dateinamen (mit Endung) ein: "
)
set "input=%input:"=%"

if not exist "%input%" (
    echo.
    echo [FEHLER] Datei "%input%" wurde nicht gefunden!
    pause
    goto START
)

call :GetFileInfo "%input%"
echo.

set /p "start=Zeitpunkt ab dem behalten werden soll (z.B. 00:01:41): "
set "output=%dir%%basename%_anfang_geschnitten%ext%"
echo.
echo Ausgabedatei wird sein: %output%
set /p "custom_output=Anderen Namen verwenden? (Enter für Standard): "
if not "%custom_output%"=="" set "output=%custom_output%"

echo.
echo Schneide Anfang ab...
"%FFMPEG%" -i "%input%" -ss %start% -c copy "%output%"
if errorlevel 1 (
    echo [FEHLER] Beim Schneiden ist ein Fehler aufgetreten!
) else (
    echo ✅ Fertig! Datei gespeichert als: "%output%"
)
set "dropped_file="
pause
goto START

:MITTE
echo.
if not "%dropped_file%"=="" (
    set "input=%dropped_file%"
    echo Verwende Drag ^& Drop Datei: %dropped_file%
) else (
    set "input="
    echo Tipp: Du kannst auch Dateien per Drag ^& Drop ins Fenster ziehen!
    set /p "input=Bitte gib den Dateinamen (mit Endung) ein: "
)
set "input=%input:"=%"

if not exist "%input%" (
    echo.
    echo [FEHLER] Datei "%input%" wurde nicht gefunden!
    pause
    goto START
)

call :GetFileInfo "%input%"
echo.

set /p "start=Startzeit des zu löschenden Bereichs (z.B. 00:01:41): "
set /p "end=Endzeit des zu löschenden Bereichs (z.B. 00:02:03): "
set "output=%dir%%basename%_mitte_geschnitten%ext%"
echo.
echo Ausgabedatei wird sein: %output%
set /p "custom_output=Anderen Namen verwenden? (Enter für Standard): "
if not "%custom_output%"=="" set "output=%custom_output%"

:: Zeit in Sekunden umrechnen
call :TimeToSeconds "%start%" start_sec
call :TimeToSeconds "%end%" end_sec

echo.
echo [1/4] Erstelle ersten Teil...
"%FFMPEG%" -i "%input%" -t %start_sec% -c copy "%TEMP%\part1.mkv"
if errorlevel 1 (
    echo [FEHLER] Beim Erstellen des ersten Teils ist ein Fehler aufgetreten!
    pause
    goto START
)

echo [2/4] Erstelle zweiten Teil...
"%FFMPEG%" -i "%input%" -ss %end_sec% -c copy "%TEMP%\part2.mkv"
if errorlevel 1 (
    echo [FEHLER] Beim Erstellen des zweiten Teils ist ein Fehler aufgetreten!
    del "%TEMP%\part1.mkv" 2>nul
    pause
    goto START
)

echo [3/4] Erstelle Liste...
(
    echo file '%TEMP%\part1.mkv'
    echo file '%TEMP%\part2.mkv'
) > "%TEMP%\filelist.txt"

echo [4/4] Füge Teile zusammen...
"%FFMPEG%" -f concat -safe 0 -i "%TEMP%\filelist.txt" -c copy "%output%"
if errorlevel 1 (
    echo [FEHLER] Beim Zusammenfügen ist ein Fehler aufgetreten!
) else (
    echo ✅ Fertig! Datei gespeichert als: "%output%"
)

:: Temporäre Dateien löschen
del "%TEMP%\part1.mkv" 2>nul
del "%TEMP%\part2.mkv" 2>nul
del "%TEMP%\filelist.txt" 2>nul

set "dropped_file="
pause
goto START

:ENDE
echo.
if not "%dropped_file%"=="" (
    set "input=%dropped_file%"
    echo Verwende Drag ^& Drop Datei: %dropped_file%
) else (
    set "input="
    echo Tipp: Du kannst auch Dateien per Drag ^& Drop ins Fenster ziehen!
    set /p "input=Bitte gib den Dateinamen (mit Endung) ein: "
)
set "input=%input:"=%"

if not exist "%input%" (
    echo.
    echo [FEHLER] Datei "%input%" wurde nicht gefunden!
    pause
    goto START
)

call :GetFileInfo "%input%"
echo.

set /p "end=Letzte Sekunde, die behalten werden soll (z.B. 00:02:03): "
set "output=%dir%%basename%_ende_geschnitten%ext%"
echo.
echo Ausgabedatei wird sein: %output%
set /p "custom_output=Anderen Namen verwenden? (Enter für Standard): "
if not "%custom_output%"=="" set "output=%custom_output%"

echo.
echo Schneide Ende ab...
"%FFMPEG%" -i "%input%" -t %end% -c copy "%output%"
if errorlevel 1 (
    echo [FEHLER] Beim Schneiden ist ein Fehler aufgetreten!
) else (
    echo ✅ Fertig! Datei gespeichert als: "%output%"
)
set "dropped_file="
pause
goto START

:: ----------------------------------------
:: Hilfsfunktion: Dateiinfo extrahieren
:: ----------------------------------------
:GetFileInfo
for %%A in ("%~1") do set "basename=%%~nA"
for %%A in ("%~1") do set "ext=%%~xA"
for %%A in ("%~1") do set "dir=%%~dpA"
exit /b

:: ----------------------------------------
:: Hilfsfunktion: Zeit in Sekunden
:: ----------------------------------------
:TimeToSeconds
setlocal enabledelayedexpansion
set "time_string=%~1"
set "return_var=%~2"

:: Zeit aufteilen (HH:MM:SS oder MM:SS)
for /f "tokens=1-3 delims=:" %%a in ("%time_string%") do (
    set "part1=%%a"
    set "part2=%%b"
    set "part3=%%c"
)

:: Prüfen ob HH:MM:SS oder MM:SS Format
if not defined part3 (
    :: MM:SS Format
    set /a seconds=!part1!*60 + !part2!
) else (
    :: HH:MM:SS Format
    set /a seconds=!part1!*3600 + !part2!*60 + !part3!
)

endlocal & set "%return_var%=%seconds%"
exit /b