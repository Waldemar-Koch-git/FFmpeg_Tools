# FFmpeg SepMerger

Ein benutzerfreundliches Windows Batch-Script zum verlustfreien Trennen und Zusammenführen von Audio- und Video-Streams mit FFmpeg.

## 🎯 Features

- **Verlustfreie Verarbeitung** - Alle Operationen nutzen Stream-Copy (`-c copy`)
- **Automatische Codec-Erkennung** - Erkennt automatisch das Audioformat und wählt die passende Dateiendung
- **Interaktives Menü** - Einfache Bedienung über ein übersichtliches Auswahlmenü
- **Mehrere Funktionen:**
  - Nur Audio exportieren
  - Nur Video exportieren
  - Audio und Video gleichzeitig trennen
  - Audio und Video zusammenführen (Muxing)

## 📋 Voraussetzungen

- Windows Betriebssystem
- FFmpeg (ffmpeg.exe und optional ffprobe.exe)

## 🚀 Installation

   
# Download

- Besuche ffmpeg.org
- Lade die Windows-Version herunter (z.B. "ffmpeg-release-essentials.zip"). Siehe auch download-link.txt in dem `FFmpeg` -Ordner.
- Entpacke die heruntergeladene Datei in diesen.


## FFmpeg-Executables platzieren:

- Navigiere im entpackten FFmpeg-Ordner zum bin-Verzeichnis
- Kopiere ffmpeg.exe in den FFmpeg-Unterordner des Projekts
- Kopiere optional auch ffprobe.exe (für bessere Codec-Erkennung)

```
ffmpeg-sepmerger/
│
├── FFmpegSepMerger.bat
├── README.md
└── FFmpeg/
    ├── ffmpeg.exe
    └── ffprobe.exe (optional, aber empfohlen)
```
	
💻 Verwendung

1. Starte die Batch-Datei durch Doppelklick auf FFmpegSepMerger.bat

2. Wähle eine der folgenden Optionen:

```
[1] Nur Audio exportieren (verlustfrei)
[2] Nur Video exportieren (verlustfrei)
[3] Audio und Video trennen (verlustfrei)
[4] Audio und Video muxen (zusammenfügen)
[5] Beenden
```	

3. Folge den Anweisungen im Menü


# Beispiele

### Audio extrahieren:

- Wähle Option [1]
- Gib den Dateinamen ein (z.B. meinvideo.mp4 oder C:\Videos\meinvideo.mp4) oder per Drag&Drop die Datei in das Fenster ziehen.
- Die Audiodatei wird mit automatisch erkannter Endung gespeichert (z.B. meinvideo_audio.aac)

### Video ohne Audio exportieren:

- Wähle Option [2]
- Gib den Dateinamen ein oder per Drag&Drop die Datei in das Fenster ziehen.
- Das Video wird als dateiname_video.mp4 gespeichert

### Audio und Video trennen:

- Wähle Option [3]
- Beide Streams werden gleichzeitig in separate Dateien exportiert (split)

### Audio und Video zusammenführen:

- Wähle Option [4]
- Gib den Pfad zur Videodatei ein oder per Drag&Drop die Videodatei in das Fenster ziehen.
- Gib den Pfad zur Audiodatei ein oder per Drag&Drop die Audiodatei in das Fenster ziehen.
- Wähle einen Namen für die Ausgabedatei (z.B. output.mp4)


# 🎵 Unterstützte Audioformate

Das Script erkennt automatisch folgende Audiocodecs und wählt die passende Dateiendung:

| Codec | Dateiendung |
|-------|-------------|
| AAC | `.aac` |
| MP3 | `.mp3` |
| FLAC | `.flac` |
| Opus | `.opus` |
| Vorbis | `.ogg` |
| AC3 | `.ac3` |
| E-AC3 | `.eac3` |
| DTS | `.dts` |
| Andere | `.mka` (Matroska Audio) |

# 📁 Dateistruktur

```
FFmpeg-SepMerger/
│
├── FFmpegSepMerger.bat    # Haupt-Script
├── README.md               # Diese Datei
└── FFmpeg/                 # FFmpeg-Unterordner
    ├── ffmpeg.exe          # FFmpeg Executable (selbst hinzufügen)
    └── ffprobe.exe         # FFprobe Executable (optional, empfohlen)
```

# ⚙️ Technische Details
- Encoding: UTF-8 (chcp 65001)
- Verarbeitungsmethode: Stream-Copy (keine Neucodierung)
- Codec-Erkennung: Primär über ffprobe, Fallback auf ffmpeg
- Fehlerbehandlung: Prüfung auf Dateiexistenz und FFmpeg-Verfügbarkeit
- FFmpeg-Pfad: Verwendet Unterordner FFmpeg\ für die Executables

# 🔧 Erweiterte Nutzung
Dateien per Drag & Drop

Du kannst Videodateien auch direkt auf die .bat-Datei ziehen, allerdings öffnet sich dann zuerst das Menü.
Absolute und relative Pfade

    Relative Pfade: meinvideo.mp4 (Datei im selben Ordner)
    Absolute Pfade: C:\Users\Name\Videos\meinvideo.mp4
    Netzwerkpfade: \\Server\Freigabe\video.mp4


# ❗ Fehlerbehebung

### "Der Ordner 'FFmpeg' wurde nicht gefunden"

- Erstelle einen Unterordner namens FFmpeg im selben Verzeichnis wie die Batch-Datei
- Achte auf die korrekte Schreibweise (Groß-/Kleinschreibung)

### "ffmpeg.exe wurde im FFmpeg-Ordner nicht gefunden"

- Stelle sicher, dass ffmpeg.exe im FFmpeg-Unterordner liegt
- Prüfe den Pfad: [Dein Projektordner]\FFmpeg\ffmpeg.exe
- Die Fehlermeldung zeigt den erwarteten Pfad an

### "Datei wurde nicht gefunden"

- Gib den vollständigen Pfad zur Datei an (z.B. C:\Videos\meinvideo.mp4)
- Oder lege die zu verarbeitende Datei in denselben Ordner wie das Script
- Verwende bei Pfaden mit Leerzeichen Anführungszeichen

### "Kein Audio-Stream gefunden"

- Die Eingabedatei enthält keine Audiospur
- Prüfe die Datei mit einem Media-Player (z.B. VLC)

### "FFprobe nicht gefunden - verwende Basis-Erkennung"

- Dies ist nur eine Info, keine Fehlermeldung
- Das Script funktioniert auch ohne ffprobe.exe
- Für bessere Codec-Erkennung: Kopiere ffprobe.exe in den FFmpeg-Ordner

# 📝 Lizenz

Dieses Projekt steht unter der MIT-Lizenz - siehe LICENSE Datei für Details.