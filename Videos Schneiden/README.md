# FFmpeg Video-Schnitt Tool

Ein benutzerfreundliches Windows Batch-Script zum präzisen, verlustfreien Schneiden von Videos mit FFmpeg.

## 🎯 Features

- **Verlustfreie Verarbeitung** - Alle Operationen nutzen Stream-Copy (`-c copy`) ohne Neucodierung
- **Drag & Drop Unterstützung** - Ziehe Videodateien direkt ins Fenster
- **Intelligente Zeitberechnung** - Unterstützt HH:MM:SS und MM:SS Zeitformate
- **Automatische Dateinamen** - Sinnvolle Standard-Ausgabenamen mit Möglichkeit zur Anpassung
- **Drei Schnitt-Modi**:
   - Anfang abschneiden (ab Zeitpunkt X behalten)
   - Mittleren Teil entfernen (Bereich zwischen zwei Zeitpunkten löschen)
   - Ende abschneiden (bis Zeitpunkt X behalten)



## 📋 Voraussetzungen

- Windows Betriebssystem
- FFmpeg (ffmpeg.exe und optional ffprobe.exe)

# 🚀 Installation
   
## Download

- Besuche ffmpeg.org
- Lade die Windows-Version herunter (z.B. "ffmpeg-release-essentials.zip"). Siehe auch download-link.txt in dem `FFmpeg` -Ordner.
- Entpacke die heruntergeladene Datei in diesen.


### FFmpeg-Executables platzieren:

- Navigiere im entpackten FFmpeg-Ordner zum bin-Verzeichnis
- Kopiere ffmpeg.exe in den FFmpeg-Unterordner des Projekts
- Kopiere optional auch ffprobe.exe (für bessere Codec-Erkennung)

```
FFmpeg-Video-Schnitt/
│
├── FFmpeg Video-Schnitt.bat
├── README.md
└── FFmpeg/
    ├── ffmpeg.exe
    ├── ffprobe.exe (optional)
    └── download-link.txt
```
	
# 💻 Verwendung

1. Starte die Batch-Datei durch Doppelklick auf `FFmpeg Video-Schnitt.bat`

2. **ODER** ziehe eine Videodatei direkt ins Terminal

## Menü
```
[1] Anfang abschneiden
[2] Mittleren Teil (oder dazwischen) abschneiden
[3] Endstück abschneiden
[4] Beenden
```	

3. Folge den Anweisungen im Menü


## Beispiele

### Anfang abschneiden

Szenario: Intro von 1 Minute 41 Sekunden entfernen

1. Wähle Option [1]
2.  Gib den Dateinamen ein (z.B. meinvideo.mp4) oder nutze Drag & Drop
3. Eingabe: 00:01:41 (Video startet ab dieser Stelle)
4. Ausgabe: meinvideo_anfang_geschnitten.mp4

### Mittleren Teil entfernen

**Szenario:** Werbung von 01:41 bis 02:03 entfernen

1. Wähle Option [2]
2. Gib den Dateinamen ein oder nutze Drag & Drop
3. Startzeit des zu löschenden Bereichs: 00:01:41
4. Endzeit des zu löschenden Bereichs: 00:02:03
5. Das Video wird in zwei Teile geschnitten und zusammengefügt
6. Ausgabe: meinvideo_mitte_geschnitten.mkv

**Hinweis:** Bei Option [2] werden temporäre .mkv-Dateien verwendet, um Kompatibilitätsprobleme beim Zusammenfügen zu vermeiden.


### Ende abschneiden

**Szenario:** Nur die ersten 2 Minuten und 3 Sekunden behalten

1. Wähle Option [3]
2. Gib den Dateinamen ein oder nutze Drag & Drop
3. Letzte Sekunde, die behalten werden soll: 00:02:03
4. Ausgabe: meinvideo_ende_geschnitten.mp4

## ⏱️ Zeitformate

Das Script akzeptiert folgende Zeitformate:

| Format | Beispiel | Bedeutung |
|--------|----------|-----------|
| HH:MM:SS | `01:30:45` | 1 Stunde, 30 Minuten, 45 Sekunden |
| MM:SS | `05:30` | 5 Minuten, 30 Sekunden |
| Sekunden | `90` | 90 Sekunden (1:30) |

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
- Verarbeitungsmethode: Stream-Copy (keine Neucodierung, verlustfrei)
- Temporäre Dateien: Werden automatisch im %TEMP%-Verzeichnis erstellt und gelöscht
- Ausgabeformat:
  - Option 1 & 3: Behält Original-Containerformat bei
  - Option 2: Nutzt .mkv für maximale Kompatibilität beim Zusammenfügen
- Fehlerbehandlung: Prüfung auf Dateiexistenz, FFmpeg-Verfügbarkeit und erfolgreiche Ausführung


# 🔧 Erweiterte Nutzung

## Dateipfade

- Relative Pfade: meinvideo.mp4 (Datei im selben Ordner)
- Absolute Pfade: C:\Users\Name\Videos\meinvideo.mp4
- Netzwerkpfade: \\Server\Freigabe\video.mp4
- Pfade mit Leerzeichen: Werden automatisch behandelt (keine Anführungszeichen nötig)

## Drag & Drop

- Ziehe eine Videodatei auf die .bat-Datei, um sie direkt zu laden
- Oder ziehe die Datei ins Konsolenfenster, wenn nach dem Dateinamen gefragt wird

## Benutzerdefinierte Ausgabenamen

Bei jedem Schnitt kannst du den vorgeschlagenen Dateinamen überschreiben:

```text
Ausgabedatei wird sein: meinvideo_anfang_geschnitten.mp4
Anderen Namen verwenden? (Enter für Standard): mein_neues_video.mp4
```

# 🎬 Unterstützte Formate

Das Script funktioniert mit allen von FFmpeg unterstützten Videoformaten:

- Container: MP4, MKV, AVI, MOV, FLV, WebM, WMV, etc.
- Video-Codecs: H.264, H.265/HEVC, VP8, VP9, AV1, MPEG-4, etc.
- Audio-Codecs: AAC, MP3, Opus, Vorbis, AC3, DTS, FLAC, etc.

# ❗ Fehlerbehebung

### "Der Ordner 'FFmpeg' wurde nicht gefunden"

    Erstelle einen Unterordner namens FFmpeg im selben Verzeichnis wie die Batch-Datei
    Achte auf die korrekte Schreibweise (Groß-/Kleinschreibung spielt bei Windows keine Rolle)

### "ffmpeg.exe wurde im FFmpeg-Ordner nicht gefunden"

    Stelle sicher, dass ffmpeg.exe im FFmpeg-Unterordner liegt
    Prüfe den Pfad: [Dein Projektordner]\FFmpeg\ffmpeg.exe
    Die Fehlermeldung zeigt den erwarteten Pfad an

### "Datei wurde nicht gefunden"

    Gib den vollständigen Pfad zur Datei an
    Oder lege die zu verarbeitende Datei in denselben Ordner wie das Script
    Bei Drag & Drop: Achte darauf, dass die Datei nicht verschoben/gelöscht wurde

### "Beim Schneiden ist ein Fehler aufgetreten"

    Prüfe, ob die Zeitangabe korrekt ist (nicht länger als das Video)
    Stelle sicher, dass genügend Speicherplatz vorhanden ist
    Bei Option [2]: Überprüfe, ob die Endzeit nach der Startzeit liegt
    Prüfe, ob die Ausgabedatei nicht bereits geöffnet ist

### "FFprobe nicht gefunden - verwende Basis-Funktionen"

    Dies ist nur eine Info, keine Fehlermeldung
    Das Script funktioniert auch ohne ffprobe.exe
    Für erweiterte Funktionen: Kopiere ffprobe.exe in den FFmpeg-Ordner

### Zusammenfügen schlägt fehl (Option 2)

    Manche Containerformate (z.B. MP4) unterstützen das Concat-Demuxing nicht perfekt
    Das Script nutzt .mkv als Zwischenformat für maximale Kompatibilität
    Falls Probleme auftreten: Nutze die Optionen [1] und [3] separat

# 💡 Tipps

- Keyframes beachten: Bei `-c copy` erfolgt der Schnitt am nächsten Keyframe, daher kann die tatsächliche Schnittposition leicht abweichen (meist ±1-2 Sekunden)
- Genaue Schnitte: Für frame-genaue Schnitte ist Neucodierung erforderlich (entferne `-c copy`)
- Temporäre Dateien: Bei Option [2] werden temporäre Dateien erstellt - stelle sicher, dass genug Speicherplatz verfügbar ist
- Batch-Verarbeitung: Das Script kehrt nach jedem Schnitt zum Menü zurück - ideal für mehrere Schnitte hintereinander


# 📝 Lizenz

Dieses Projekt steht unter der MIT-Lizenz.