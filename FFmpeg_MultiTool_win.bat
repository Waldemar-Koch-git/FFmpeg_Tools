@echo off
title FFmpeg Multi-Tool
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: ============================================================================
::  FFmpeg Multi-Tool
::  Vereint: Video-Schnitt, Audio/Video-Trennung, Muxen, Rotation, MP3-Konvertierung
::  Mehrere Bugs entfernt die in den 3 einzel-bat noch existieren..
:: ============================================================================

set "FFMPEG_DIR=%~dp0FFmpeg"
set "FFMPEG=%FFMPEG_DIR%\ffmpeg.exe"
set "FFPROBE=%FFMPEG_DIR%\ffprobe.exe"

call :CheckFFmpeg
if errorlevel 1 exit /b 1

:: Verwaiste Temp-Dateien aus abgebrochenen frueheren Laeufen entfernen
del /q "%TEMP%\ffmpegmt_*" 2>nul

set "dropped_file="
if not "%~1"=="" set "dropped_file=%~1"

goto MAIN_MENU

:: ============================================================================
::   HAUPTMENUE
:: ============================================================================
:MAIN_MENU
cls
echo ===================================================
echo             FFmpeg Multi-Tool
echo ===================================================
echo.
echo   [1] Video schneiden        (Anfang / Mitte / Ende)
echo   [2] Audio / Video trennen  (exportieren, verlustfrei)
echo   [3] Audio + Video muxen    (zusammenfuegen)
echo   [4] Video rotieren
echo   [5] Audio in MP3 konvertieren
echo   [6] Beenden
echo.
if defined dropped_file echo   Aktive Datei ^(Drag ^& Drop^): %dropped_file%
echo.
set "main_choice="
set /p "main_choice=Deine Auswahl: "

if "%main_choice%"=="1" goto MENU_SCHNITT
if "%main_choice%"=="2" goto MENU_TRENNEN
if "%main_choice%"=="3" goto MENU_MUX
if "%main_choice%"=="4" goto MENU_ROTATE
if "%main_choice%"=="5" goto MENU_CONVERT
if "%main_choice%"=="6" exit
echo Ungueltige Auswahl!
pause
goto MAIN_MENU

:: ============================================================================
::   1) VIDEO SCHNEIDEN
:: ============================================================================
:MENU_SCHNITT
cls
echo ===================================================
echo   Video schneiden
echo ===================================================
echo.
echo   [1] Anfang abschneiden
echo   [2] Mittleren Teil herausschneiden
echo   [3] Ende abschneiden (nur Anfangsteil behalten)
echo   [4] Zurueck zum Hauptmenue
echo.
set "schnitt_choice="
set /p "schnitt_choice=Deine Auswahl: "

if "%schnitt_choice%"=="1" goto SCHNITT_ANFANG
if "%schnitt_choice%"=="2" goto SCHNITT_MITTE
if "%schnitt_choice%"=="3" goto SCHNITT_ENDE
if "%schnitt_choice%"=="4" goto MAIN_MENU
echo Ungueltige Auswahl!
pause
goto MENU_SCHNITT

:SCHNITT_ANFANG
cls
call :GetInputFile
if "%INPUT_OK%"=="0" (
    pause
    goto MENU_SCHNITT
)
call :GetFileInfo "%INPUT_FILE%"

echo.
call :AskTime "Zeitpunkt, ab dem behalten werden soll (z.B. 00:01:41): " start

call :AskCustomOutput "%dir%%basename%_anfang_geschnitten%ext%"
call :CheckOverwrite "%OUTPUT_FILE%"
if "%OVERWRITE_OK%"=="0" (
    echo Abgebrochen.
    pause
    goto MENU_SCHNITT
)

echo.
echo Schneide Anfang ab...
echo ^(Hinweis: Stream-Copy schneidet am naechsten Keyframe, kleine
echo  Abweichungen vom exakten Zeitstempel sind moeglich^)
"%FFMPEG%" -y -ss %start% -i "%INPUT_FILE%" -c copy "%OUTPUT_FILE%"
call :ReportResult "Beim Schneiden ist ein Fehler aufgetreten" "Fertig! Datei gespeichert als: !OUTPUT_FILE!"
pause
goto MENU_SCHNITT

:SCHNITT_MITTE
cls
call :GetInputFile
if "%INPUT_OK%"=="0" (
    pause
    goto MENU_SCHNITT
)
call :GetFileInfo "%INPUT_FILE%"

echo.
call :AskTime "Startzeit des zu loeschenden Bereichs (z.B. 00:01:41): " start
call :AskTime "Endzeit des zu loeschenden Bereichs (z.B. 00:02:03): " end

call :AskCustomOutput "%dir%%basename%_mitte_geschnitten%ext%"
call :CheckOverwrite "%OUTPUT_FILE%"
if "%OVERWRITE_OK%"=="0" (
    echo Abgebrochen.
    pause
    goto MENU_SCHNITT
)

set "TMP1=%TEMP%\ffmpegmt_%RANDOM%%RANDOM%_part1.mkv"
set "TMP2=%TEMP%\ffmpegmt_%RANDOM%%RANDOM%_part2.mkv"
set "TMPLIST=%TEMP%\ffmpegmt_%RANDOM%%RANDOM%_filelist.txt"

echo.
echo [1/4] Erstelle ersten Teil (0 bis %start%)...
"%FFMPEG%" -y -i "%INPUT_FILE%" -t %start% -c copy "%TMP1%"
if errorlevel 1 (
    echo [FEHLER] Beim Erstellen des ersten Teils ist ein Fehler aufgetreten!
    del "%TMP1%" 2>nul
    pause
    goto MENU_SCHNITT
)

echo [2/4] Erstelle zweiten Teil (ab %end%)...
"%FFMPEG%" -y -ss %end% -i "%INPUT_FILE%" -c copy "%TMP2%"
if errorlevel 1 (
    echo [FEHLER] Beim Erstellen des zweiten Teils ist ein Fehler aufgetreten!
    del "%TMP1%" 2>nul
    del "%TMP2%" 2>nul
    pause
    goto MENU_SCHNITT
)

echo [3/4] Erstelle Verkettungsliste...
(
    echo file '%TMP1%'
    echo file '%TMP2%'
) > "%TMPLIST%"

echo [4/4] Fuege Teile zusammen...
"%FFMPEG%" -y -f concat -safe 0 -i "%TMPLIST%" -c copy "%OUTPUT_FILE%"
call :ReportResult "Beim Zusammenfuegen ist ein Fehler aufgetreten" "Fertig! Datei gespeichert als: !OUTPUT_FILE!"

del "%TMP1%" 2>nul
del "%TMP2%" 2>nul
del "%TMPLIST%" 2>nul
pause
goto MENU_SCHNITT

:SCHNITT_ENDE
cls
call :GetInputFile
if "%INPUT_OK%"=="0" (
    pause
    goto MENU_SCHNITT
)
call :GetFileInfo "%INPUT_FILE%"

echo.
call :AskTime "Bis zu diesem Zeitpunkt behalten, Rest abschneiden (z.B. 00:02:03): " end

call :AskCustomOutput "%dir%%basename%_ende_geschnitten%ext%"
call :CheckOverwrite "%OUTPUT_FILE%"
if "%OVERWRITE_OK%"=="0" (
    echo Abgebrochen.
    pause
    goto MENU_SCHNITT
)

echo.
echo Schneide Ende ab...
"%FFMPEG%" -y -i "%INPUT_FILE%" -t %end% -c copy "%OUTPUT_FILE%"
call :ReportResult "Beim Schneiden ist ein Fehler aufgetreten" "Fertig! Datei gespeichert als: !OUTPUT_FILE!"
pause
goto MENU_SCHNITT

:: ============================================================================
::   2) AUDIO / VIDEO TRENNEN
:: ============================================================================
:MENU_TRENNEN
cls
echo ===================================================
echo   Audio / Video trennen
echo ===================================================
echo.
echo   [1] Nur Audio exportieren (verlustfrei)
echo   [2] Nur Video exportieren (verlustfrei, ohne Ton)
echo   [3] Beides gleichzeitig exportieren
echo   [4] Zurueck zum Hauptmenue
echo.
set "trennen_choice="
set /p "trennen_choice=Deine Auswahl: "

if "%trennen_choice%"=="1" goto TRENNEN_AUDIO
if "%trennen_choice%"=="2" goto TRENNEN_VIDEO
if "%trennen_choice%"=="3" goto TRENNEN_BEIDE
if "%trennen_choice%"=="4" goto MAIN_MENU
echo Ungueltige Auswahl!
pause
goto MENU_TRENNEN

:TRENNEN_AUDIO
cls
call :GetInputFile
if "%INPUT_OK%"=="0" (
    pause
    goto MENU_TRENNEN
)
call :GetFileInfo "%INPUT_FILE%"
call :DetectAudioCodec "%INPUT_FILE%"
if "%a_ext%"=="" set "a_ext=mka"

call :AskCustomOutput "%dir%%basename%_audio.%a_ext%"
call :CheckOverwrite "%OUTPUT_FILE%"
if "%OVERWRITE_OK%"=="0" (
    echo Abgebrochen.
    pause
    goto MENU_TRENNEN
)

echo.
echo Exportiere nur Audio (verlustfrei)...
"%FFMPEG%" -y -i "%INPUT_FILE%" -vn -c copy "%OUTPUT_FILE%"
call :ReportResult "Beim Audio-Export ist ein Fehler aufgetreten!" "Audio exportiert: %OUTPUT_FILE%"
pause
goto MENU_TRENNEN

:TRENNEN_VIDEO
cls
call :GetInputFile
if "%INPUT_OK%"=="0" (
    pause
    goto MENU_TRENNEN
)
call :GetFileInfo "%INPUT_FILE%"

call :AskCustomOutput "%dir%%basename%_video.mp4"
call :CheckOverwrite "%OUTPUT_FILE%"
if "%OVERWRITE_OK%"=="0" (
    echo Abgebrochen.
    pause
    goto MENU_TRENNEN
)

echo.
echo Exportiere nur Video (verlustfrei, ohne Ton)...
"%FFMPEG%" -y -i "%INPUT_FILE%" -an -c copy "%OUTPUT_FILE%"
call :ReportResult "Beim Video-Export ist ein Fehler aufgetreten!" "Video exportiert: %OUTPUT_FILE%"
pause
goto MENU_TRENNEN

:TRENNEN_BEIDE
cls
call :GetInputFile
if "%INPUT_OK%"=="0" (
    pause
    goto MENU_TRENNEN
)
call :GetFileInfo "%INPUT_FILE%"
call :DetectAudioCodec "%INPUT_FILE%"
if "%a_ext%"=="" set "a_ext=mka"

set "AUDIO_OUT=%dir%%basename%_audio.%a_ext%"
set "VIDEO_OUT=%dir%%basename%_video.mp4"

call :CheckOverwrite "%AUDIO_OUT%"
set "audio_ow=%OVERWRITE_OK%"
call :CheckOverwrite "%VIDEO_OUT%"
set "video_ow=%OVERWRITE_OK%"

echo.
if "%audio_ow%"=="1" (
    echo Exportiere Audio...
    "%FFMPEG%" -y -i "!INPUT_FILE!" -vn -c copy "!AUDIO_OUT!"
    call :ReportResult "Beim Audio-Export ist ein Fehler aufgetreten" "Audio exportiert: !AUDIO_OUT!"
) else (
    echo Audio-Export uebersprungen.
)

if "%video_ow%"=="1" (
    echo Exportiere Video...
    "%FFMPEG%" -y -i "!INPUT_FILE!" -an -c copy "!VIDEO_OUT!"
    call :ReportResult "Beim Video-Export ist ein Fehler aufgetreten" "Video exportiert: !VIDEO_OUT!"
) else (
    echo Video-Export uebersprungen.
)
pause
goto MENU_TRENNEN

:: ============================================================================
::   3) MUXEN (AUDIO + VIDEO ZUSAMMENFUEGEN)
:: ============================================================================
:MENU_MUX
cls
echo ===================================================
echo   Audio + Video zusammenfuegen (Muxen)
echo ===================================================
echo.
echo   [1] Audio unveraendert uebernehmen (verlustfrei)
echo   [2] Audio dabei zu MP3 konvertieren (z.B. bei WAV)
echo   [3] Zurueck zum Hauptmenue
echo.
set "mux_choice="
set /p "mux_choice=Deine Auswahl: "

if "%mux_choice%"=="1" goto MUX_COPY
if "%mux_choice%"=="2" goto MUX_MP3
if "%mux_choice%"=="3" goto MAIN_MENU
echo Ungueltige Auswahl!
pause
goto MENU_MUX

:MUX_COPY
cls
echo ===================================================
echo   Muxen - Audio unveraendert uebernehmen
echo ===================================================
echo.
call :GetInputFile "Videodatei"
if "%INPUT_OK%"=="0" (
    pause
    goto MENU_MUX
)
set "video=%INPUT_FILE%"

echo.
call :GetInputFile "Audiodatei"
if "%INPUT_OK%"=="0" (
    pause
    goto MENU_MUX
)
set "audio=%INPUT_FILE%"

call :GetFileInfo "%video%"
call :AskCustomOutput "%dir%%basename%_muxed.mp4"
call :CheckOverwrite "%OUTPUT_FILE%"
if "%OVERWRITE_OK%"=="0" (
    echo Abgebrochen.
    pause
    goto MENU_MUX
)

echo.
echo Fuege Video und Audio zusammen...
"%FFMPEG%" -y -i "%video%" -i "%audio%" -c copy -map 0:v:0 -map 1:a:0 "%OUTPUT_FILE%"
call :ReportResult "Beim Muxen ist ein Fehler aufgetreten!" "Muxen abgeschlossen: %OUTPUT_FILE%"
if errorlevel 1 (
    echo Moegliche Ursache: Der Audio-Codec ist im Ziel-Container nicht erlaubt
    echo ^(z.B. WAV direkt in MP4^). Nutze in diesem Fall Option [2] im Muxen-Menue.
)
pause
goto MENU_MUX

:MUX_MP3
cls
echo ===================================================
echo   Muxen mit MP3-Konvertierung
echo ===================================================
echo.
echo Kombiniert eine Videodatei (ohne Ton) mit einer
echo Audiodatei und konvertiert das Audio dabei zu MP3.
echo ===================================================
echo.
call :GetInputFile "Videodatei (ohne Audio)"
if "%INPUT_OK%"=="0" (
    pause
    goto MENU_MUX
)
set "video=%INPUT_FILE%"

echo.
call :GetInputFile "Audiodatei (z.B. WAV)"
if "%INPUT_OK%"=="0" (
    pause
    goto MENU_MUX
)
set "audio=%INPUT_FILE%"

call :GetFileInfo "%video%"
call :SelectMp3Bitrate

call :AskCustomOutput "%dir%%basename%_merged.mp4"
call :CheckOverwrite "%OUTPUT_FILE%"
if "%OVERWRITE_OK%"=="0" (
    echo Abgebrochen.
    pause
    goto MENU_MUX
)

cls
echo ===================================================
echo   Starte Muxing-Prozess
echo ===================================================
echo.
echo Video:    %video%
echo Audio:    %audio%
echo Bitrate:  %MP3_INFO%
echo Ausgabe:  %OUTPUT_FILE%
echo.
echo Verarbeitung laeuft (Video wird kopiert, Audio zu MP3 konvertiert)...
echo.

"%FFMPEG%" -y -i "%video%" -i "%audio%" -c:v copy %MP3_PARAMS% -map 0:v:0 -map 1:a:0 "%OUTPUT_FILE%"
echo.
call :ReportResult "Beim Muxen ist ein Fehler aufgetreten" "Erfolgreich abgeschlossen!"
if errorlevel 1 (
    echo Moegliche Ursachen:
    echo  - Video- und Audiolaenge unterscheiden sich stark
    echo  - Beschaedigte Eingabedateien
    echo  - Unzureichender Speicherplatz
) else (
    echo Ausgabedatei: !OUTPUT_FILE!
    echo Audio-Format: MP3 ^(%MP3_INFO%^)
    echo Video-Format: unveraendert ^(verlustfrei kopiert^)
)
echo.
pause
goto MENU_MUX

:: ============================================================================
::   4) VIDEO ROTIEREN
:: ============================================================================
:MENU_ROTATE
cls
call :GetInputFile
if "%INPUT_OK%"=="0" (
    pause
    goto MAIN_MENU
)
call :GetFileInfo "%INPUT_FILE%"

:ROTATE_ANGLE_MENU
cls
echo ===================================================
echo   Video Rotation - Winkel waehlen
echo ===================================================
echo.
echo Datei: %basename%%ext%
echo.
echo   [1] 90 Grad im Uhrzeigersinn
echo   [2] 180 Grad drehen
echo   [3] 270 Grad im Uhrzeigersinn (90 Grad gegen den UZS)
echo   [4] Zurueck zum Hauptmenue
echo.
set "rotate_choice="
set /p "rotate_choice=Waehle Rotation: "

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
    goto MAIN_MENU
) else (
    echo Ungueltige Auswahl!
    pause
    goto ROTATE_ANGLE_MENU
)

:ROTATE_METHOD_MENU
cls
echo ===================================================
echo   Rotations-Methode waehlen
echo ===================================================
echo.
echo   [1] Metadaten-Rotation (instant, 100%% verlustfrei)
echo       - keine Re-Encodierung, funktioniert in den meisten Playern
echo   [2] Pixel-Rotation (Re-Encoding, CRF 0 = verlustfrei)
echo       - dauert laenger, funktioniert in allen Playern/Editoren
echo   [3] Zurueck
echo.
set "method="
set /p "method=Waehle Methode: "

if "%method%"=="1" goto ROTATE_METADATA
if "%method%"=="2" goto ROTATE_REENCODE
if "%method%"=="3" goto ROTATE_ANGLE_MENU
echo Ungueltige Auswahl!
pause
goto ROTATE_METHOD_MENU

:ROTATE_METADATA
call :AskCustomOutput "%dir%%basename%%suffix%_metadata.mp4"
call :CheckOverwrite "%OUTPUT_FILE%"
if "%OVERWRITE_OK%"=="0" (
    echo Abgebrochen.
    pause
    goto MENU_ROTATE
)

echo.
echo Rotiere Video (Metadaten, verlustfrei)...
"%FFMPEG%" -y -i "%INPUT_FILE%" -c copy -metadata:s:v:0 rotate=%rotation% "%OUTPUT_FILE%"
call :ReportResult "Beim Rotieren ist ein Fehler aufgetreten" "Video rotiert! Ausgabe: !OUTPUT_FILE!"
if not errorlevel 1 (
    echo HINWEIS: Aendert nur Metadaten. Falls im Player nicht sichtbar,
    echo nutze stattdessen die Pixel-Rotation.
)
pause
goto MAIN_MENU

:ROTATE_REENCODE
call :AskCustomOutput "%dir%%basename%%suffix%.mp4"
call :CheckOverwrite "%OUTPUT_FILE%"
if "%OVERWRITE_OK%"=="0" (
    echo Abgebrochen.
    pause
    goto MENU_ROTATE
)

set "filter="
if "%rotation%"=="90" set "filter=transpose=1"
if "%rotation%"=="180" set "filter=transpose=1,transpose=1"
if "%rotation%"=="270" set "filter=transpose=2"

echo.
echo Rotiere Video (Re-Encoding, CRF 0 = verlustfrei)...
echo Dies kann je nach Videolaenge einige Zeit dauern...
echo.
"%FFMPEG%" -y -i "%INPUT_FILE%" -vf "%filter%" -c:v libx264 -preset veryslow -crf 0 -c:a copy "%OUTPUT_FILE%"
call :ReportResult "Beim Rotieren ist ein Fehler aufgetreten" "Video rotiert! Ausgabe: !OUTPUT_FILE!"
if not errorlevel 1 (
    echo Einstellungen: CRF 0, Preset veryslow, Audio verlustfrei kopiert.
)
pause
goto MAIN_MENU

:: ============================================================================
::   5) AUDIO IN MP3 KONVERTIEREN
:: ============================================================================
:MENU_CONVERT
cls
echo ===================================================
echo   Audio in MP3 konvertieren
echo ===================================================
echo.
call :GetInputFile
if "%INPUT_OK%"=="0" (
    pause
    goto MAIN_MENU
)
call :GetFileInfo "%INPUT_FILE%"

call :SelectMp3Bitrate

call :AskCustomOutput "%dir%%basename%_converted.mp3"
call :CheckOverwrite "%OUTPUT_FILE%"
if "%OVERWRITE_OK%"=="0" (
    echo Abgebrochen.
    pause
    goto MAIN_MENU
)

echo.
echo Konvertierung laeuft (%MP3_INFO%)...
"%FFMPEG%" -y -i "%INPUT_FILE%" %MP3_PARAMS% -vn "%OUTPUT_FILE%"
echo.
call :ReportResult "Bei der Konvertierung ist ein Fehler aufgetreten" "Fertig! Datei gespeichert als: !OUTPUT_FILE!"
pause
goto MAIN_MENU

:: ============================================================================
::   HILFSFUNKTIONEN
:: ============================================================================

:CheckFFmpeg
if not exist "%FFMPEG_DIR%" (
    echo [FEHLER] Der Ordner "FFmpeg" wurde nicht gefunden!
    echo Bitte erstelle einen Unterordner "FFmpeg" neben dieser Batch-Datei
    echo und lege ffmpeg.exe ^(und optional ffprobe.exe^) dort hinein.
    echo.
    pause
    exit /b 1
)
if not exist "%FFMPEG%" (
    echo [FEHLER] ffmpeg.exe wurde im Ordner "FFmpeg" nicht gefunden!
    echo Erwarteter Pfad: !FFMPEG!
    echo.
    pause
    exit /b 1
)
echo [INFO] FFmpeg gefunden in: %FFMPEG_DIR%
if exist "%FFPROBE%" (
    echo [INFO] FFprobe gefunden - erweiterte Codec-Erkennung aktiv
) else (
    echo [INFO] FFprobe nicht gefunden - Basis-Codec-Erkennung wird verwendet
)
echo.
timeout /t 1 >nul
exit /b 0

:: Fragt eine Eingabedatei ab (nutzt zuerst eine per Drag & Drop uebergebene
:: Datei, danach manuelle Eingabe). Ergebnis in INPUT_FILE, Status in INPUT_OK.
:: %1 (optional) = Bezeichnung fuer den Prompt, z.B. "Videodatei"
:GetInputFile
set "_label=%~1"
if "%_label%"=="" set "_label=Datei"
set "INPUT_FILE="
if defined dropped_file (
    set "INPUT_FILE=!dropped_file!"
    echo Verwende per Drag ^& Drop uebergebene Datei als %_label%: !dropped_file!
    set "dropped_file="
) else (
    echo Tipp: %_label% per Drag ^& Drop in dieses Fenster ziehen und Enter druecken,
    echo oder Dateiname/Pfad eingeben:
    set /p "INPUT_FILE=%_label%: "
)
set "INPUT_FILE=%INPUT_FILE:"=%"
if not exist "%INPUT_FILE%" (
    echo.
    echo [FEHLER] Datei "!INPUT_FILE!" wurde nicht gefunden!
    set "INPUT_OK=0"
    exit /b 1
)
set "INPUT_OK=1"
exit /b 0

:: Extrahiert Basisname, Endung und Verzeichnis aus einem Dateipfad (%1)
:GetFileInfo
for %%A in ("%~1") do set "basename=%%~nA"
for %%A in ("%~1") do set "ext=%%~xA"
for %%A in ("%~1") do set "dir=%%~dpA"
exit /b 0

:: Schlaegt einen Standard-Ausgabepfad (%1) vor und erlaubt einen eigenen Namen.
:: Ergebnis in OUTPUT_FILE. Prueft, dass das Zielverzeichnis existiert.
:AskCustomOutput
set "_default_output=%~1"
set "OUTPUT_FILE=%_default_output%"
:AskCustomOutput_Retry
echo.
echo Ausgabedatei: %OUTPUT_FILE%
set "custom_output="
set /p "custom_output=Anderen Dateinamen verwenden? (Enter fuer Standard): "
set "custom_output=%custom_output:"=%"
if not "%custom_output%"=="" set "OUTPUT_FILE=%custom_output%"

for %%A in ("%OUTPUT_FILE%") do set "_out_dir=%%~dpA"
if not exist "%_out_dir%" (
    echo.
    echo [FEHLER] Zielverzeichnis "!_out_dir!" existiert nicht!
    set "OUTPUT_FILE=!_default_output!"
    goto AskCustomOutput_Retry
)
exit /b 0

:: Prueft ob eine Datei (%1) bereits existiert und fragt ggf. nach.
:: Ergebnis in OVERWRITE_OK (1 = fortfahren, 0 = abbrechen).
:CheckOverwrite
if not exist "%~1" (
    set "OVERWRITE_OK=1"
    exit /b 0
)
echo.
echo [HINWEIS] Die Datei "%~1" existiert bereits.
choice /c JN /n /m "Ueberschreiben? (J=Ja, N=Nein): "
if errorlevel 2 (
    set "OVERWRITE_OK=0"
) else (
    set "OVERWRITE_OK=1"
)
exit /b 0

:: Meldet Erfolg/Fehler des zuletzt ausgefuehrten Befehls (ffmpeg-Aufruf)
:: anhand von dessen Errorlevel und gibt diesen Status per exit /b weiter,
:: sodass "if errorlevel 1 (...)" danach im Aufrufer weiterhin funktioniert.
:: %1 = Fehlertext, %2 = Erfolgstext
:ReportResult
if errorlevel 1 (
    echo [FEHLER] %~1
    exit /b 1
) else (
    echo [OK] %~2
    exit /b 0
)

:: Fragt eine Zeitangabe ab und wiederholt die Abfrage, bis das Format
:: plausibel ist (nur Ziffern, ':' und '.', nicht leer).
:: %1 = Prompt-Text, %2 = Name der Zielvariable
:AskTime
set "_time_prompt=%~1"
set "_time_var=%~2"
:AskTime_Retry
set "_time_val="
set /p "_time_val=%_time_prompt%"
call :ValidateTimeFormat "%_time_val%"
if "%TIME_VALID%"=="0" (
    echo [FEHLER] Ungueltiges Zeitformat! Erlaubt sind nur Ziffern, ':' und '.'
    echo ^(z.B. 00:01:41 oder 95.5^).
    goto AskTime_Retry
)
set "%_time_var%=%_time_val%"
exit /b 0

:: Prueft, ob %1 eine plausible ffmpeg-Zeitangabe ist. Ergebnis in TIME_VALID.
:ValidateTimeFormat
set "TIME_VALID=1"
if "%~1"=="" set "TIME_VALID=0"
for /f "delims=0123456789:." %%a in ("%~1") do set "TIME_VALID=0"
exit /b 0

:: Zeigt das MP3-Bitraten-Menue an. Ergebnis in MP3_PARAMS und MP3_INFO.
:SelectMp3Bitrate
cls
echo ===================================================
echo   MP3-Bitrate auswaehlen
echo ===================================================
echo.
echo   [1] 128 kbps  (kleine Dateigroesse, ok fuer Sprache)
echo   [2] 160 kbps  (Standard)
echo   [3] 192 kbps  (guter Kompromiss)
echo   [4] 256 kbps  (hohe Qualitaet)
echo   [5] 320 kbps  (maximale MP3-Qualitaet)
echo   [6] VBR V0    (~245 kbps, variabel, beste Qualitaet)
echo   [7] VBR V2    (~190 kbps, variabel, sehr gut)
echo   [8] VBR V4    (~165 kbps, variabel, gut fuer Sprache)
echo   [9] Eigene Bitrate eingeben
echo.
set "bitrate_choice="
set /p "bitrate_choice=Deine Auswahl: "

set "MP3_PARAMS="
set "MP3_INFO="

if "%bitrate_choice%"=="1" (
    set "MP3_PARAMS=-c:a libmp3lame -b:a 128k"
    set "MP3_INFO=128 kbps CBR"
    goto MP3_BITRATE_DONE
)
if "%bitrate_choice%"=="2" (
    set "MP3_PARAMS=-c:a libmp3lame -b:a 160k"
    set "MP3_INFO=160 kbps CBR"
    goto MP3_BITRATE_DONE
)
if "%bitrate_choice%"=="3" (
    set "MP3_PARAMS=-c:a libmp3lame -b:a 192k"
    set "MP3_INFO=192 kbps CBR"
    goto MP3_BITRATE_DONE
)
if "%bitrate_choice%"=="4" (
    set "MP3_PARAMS=-c:a libmp3lame -b:a 256k"
    set "MP3_INFO=256 kbps CBR"
    goto MP3_BITRATE_DONE
)
if "%bitrate_choice%"=="5" (
    set "MP3_PARAMS=-c:a libmp3lame -b:a 320k"
    set "MP3_INFO=320 kbps CBR"
    goto MP3_BITRATE_DONE
)
if "%bitrate_choice%"=="6" (
    set "MP3_PARAMS=-c:a libmp3lame -q:a 0"
    set "MP3_INFO=VBR V0 ^(~245 kbps^)"
    goto MP3_BITRATE_DONE
)
if "%bitrate_choice%"=="7" (
    set "MP3_PARAMS=-c:a libmp3lame -q:a 2"
    set "MP3_INFO=VBR V2 ^(~190 kbps^)"
    goto MP3_BITRATE_DONE
)
if "%bitrate_choice%"=="8" (
    set "MP3_PARAMS=-c:a libmp3lame -q:a 4"
    set "MP3_INFO=VBR V4 ^(~165 kbps^)"
    goto MP3_BITRATE_DONE
)
if "%bitrate_choice%"=="9" goto CUSTOM_BITRATE

echo Ungueltige Auswahl!
pause
goto SelectMp3Bitrate

:CUSTOM_BITRATE
echo.
echo Empfohlene Werte: 96, 128, 160, 192, 224, 256, 320
set "custom_br="
set /p "custom_br=Bitrate in kbps eingeben: "

set "valid=true"
for /f "delims=0123456789" %%a in ("%custom_br%") do set "valid=false"
if "%custom_br%"=="" set "valid=false"

if "%valid%"=="false" (
    echo.
    echo [FEHLER] Ungueltige Eingabe! Bitte nur eine Zahl eingeben.
    pause
    goto SelectMp3Bitrate
)

set "MP3_PARAMS=-c:a libmp3lame -b:a %custom_br%k"
set "MP3_INFO=%custom_br% kbps CBR (benutzerdefiniert)"

:MP3_BITRATE_DONE
exit /b 0

:: Ermittelt den Audio-Codec einer Datei (%1) und leitet daraus die passende
:: Dateiendung ab (a_ext). Nutzt ffprobe falls vorhanden, sonst ffmpeg-Fallback.
:DetectAudioCodec
setlocal EnableDelayedExpansion
set "a_codec="
set "a_ext="
if exist "%FFPROBE%" (
    for /f "tokens=*" %%a in ('"%FFPROBE%" -v error -select_streams a:0 -show_entries stream^=codec_name -of default^=noprint_wrappers^=1:nokey^=1 "%~1" 2^>^&1') do set "a_codec=%%a"
) else (
    echo [INFO] ffprobe.exe nicht gefunden, verwende ffmpeg fuer Codec-Erkennung
    set "audio_line="
    for /f "tokens=*" %%a in ('"%FFMPEG%" -i "%~1" 2^>^&1 ^| findstr /i "Audio:"') do (
        if not defined audio_line set "audio_line=%%a"
    )
    if defined audio_line (
        set "after_audio=!audio_line:*Audio: =!"
        for /f "tokens=1 delims=, " %%c in ("!after_audio!") do set "a_codec=%%c"
    )
)

if "%a_codec%"=="" (
    echo [WARNUNG] Kein Audio-Stream gefunden oder Codec konnte nicht erkannt werden!
) else (
    echo Erkanntes Audioformat: %a_codec%
    call :MapAudioExt "%a_codec%"
)

endlocal & set "a_codec=%a_codec%" & set "a_ext=%a_ext%"
exit /b 0

:: Ordnet einen Audio-Codec (%1) einer passenden Dateiendung zu (a_ext)
:MapAudioExt
set "a_ext=mka"
if /I "%~1"=="aac"    set "a_ext=aac"
if /I "%~1"=="mp3"    set "a_ext=mp3"
if /I "%~1"=="flac"   set "a_ext=flac"
if /I "%~1"=="opus"   set "a_ext=opus"
if /I "%~1"=="vorbis" set "a_ext=ogg"
if /I "%~1"=="ac3"    set "a_ext=ac3"
if /I "%~1"=="eac3"   set "a_ext=eac3"
if /I "%~1"=="dts"    set "a_ext=dts"
exit /b 0
