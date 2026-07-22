@echo off
title FFmpeg SepMerger
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
    echo [INFO] FFprobe gefunden - verwende erweiterte Codec-Erkennung
) else (
    echo [INFO] FFprobe nicht gefunden - verwende Basis-Erkennung
)
echo.
timeout /t 2 >nul

:: ----------------------------------------
::   FFmpeg Menü – verlustfrei mit Auto-Erkennung
:: ----------------------------------------

:START
cls
echo =====================================
echo        FFmpeg Separator + Merger
echo =====================================
echo.
echo Wähle eine Option:
echo [1] Nur Audio exportieren (verlustfrei)
echo [2] Nur Video exportieren (verlustfrei)
echo [3] Audio und Video trennen (verlustfrei)
echo [4] Audio und Video muxen (zusammenfügen)
echo [5] Video rotieren (90°-Schritte)
echo [6] Beenden
echo.

set /p "choice=Deine Auswahl: "

if "%choice%"=="1" goto AUDIO
if "%choice%"=="2" goto VIDEO
if "%choice%"=="3" goto SPLIT
if "%choice%"=="4" goto MUX
if "%choice%"=="5" goto ROTATE
if "%choice%"=="6" exit
echo Ungültige Auswahl!
pause
goto START

:AUDIO
echo.
set "input="
set /p "input=Bitte gib den Dateinamen (mit Endung) ein: "
set "input=%input:"=%"

if not exist "%input%" (
    echo.
    echo [FEHLER] Datei "%input%" wurde nicht gefunden!
    pause
    goto START
)

call :GetFileInfo "%input%"
call :DetectAudioCodec "%input%"

echo.
echo Exportiere nur Audio (verlustfrei)...
if "%a_ext%"=="" set "a_ext=mka"
"%FFMPEG%" -i "%input%" -vn -c copy "%dir%%basename%_audio.%a_ext%"
if errorlevel 1 (
    echo [FEHLER] Beim Audio-Export ist ein Fehler aufgetreten!
) else (
    echo Audio wurde exportiert als "%dir%%basename%_audio.%a_ext%"
)
pause
goto START

:VIDEO
echo.
set "input="
set /p "input=Bitte gib den Dateinamen (mit Endung) ein: "
set "input=%input:"=%"

if not exist "%input%" (
    echo.
    echo [FEHLER] Datei "%input%" wurde nicht gefunden!
    pause
    goto START
)

call :GetFileInfo "%input%"

echo.
echo Exportiere nur Video (verlustfrei)...
"%FFMPEG%" -i "%input%" -an -c copy "%dir%%basename%_video.mp4"
if errorlevel 1 (
    echo [FEHLER] Beim Video-Export ist ein Fehler aufgetreten!
) else (
    echo Video wurde exportiert als "%dir%%basename%_video.mp4"
)
pause
goto START

:SPLIT
echo.
set "input="
set /p "input=Bitte gib den Dateinamen (mit Endung) ein: "
set "input=%input:"=%"

if not exist "%input%" (
    echo.
    echo [FEHLER] Datei "%input%" wurde nicht gefunden!
    pause
    goto START
)

call :GetFileInfo "%input%"
call :DetectAudioCodec "%input%"

echo.
echo Trenne Audio und Video (verlustfrei)...
if "%a_ext%"=="" set "a_ext=mka"
"%FFMPEG%" -i "%input%" -vn -c copy "%dir%%basename%_audio.%a_ext%"
if errorlevel 1 (
    echo [FEHLER] Beim Audio-Export ist ein Fehler aufgetreten!
) else (
    echo Audio exportiert: "%dir%%basename%_audio.%a_ext%"
)
"%FFMPEG%" -i "%input%" -an -c copy "%dir%%basename%_video.mp4"
if errorlevel 1 (
    echo [FEHLER] Beim Video-Export ist ein Fehler aufgetreten!
) else (
    echo Video exportiert: "%dir%%basename%_video.mp4"
)
pause
goto START

:MUX
echo.
set "video="
set /p "video=Pfad zur Videodatei: "
set "video=%video:"=%"

set "audio="
set /p "audio=Pfad zur Audiodatei: "
set "audio=%audio:"=%"

if not exist "%video%" (
    echo Videodatei nicht gefunden!
    pause
    goto START
)
if not exist "%audio%" (
    echo Audiodatei nicht gefunden!
    pause
    goto START
)

set "output="
set /p "output=Name der Ausgabedatei (z.B. output.mp4): "
set "output=%output:"=%"

"%FFMPEG%" -i "%video%" -i "%audio%" -c copy "%output%"
if errorlevel 1 (
    echo [FEHLER] Beim Muxen ist ein Fehler aufgetreten!
) else (
    echo Muxen abgeschlossen! Ergebnis: "%output%"
)
pause
goto START

:: ----------------------------------------
::   Video rotieren in 90°-Schritten
:: ----------------------------------------
:ROTATE
cls
echo =====================================
echo          Video Rotation
echo =====================================
echo.
set "input="
set /p "input=Bitte gib den Dateinamen (mit Endung) ein: "
set "input=%input:"=%"

if not exist "%input%" (
    echo.
    echo [FEHLER] Datei "%input%" wurde nicht gefunden!
    pause
    goto START
)

call :GetFileInfo "%input%"

:ROTATE_MENU
cls
echo =====================================
echo    Video Rotation - Winkel wählen
echo =====================================
echo.
echo Datei: %basename%%ext%
echo.
echo [1] 90° im Uhrzeigersinn
echo [2] 180° drehen
echo [3] 270° im Uhrzeigersinn (90° gegen UZS)
echo [4] Zurück zum Hauptmenü
echo.

set /p "rotate_choice=Wähle Rotation: "

set "rotation="
set "suffix="

if "%rotate_choice%"=="1" (
    set "rotation=90"
    set "suffix=_rot90"
) else if "%rotate_choice%"=="2" (
    set "rotation=180"
    set "suffix=_rot180"
) else if "%rotate_choice%"=="3" (
    set "rotation=270"
    set "suffix=_rot270"
) else if "%rotate_choice%"=="4" (
    goto START
) else (
    echo Ungültige Auswahl!
    pause
    goto ROTATE_MENU
)

:ROTATE_METHOD
cls
echo =====================================
echo       Rotations-Methode wählen
echo =====================================
echo.
echo [1] Metadaten-Rotation (100%% verlustfrei)
echo     - Keine Re-Encodierung
echo     - Funktioniert in den meisten Playern
echo     - Instant, keine Wartezeit
echo.
echo [2] Pixel-Rotation (quasi-verlustfrei)
echo     - Re-Encodierung mit höchster Qualität
echo     - Funktioniert in allen Playern/Editoren
echo     - Dauert länger
echo.
echo [3] Zurück
echo.

set /p "method=Wähle Methode: "

if "%method%"=="1" goto ROTATE_METADATA
if "%method%"=="2" goto ROTATE_REENCODE
if "%method%"=="3" goto ROTATE_MENU

echo Ungültige Auswahl!
pause
goto ROTATE_METHOD

:ROTATE_METADATA
echo.
echo =====================================
echo Rotiere Video (Metadaten, verlustfrei)...
echo =====================================
echo.

"%FFMPEG%" -i "%input%" -c copy -metadata:s:v:0 rotate="%rotation%" "%dir%%basename%%suffix%_metadata.mp4"

if errorlevel 1 (
    echo.
    echo [FEHLER] Beim Rotieren ist ein Fehler aufgetreten!
) else (
    echo.
    echo =====================================
    echo Video erfolgreich rotiert (Metadaten)!
    echo Ausgabe: %dir%%basename%%suffix%_metadata.mp4
    echo.
    echo HINWEIS: Dies ändert nur Metadaten.
    echo Funktioniert in VLC, Windows Media Player, etc.
    echo Falls nicht sichtbar, nutze Pixel-Rotation.
    echo =====================================
)

echo.
pause
goto START

:ROTATE_REENCODE
echo.
echo =====================================
echo Rotiere Video (Re-Encoding, quasi-verlustfrei)...
echo =====================================
echo.
echo Verwende höchste Qualität (CRF 0 = verlustfrei)
echo Dies kann einige Zeit dauern...
echo.

set "filter="
if "%rotation%"=="90" set "filter=transpose=1"
if "%rotation%"=="180" set "filter=transpose=1,transpose=1"
if "%rotation%"=="270" set "filter=transpose=2"

"%FFMPEG%" -i "%input%" -vf "%filter%" -c:v libx264 -preset veryslow -crf 0 -c:a copy "%dir%%basename%%suffix%.mp4"

if errorlevel 1 (
    echo.
    echo [FEHLER] Beim Rotieren ist ein Fehler aufgetreten!
) else (
    echo.
    echo =====================================
    echo Video erfolgreich rotiert!
    echo Ausgabe: %dir%%basename%%suffix%.mp4
    echo.
    echo Verwendete Einstellungen:
    echo - CRF 0 (verlustfreie H.264 Kodierung)
    echo - Preset: veryslow (beste Kompression)
    echo - Audio: verlustfrei kopiert
    echo =====================================
)

echo.
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
:: Hilfsfunktion: Audio-Codec erkennen
:: ----------------------------------------
:DetectAudioCodec
set "a_codec="
if exist "%FFPROBE%" (
    for /f "tokens=*" %%a in ('"%FFPROBE%" -v error -select_streams a:0 -show_entries stream^=codec_name -of default^=noprint_wrappers^=1:nokey^=1 "%~1" 2^>^&1') do set "a_codec=%%a"
) else (
    echo [INFO] ffprobe.exe nicht gefunden, verwende ffmpeg für Codec-Erkennung
    for /f "tokens=1 delims=," %%a in ('"%FFMPEG%" -i "%~1" 2^>^&1 ^| findstr /i "Audio:"') do (
        for /f "tokens=2 delims=:" %%b in ("%%a") do set "a_codec=%%b"
    )
    if defined a_codec (
        set "a_codec=%a_codec: =%"
    )
)

if "%a_codec%"=="" (
    echo [WARNUNG] Kein Audio-Stream gefunden!
    set "a_ext="
) else (
    echo Erkanntes Audioformat: %a_codec%
    call :MapAudioExt "%a_codec%"
)
exit /b

:: ----------------------------------------
:: Hilfsfunktion: Codec -> Dateiendung
:: ----------------------------------------
:MapAudioExt
set "a_ext=mka"
if /I "%~1"=="aac"  set "a_ext=aac"
if /I "%~1"=="mp3"  set "a_ext=mp3"
if /I "%~1"=="flac" set "a_ext=flac"
if /I "%~1"=="opus" set "a_ext=opus"
if /I "%~1"=="vorbis" set "a_ext=ogg"
if /I "%~1"=="ac3"  set "a_ext=ac3"
if /I "%~1"=="eac3" set "a_ext=eac3"
if /I "%~1"=="dts"  set "a_ext=dts"
exit /b