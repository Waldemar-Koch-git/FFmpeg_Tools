# FFmpeg Multi-Tool

Batch-Skript für Windows zum Schneiden, Trennen, Muxen, Rotieren und
Konvertieren von Video-/Audiodateien auf Basis von FFmpeg.

## Voraussetzungen

- Windows mit `cmd.exe`
- FFmpeg (und optional FFprobe für erweiterte Codec-Erkennung)

## Installation

1. Ordner `FFmpeg` neben `FFmpeg_MultiTool.bat` anlegen.
2. `ffmpeg.exe` (und optional `ffprobe.exe`) in diesen Ordner legen.

```
FFmpeg_MultiTool.bat
FFmpeg/
  ffmpeg.exe
  ffprobe.exe   (optional)
```

## Verwendung

`FFmpeg_MultiTool.bat` per Doppelklick starten, oder eine Datei direkt auf
das Skript ziehen, um sie als aktive Eingabedatei zu übernehmen.

Im Hauptmenü stehen folgende Funktionen zur Verfügung:

| Option | Funktion |
|---|---|
| 1 | Video schneiden (Anfang / Mitte / Ende, verlustfrei) |
| 2 | Audio und Video trennen (verlustfrei) |
| 3 | Audio und Video zusammenfügen (Muxen) |
| 4 | Video rotieren (Metadaten oder Re-Encoding) |
| 5 | Audio in MP3 konvertieren |

Alle Funktionen unterstützen Drag & Drop für Eingabedateien und fragen vor
dem Überschreiben vorhandener Ausgabedateien nach.

## Hinweise

- Verlustfreie Schnitte (Stream-Copy) sind an Keyframes ausgerichtet;
  geringe Abweichungen vom exakten Zeitstempel sind möglich.
- Zeitangaben im Format `HH:MM:SS` oder in Sekunden (z. B. `95.5`).
- Bei Fehlern liefert die Konsolenausgabe den ffmpeg-Fehlertext.

## Lizenz

Privates Nutzungsskript, keine Weitergabe von FFmpeg-Binaries enthalten.
