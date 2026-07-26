# FFmpeg Multi-Tool

Tool zum Schneiden, Trennen, Muxen, Rotieren und Konvertieren von
Video-/Audiodateien auf Basis von FFmpeg. Enthält zwei gleichwertige
Varianten mit identischem Funktionsumfang:

| Variante | Datei | Voraussetzung |
|---|---|---|
| Batch (nur Windows) | `FFmpeg_MultiTool_win.bat` | `cmd.exe` |
| Python (Windows, Linux, macOS) | `ffmpeg_multitool.py` | Python 3.9+ |

Die Python-Variante geht robuster mit Sonderzeichen in Dateinamen um
(Klammern, `&`, `%`, Umlaute etc.), da FFmpeg-Argumente dort als Liste statt
als Shell-String übergeben werden. Wer kein Python installieren möchte,
kann weiterhin die Batch-Datei verwenden.

## Voraussetzungen

- FFmpeg (und optional FFprobe für erweiterte Codec-Erkennung)
- **Batch-Variante:** Windows mit `cmd.exe`
- **Python-Variante:** Python 3.9 oder neuer ([python.org](https://www.python.org/downloads/)),
  unter Windows beim Setup „Add Python to PATH“ aktivieren

## Installation

### Batch-Variante (Windows)

1. Ordner `FFmpeg` neben `FFmpeg_MultiTool_win.bat` anlegen.
2. `ffmpeg.exe` (und optional `ffprobe.exe`) in diesen Ordner legen.

```
FFmpeg_MultiTool_win.bat
FFmpeg/
  ffmpeg.exe
  ffprobe.exe   (optional)
```

### Python-Variante (Windows, Linux, macOS)

`ffmpeg_multitool.py` sucht FFmpeg an zwei Stellen, in dieser Reihenfolge:

1. **Lokaler Ordner** `FFmpeg` neben dem Skript (portabel, wie bei der
   Batch-Variante) – unter Windows `ffmpeg.exe`/`ffprobe.exe`, unter
   Linux/macOS `ffmpeg`/`ffprobe` ohne Dateiendung.
2. **Systemweite Installation** im PATH, z. B.:
   ```
   sudo apt install ffmpeg     # Debian/Ubuntu
   brew install ffmpeg         # macOS
   ```

Es reicht also entweder ein lokaler `FFmpeg`-Ordner **oder** eine
systemweite FFmpeg-Installation – ein Vorhandensein von beidem ist nicht
nötig. Wer beide Skripte im selben Repo nutzt, kann sich unter Windows
einen gemeinsamen `FFmpeg`-Ordner teilen:

```
FFmpeg_MultiTool_win.bat
ffmpeg_multitool.py
FFmpeg/
  ffmpeg.exe
  ffprobe.exe   (optional)
```

## Verwendung

**Batch:** `FFmpeg_MultiTool_win.bat` per Doppelklick starten, oder eine Datei
direkt auf das Skript ziehen, um sie als aktive Eingabedatei zu übernehmen.

**Python:**
- Windows: `python ffmpeg_multitool.py` in der Kommandozeile, oder Datei
  aufs Skript ziehen (falls `.py`-Dateien mit Python verknüpft sind).
- Linux/macOS: `python3 ffmpeg_multitool.py` im Terminal, optional mit
  Eingabedatei als Argument: `python3 ffmpeg_multitool.py video.mp4`

Im Hauptmenü stehen bei beiden Varianten folgende Funktionen zur
Verfügung:

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
- Die Batch-Variante kann bei Dateinamen mit Klammern (z. B.
  `Video (1).mp4`) in seltenen Fällen an Grenzen von `cmd.exe` stoßen; die
  Python-Variante ist davon nicht betroffen.

## Lizenz

Privates Nutzungsskript, keine Weitergabe von FFmpeg-Binaries enthalten.
