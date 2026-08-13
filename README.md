# FFmpeg Multi-Tool

Tool zum Schneiden, Zusammensetzen, Trennen, Muxen, Rotieren und
Konvertieren von Video-/Audiodateien auf Basis von FFmpeg. Läuft unter
Windows, Linux und macOS.

| Datei | Voraussetzung |
|---|---|
| `FFmpeg_MultiTool.py` | Python 3.9+ |

Das Skript geht robust mit Sonderzeichen in Dateinamen um (Klammern, `&`,
`%`, Umlaute etc.), da FFmpeg-Argumente als Liste statt als Shell-String
übergeben werden.

## Voraussetzungen

- FFmpeg (und optional FFprobe für erweiterte Codec-Erkennung)
- Python 3.9 oder neuer ([python.org](https://www.python.org/downloads/)),
  unter Windows beim Setup „Add Python to PATH“ aktivieren

## Installation

`FFmpeg_MultiTool.py` sucht FFmpeg an zwei Stellen, in dieser Reihenfolge:

1. **Lokaler Ordner** `FFmpeg` neben dem Skript (portabel) – unter Windows
   `ffmpeg.exe`/`ffprobe.exe`, unter Linux/macOS `ffmpeg`/`ffprobe` ohne
   Dateiendung.
2. **Systemweite Installation** im PATH, z. B.:
   ```
   sudo apt install ffmpeg     # Debian/Ubuntu
   brew install ffmpeg         # macOS
   ```

Es reicht also entweder ein lokaler `FFmpeg`-Ordner **oder** eine
systemweite FFmpeg-Installation:

```
FFmpeg_MultiTool.py
FFmpeg/
  ffmpeg.exe    (unter Linux/macOS ohne .exe)
  ffprobe.exe   (optional, ohne .exe unter Linux/macOS)
```

## Verwendung

- Windows: `python FFmpeg_MultiTool.py` in der Kommandozeile, oder Datei
  aufs Skript ziehen (falls `.py`-Dateien mit Python verknüpft sind).
- Linux/macOS: `python3 FFmpeg_MultiTool.py` im Terminal, optional mit
  Eingabedatei als Argument: `python3 FFmpeg_MultiTool.py video.mp4`

Im Hauptmenü stehen folgende Funktionen zur Verfügung:

| Option | Funktion |
|---|---|
| 1 | Video schneiden (Anfang / Mitte / Ende, verlustfrei) |
| 2 | Videos zusammensetzen (mehrere Videos mergen) |
| 3 | Audio und Video trennen (verlustfrei) |
| 4 | Audio und Video zusammenfügen (Muxen) |
| 5 | Video rotieren (Metadaten oder Re-Encoding) |
| 6 | Audio konvertieren (MP3, AAC, Opus, Vorbis, FLAC, WAV) |
| 0 | Zurück / Beenden |

`0` ist in allen Menüs und Untermenüs einheitlich der Punkt für
„Zurück“ bzw. „Beenden“.

Alle Funktionen unterstützen Drag & Drop für Eingabedateien und fragen vor
dem Überschreiben vorhandener Ausgabedateien nach. Soll eine Datei nicht
überschrieben werden, kann direkt ein alternativer Dateiname eingegeben
werden – bei „Audio und Video gleichzeitig trennen“ (Option 3) gilt das
für Audio- und Video-Export unabhängig voneinander; leere Eingabe
überspringt den jeweiligen Export bewusst.

### Videos zusammensetzen (Option 2)

Fügt beliebig viele Videos in der eingegebenen Reihenfolge zu einer Datei
zusammen (Dateien nacheinander eingeben, leere Eingabe = fertig). Zwei
Methoden stehen zur Wahl:

- **Schnell (Stream-Copy):** verlustfrei, aber nur möglich, wenn alle
  Videos denselben Codec, dieselbe Auflösung und dasselbe Format haben.
- **Kompatibel (Re-Encoding):** funktioniert auch bei unterschiedlichen
  Quelldateien, dauert aber länger, da neu codiert wird (H.264 CRF 18,
  AAC 192 kbps). Alle Eingabedateien benötigen dabei Bild **und** Ton.

### Audio konvertieren (Option 6)

Unterstützte Zielformate: MP3, AAC/M4A, Opus, Vorbis/OGG (jeweils mit
auswählbarer Bitrate/Qualitätsstufe oder eigener Bitrate), FLAC (mit
wählbarem Kompressionslevel 0–8, Standard 5) und WAV (16-bit oder 24-bit
PCM).

- **Cover-Art bleibt erhalten:** Ein eingebettetes Album-Cover wird beim
  Konvertieren automatisch als Bildanhang übernommen (gilt nicht für WAV,
  das keine Bildanhänge unterstützt). Ist kein Cover vorhanden oder lässt
  es sich nicht übernehmen, wird automatisch ohne Cover weiterkonvertiert.
- **Passt die Dateiendung nicht zum gewählten Format** (z. B. eigener
  Dateiname `song.mp3` bei zuvor gewähltem FLAC), warnt das Programm und
  bietet an, die Endung automatisch zu korrigieren.
- Fehlt der für das gewählte Format nötige Encoder in der installierten
  FFmpeg-Version (z. B. `libopus`), wird das vorab gemeldet, statt erst
  beim Ausführen mit einer FFmpeg-Fehlermeldung zu scheitern.

### Muxen (Option 4)

Beim Zusammenfügen von Video- und Audiodatei kann das Audio wahlweise
unverändert übernommen oder – z. B. bei WAV-Audio, das nicht direkt in
MP4 passt – nach MP3, AAC oder Opus konvertiert werden.

## Hinweise

- Verlustfreie Schnitte (Stream-Copy) sind an Keyframes ausgerichtet;
  geringe Abweichungen vom exakten Zeitstempel sind möglich.
- Zeitangaben im Format `HH:MM:SS` oder in Sekunden (z. B. `95.5`). Beim
  Herausschneiden eines mittleren Bereichs (Option 1 → „Mittleren Teil
  herausschneiden“) muss die Endzeit nach der Startzeit liegen, das
  Programm prüft das direkt bei der Eingabe.
- Bei Fehlern liefert die Konsolenausgabe den ffmpeg-Fehlertext.
- Wird bei einem eigenen Ausgabedateinamen nur ein Dateiname ohne Pfad
  angegeben (z. B. `neu.mp4`), landet die Datei automatisch im selben
  Ordner wie der Eingabedatei – nicht im Arbeitsverzeichnis, in dem das
  Programm gestartet wurde.
- **Strg+C** bricht nur die gerade laufende Aktion ab und kehrt zum
  zuletzt geöffneten Menü zurück; das Programm wird dabei nicht beendet.
  Zum Beenden bitte den Menüpunkt `[0]` verwenden.

## Lizenz

Privates Nutzungsskript, keine Weitergabe von FFmpeg-Binaries enthalten.
