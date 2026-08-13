#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FFmpeg Multi-Tool (Python-Version)
Vereint: Video-Schnitt, Audio/Video-Trennung, Muxen, Rotation, Audio-Konvertierung
(MP3, AAC, Opus, Vorbis, FLAC, WAV)

Funktioniert unter Windows, Linux und macOS. FFmpeg wird an zwei Stellen
gesucht (in dieser Reihenfolge):
  1. Lokaler Unterordner "FFmpeg" neben diesem Skript (portable Variante,
     unter Windows ffmpeg.exe/ffprobe.exe, sonst ffmpeg/ffprobe ohne
     Endung) - genau wie bei der .bat-Version.
  2. Systemweit installiertes FFmpeg im PATH (z.B. nach
     "sudo apt install ffmpeg" unter Linux oder "brew install ffmpeg"
     unter macOS).

Vorteil gegenüber der Batch-Version: Dateinamen mit Klammern, "&", "%%",
Umlauten etc. funktionieren hier ganz normal, weil Python Pfade als echte
Strings behandelt und FFmpeg-Argumente als Liste übergibt (kein
Shell-Parsing, kein Quoting-Aerger).
"""

from __future__ import annotations

import functools
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Grundkonfiguration
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(sys.argv[0]).resolve().parent
FFMPEG_DIR = SCRIPT_DIR / "FFmpeg"

_EXE_SUFFIX = ".exe" if os.name == "nt" else ""


def _resolve_binary(name: str) -> Path:
    """Sucht ein FFmpeg-Binary zuerst im lokalen FFmpeg-Ordner, danach im
    System-PATH. Gibt den lokalen Pfad zurück, falls gar nichts gefunden
    wird (für eine aussagekräftige Fehlermeldung in check_ffmpeg)."""
    local = FFMPEG_DIR / f"{name}{_EXE_SUFFIX}"
    if local.is_file():
        return local
    from_path = shutil.which(name)
    if from_path:
        return Path(from_path)
    return local


FFMPEG = _resolve_binary("ffmpeg")
FFPROBE = _resolve_binary("ffprobe")

AUDIO_EXT_MAP = {
    "aac": "aac",
    "mp3": "mp3",
    "flac": "flac",
    "opus": "opus",
    "vorbis": "ogg",
    "ac3": "ac3",
    "eac3": "eac3",
    "dts": "dts",
}

MP3_BITRATES = {
    "1": (["-c:a", "libmp3lame", "-b:a", "128k"], "128 kbps CBR"),
    "2": (["-c:a", "libmp3lame", "-b:a", "160k"], "160 kbps CBR"),
    "3": (["-c:a", "libmp3lame", "-b:a", "192k"], "192 kbps CBR"),
    "4": (["-c:a", "libmp3lame", "-b:a", "256k"], "256 kbps CBR"),
    "5": (["-c:a", "libmp3lame", "-b:a", "320k"], "320 kbps CBR"),
    "6": (["-c:a", "libmp3lame", "-q:a", "0"], "VBR V0 (~245 kbps)"),
    "7": (["-c:a", "libmp3lame", "-q:a", "2"], "VBR V2 (~190 kbps)"),
    "8": (["-c:a", "libmp3lame", "-q:a", "4"], "VBR V4 (~165 kbps)"),
}

AAC_BITRATES = {
    "1": (["-c:a", "aac", "-b:a", "128k"], "128 kbps"),
    "2": (["-c:a", "aac", "-b:a", "160k"], "160 kbps"),
    "3": (["-c:a", "aac", "-b:a", "192k"], "192 kbps"),
    "4": (["-c:a", "aac", "-b:a", "256k"], "256 kbps"),
    "5": (["-c:a", "aac", "-b:a", "320k"], "320 kbps"),
}

OPUS_BITRATES = {
    "1": (["-c:a", "libopus", "-b:a", "64k"], "64 kbps (Sprache/Podcast)"),
    "2": (["-c:a", "libopus", "-b:a", "96k"], "96 kbps"),
    "3": (["-c:a", "libopus", "-b:a", "128k"], "128 kbps (Standard, sehr gut)"),
    "4": (["-c:a", "libopus", "-b:a", "160k"], "160 kbps"),
    "5": (["-c:a", "libopus", "-b:a", "192k"], "192 kbps"),
    "6": (["-c:a", "libopus", "-b:a", "256k"], "256 kbps (max. empfohlen)"),
}

VORBIS_BITRATES = {
    "1": (["-c:a", "libvorbis", "-q:a", "3"], "~112 kbps (Qualität 3)"),
    "2": (["-c:a", "libvorbis", "-q:a", "5"], "~160 kbps (Qualität 5, Standard)"),
    "3": (["-c:a", "libvorbis", "-q:a", "7"], "~224 kbps (Qualität 7)"),
    "4": (["-c:a", "libvorbis", "-q:a", "9"], "~320 kbps (Qualität 9, maximal)"),
}

TIME_RE = re.compile(r"^[0-9:.]+$")

# Wird beim Start ggf. mit einer per Drag & Drop übergebenen Datei belegt
_dropped_file: str | None = None


# ---------------------------------------------------------------------------
# Kleine Hilfsfunktionen für die Konsole
# ---------------------------------------------------------------------------

def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def pause() -> None:
    input("\nWeiter mit beliebiger Taste (Enter)...")


def header(title: str) -> None:
    clear()
    print("=" * 51)
    print(f"  {title}")
    print("=" * 51)
    print()


def ask(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        print()
        sys.exit(0)
    # KeyboardInterrupt (Strg+C) wird bewusst NICHT hier abgefangen,
    # sondern nach oben durchgereicht: die jeweilige Menü-Schleife fängt
    # sie ab und kehrt zum Menü zurück, statt das ganze Programm zu
    # beenden (siehe run_menu_loop / main_menu / menu_*).


def interrupted() -> None:
    """Einheitliche Meldung, wenn eine Aktion per Strg+C abgebrochen wurde."""
    print("\n\n[ABBRUCH] Vorgang mit Strg+C abgebrochen - zurück zum Menü.")


# ---------------------------------------------------------------------------
# FFmpeg-Grundcheck
# ---------------------------------------------------------------------------

def check_ffmpeg() -> None:
    ffmpeg_name = f"ffmpeg{_EXE_SUFFIX}"
    if not FFMPEG.is_file():
        print(f'[FEHLER] "{ffmpeg_name}" wurde nicht gefunden!')
        print(f'Gesucht wurde im Ordner "{FFMPEG_DIR}" sowie im System-PATH.')
        print()
        print("Lösungsmöglichkeiten:")
        print(f'  - Unterordner "FFmpeg" neben diesem Skript anlegen und')
        print(f"    {ffmpeg_name} (und optional ffprobe{_EXE_SUFFIX}) dort hineinlegen,")
        print("    oder")
        if os.name == "nt":
            print("  - FFmpeg systemweit installieren und zum PATH hinzufügen")
        else:
            print("  - FFmpeg über den Paketmanager installieren, z.B.:")
            print("      sudo apt install ffmpeg      (Debian/Ubuntu)")
            print("      brew install ffmpeg          (macOS)")
        pause()
        sys.exit(1)

    print(f"[INFO] FFmpeg gefunden: {FFMPEG}")
    if FFPROBE.is_file():
        print(f"[INFO] FFprobe gefunden: {FFPROBE} - erweiterte Codec-Erkennung aktiv")
    else:
        print("[INFO] FFprobe nicht gefunden - Basis-Codec-Erkennung wird verwendet")
    print()


def cleanup_temp_files() -> None:
    for f in Path(tempfile.gettempdir()).glob("ffmpegmt_*"):
        try:
            f.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Datei-Ein-/Ausgabe-Helfer
# ---------------------------------------------------------------------------

def get_input_file(label: str = "Datei") -> Path | None:
    """Fragt eine Eingabedatei ab. Nutzt zuerst eine per Drag & Drop
    übergebene Datei, danach manuelle Eingabe. Gibt None zurück, wenn
    die Datei nicht existiert."""
    global _dropped_file
    if _dropped_file:
        raw = _dropped_file
        print(f"Verwende per Drag & Drop übergebene Datei als {label}: {raw}")
        _dropped_file = None
    else:
        print(f"Tipp: {label} per Drag & Drop in dieses Fenster ziehen und Enter drücken,")
        raw = ask(f"oder Dateiname/Pfad eingeben ({label}): ")

    raw = raw.strip().strip('"')
    path = Path(raw)
    if not path.is_file():
        print()
        print(f'[FEHLER] Datei "{raw}" wurde nicht gefunden!')
        return None
    return path


def get_file_info(path: Path) -> tuple[Path, str, str]:
    """Gibt (Verzeichnis, Basisname, Endung-mit-Punkt) zurück."""
    return path.parent, path.stem, path.suffix


def ask_custom_output(default_output: Path) -> Path | None:
    """Schlägt einen Standard-Ausgabepfad vor und erlaubt einen eigenen
    Namen. Prüft, dass das Zielverzeichnis existiert.

    Wird nur ein blanker Dateiname ohne Pfad eingegeben (z.B. "neu.mp4"),
    wird dieser im selben Ordner wie der Standard-Vorschlag gespeichert -
    NICHT im aktuellen Arbeitsverzeichnis des Programms. Das verhindert
    "Permission denied"-Fehler, wenn das Programm z.B. aus einem
    schreibgeschützten Ordner (Programme, System32 o.ä.) gestartet wurde.
    """
    output = default_output
    while True:
        print()
        print(f"Ausgabedatei: {output}")
        custom = ask("Anderen Dateinamen verwenden? (Enter für Standard): ").strip().strip('"')
        if custom:
            custom_path = Path(custom)
            if custom_path.is_absolute() or len(custom_path.parts) > 1:
                output = custom_path
            else:
                # Nur ein Dateiname ohne Verzeichnisanteil -> gleicher Ordner
                # wie der Standard-Ausgabevorschlag (nicht das cwd!).
                output = default_output.parent / custom_path

        if not output.parent.is_dir():
            print()
            print(f'[FEHLER] Zielverzeichnis "{output.parent}" existiert nicht!')
            output = default_output
            continue
        return output


def resolve_conflict_output(output: Path, label: str) -> Path | None:
    """Punkt 8: Existiert die Zieldatei bereits und soll nicht überschrieben
    werden, wird - statt den Export einfach zu überspringen - nach einem
    alternativen Dateinamen gefragt. Leere Eingabe an dieser Stelle
    überspringt den Export bewusst (explizite Nutzerentscheidung). Gibt den
    finalen (konfliktfreien) Pfad zurück, oder None bei explizitem
    Ueberspringen."""
    while output.exists():
        if check_overwrite(output):
            return output
        print()
        custom = ask(f"Alternativer Dateiname für {label} (leer = Export überspringen): ").strip().strip('"')
        if not custom:
            return None
        custom_path = Path(custom)
        if custom_path.is_absolute() or len(custom_path.parts) > 1:
            output = custom_path
        else:
            output = output.parent / custom_path
    return output


def check_overwrite(path: Path) -> bool:
    """Prüft ob eine Datei bereits existiert und fragt ggf. nach.
    True = fortfahren, False = abbrechen."""
    if not path.exists():
        return True
    print()
    print(f'[HINWEIS] Die Datei "{path}" existiert bereits.')
    while True:
        choice = ask("Ueberschreiben? (J=Ja, N=Nein): ").strip().lower()
        if choice in ("j", "ja"):
            return True
        if choice in ("n", "nein"):
            return False


def parse_time_to_seconds(value: str) -> float | None:
    """Wandelt eine Zeitangabe ('SS', 'MM:SS', 'HH:MM:SS', jeweils optional
    mit Nachkommastellen) in Sekunden um. Gibt None zurück, wenn der Wert
    nicht als Zeit interpretiert werden kann (Punkt 7)."""
    parts = value.split(":")
    try:
        if len(parts) == 1:
            return float(parts[0])
        if len(parts) == 2:
            minutes, seconds = parts
            return int(minutes) * 60 + float(seconds)
        if len(parts) == 3:
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    except ValueError:
        return None
    return None


def ask_time(prompt: str) -> str:
    """Fragt eine Zeitangabe ab und wiederholt, bis das Format plausibel
    ist (nur Ziffern, ':' und '.', nicht leer)."""
    while True:
        value = ask(prompt).strip()
        if value and TIME_RE.match(value):
            return value
        print("[FEHLER] Ungültiges Zeitformat! Erlaubt sind nur Ziffern, ':' und '.'")
        print("(z.B. 00:01:41 oder 95.5).")


# ---------------------------------------------------------------------------
# FFmpeg-Aufrufe
# ---------------------------------------------------------------------------

def run_ffmpeg(args: list[str]) -> int:
    """Ruft ffmpeg mit einer Argumentliste auf (kein Shell-Parsing nötig,
    daher sind Klammern/Sonderzeichen in Dateinamen kein Problem)."""
    cmd = [str(FFMPEG), "-y"] + args
    result = subprocess.run(cmd)
    return result.returncode


def report_result(returncode: int, err_msg: str, success_msg: str) -> bool:
    if returncode != 0:
        print(f"[FEHLER] {err_msg}")
        return False
    print(f"[OK] {success_msg}")
    return True


def detect_audio_codec(path: Path) -> str | None:
    """Ermittelt den Audio-Codec einer Datei. Nutzt ffprobe falls
    vorhanden, sonst ffmpeg-Fallback über die stderr-Ausgabe.
    Dünnes Wrapper um _detect_audio_codec_cached (Punkt 6): das Ergebnis
    wird pro (aufgelöstem) Pfad gecacht, damit z.B. trennen_beide() oder
    ein erneuter Aufruf für dieselbe Datei nicht erneut ffprobe/ffmpeg
    aufruft. Die Info-Ausgabe ('Erkanntes Audioformat: ...') erfolgt aber
    bei jedem Aufruf, damit der Nutzer sie weiterhin sieht."""
    codec = _detect_audio_codec_cached(str(path.resolve()))
    if not codec:
        print("[WARNUNG] Kein Audio-Stream gefunden oder Codec konnte nicht erkannt werden!")
    else:
        print(f"Erkanntes Audioformat: {codec}")
    return codec


@functools.lru_cache(maxsize=None)
def _detect_audio_codec_cached(resolved_path: str) -> str | None:
    path = Path(resolved_path)
    codec = None
    if FFPROBE.is_file():
        cmd = [
            str(FFPROBE), "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
            codec = out or None
        except OSError:
            codec = None
    else:
        print("[INFO] ffprobe.exe nicht gefunden, verwende ffmpeg für Codec-Erkennung")
        cmd = [str(FFMPEG), "-i", str(path)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        for line in proc.stderr.splitlines():
            if "Audio:" in line:
                after = line.split("Audio:", 1)[1].strip()
                codec = after.split(",")[0].strip()
                break

    return codec


def audio_ext_for_codec(codec: str | None) -> str:
    if not codec:
        return "mka"
    return AUDIO_EXT_MAP.get(codec.lower(), "mka")


def select_bitrate(presets: dict, title: str, codec_args: list[str] | None = None
                    ) -> tuple[list[str], str] | None:
    """Generisches Bitraten-/Qualitäts-Auswahlmenu (für AAC, Opus, Vorbis
    etc.). 'presets' hat dasselbe Format wie MP3_BITRATES. Ist 'codec_args'
    gesetzt, wird zusätzlich eine Option für eine benutzerdefinierte
    Bitrate (in kbps) angeboten. Gibt None zurück, wenn der Nutzer
    zurück möchte."""
    custom_key = str(max(int(k) for k in presets) + 1)
    while True:
        header(title)
        for key in sorted(presets, key=int):
            _, label = presets[key]
            print(f"  [{key}] {label}")
        if codec_args is not None:
            print(f"  [{custom_key}] Eigene Bitrate eingeben")
        print("  [0] Zurück")
        print()
        choice = ask("Deine Auswahl: ").strip()

        if choice in presets:
            return presets[choice]

        if codec_args is not None and choice == custom_key:
            print()
            print("Empfohlene Werte: 96, 128, 160, 192, 224, 256, 320")
            custom = ask("Bitrate in kbps eingeben: ").strip()
            if custom.isdigit():
                return (codec_args + ["-b:a", f"{custom}k"],
                         f"{custom} kbps (benutzerdefiniert)")
            print()
            print("[FEHLER] Ungültige Eingabe! Bitte nur eine Zahl eingeben.")
            pause()
            continue

        if choice == "0":
            return None

        print("Ungültige Auswahl!")
        pause()


# Tabellengetriebene Definition der verlustbehafteten Zielformate (Punkt 4).
# Jeder Eintrag beschreibt eine Zeile im Zielformat-Menü sowie das
# zugehörige Bitraten-/Qualitätsmenü. Ein neues Format hinzuzufügen
# bedeutet nur noch: neuen Eintrag ergänzen, keine neue if-Kette nötig.
AUDIO_FORMATS = [
    {"key": "1", "ext": "mp3", "label": "MP3         (verlustbehaftet, universell kompatibel)",
     "presets": MP3_BITRATES, "menu_title": "MP3-Bitrate auswählen",
     "codec_args": ["-c:a", "libmp3lame"]},
    {"key": "2", "ext": "m4a", "label": "AAC / M4A   (verlustbehaftet, gut für Apple-Geräte)",
     "presets": AAC_BITRATES, "menu_title": "AAC-Bitrate auswählen",
     "codec_args": ["-c:a", "aac"]},
    {"key": "3", "ext": "opus", "label": "Opus        (verlustbehaftet, beste Qualität pro kbps)",
     "presets": OPUS_BITRATES, "menu_title": "Opus-Bitrate auswählen",
     "codec_args": ["-c:a", "libopus"]},
    {"key": "4", "ext": "ogg", "label": "Vorbis/OGG  (verlustbehaftet, freies Format)",
     "presets": VORBIS_BITRATES, "menu_title": "Vorbis-Qualität auswählen",
     "codec_args": ["-c:a", "libvorbis"]},
]
AUDIO_FORMATS_BY_KEY = {fmt["key"]: fmt for fmt in AUDIO_FORMATS}


def select_flac_options() -> tuple[str, list[str], str] | None:
    """FLAC-Kompressionslevel wählen (Punkt 10). 0 = schnell/grösser,
    8 = langsam/kleiner, Standard ist 5. Gibt None zurück bei 'Zurück'."""
    while True:
        header("FLAC-Kompressionslevel wählen")
        print("Level 0 = schnellste Kompression, grösste Datei")
        print("Level 8 = langsamste Kompression, kleinste Datei")
        print("(Die Audioqualität ist bei FLAC in jedem Level verlustfrei identisch)")
        print()
        print("  [1] Standard (Level 5)")
        print("  [2] Eigenes Level eingeben (0-8)")
        print("  [0] Zurück")
        print()
        choice = ask("Deine Auswahl: ").strip()

        if choice == "1":
            return "flac", ["-c:a", "flac", "-compression_level", "5"], "FLAC Level 5 (Standard)"

        if choice == "2":
            level = ask("Kompressionslevel eingeben (0-8): ").strip()
            if level.isdigit() and 0 <= int(level) <= 8:
                return ("flac", ["-c:a", "flac", "-compression_level", level],
                         f"FLAC Level {level}")
            print()
            print("[FEHLER] Bitte eine Zahl zwischen 0 und 8 eingeben.")
            pause()
            continue

        if choice == "0":
            return None

        print("Ungültige Auswahl!")
        pause()


def select_wav_options() -> tuple[str, list[str], str] | None:
    """WAV-Bittiefe wählen (Punkt 11). Gibt None zurück bei 'Zurück'."""
    while True:
        header("WAV-Bittiefe wählen")
        print("  [1] 16-bit PCM  (Standard, CD-Qualität)")
        print("  [2] 24-bit PCM  (höhere Auflösung, grössere Datei)")
        print("  [0] Zurück")
        print()
        choice = ask("Deine Auswahl: ").strip()

        if choice == "1":
            return "wav", ["-c:a", "pcm_s16le"], "WAV PCM 16-bit (verlustfrei)"

        if choice == "2":
            return "wav", ["-c:a", "pcm_s24le"], "WAV PCM 24-bit (verlustfrei)"

        if choice == "0":
            return None

        print("Ungültige Auswahl!")
        pause()


def select_audio_format() -> tuple[str, list[str], str] | None:
    """Zeigt das Zielformat-Menü für die Audio-Konvertierung an und
    anschliessend (falls zutreffend) das passende Bitraten-/Qualitätsmenü.
    Gibt (Dateiendung, ffmpeg-Codec-Parameter, Info-Text) zurück, oder
    None, wenn der Nutzer zurück zum Hauptmenü möchte."""
    while True:
        header("Audio konvertieren - Zielformat wählen")
        for fmt in AUDIO_FORMATS:
            print(f"  [{fmt['key']}] {fmt['label']}")
        print("  [5] FLAC        (verlustfrei, komprimiert)")
        print("  [6] WAV         (verlustfrei, unkomprimiert)")
        print("  [0] Zurück zum Hauptmenü")
        print()
        choice = ask("Zielformat wählen: ").strip()

        if choice in AUDIO_FORMATS_BY_KEY:
            fmt = AUDIO_FORMATS_BY_KEY[choice]
            picked = select_bitrate(fmt["presets"], fmt["menu_title"], codec_args=fmt["codec_args"])
            if picked is None:
                continue
            params, info = picked
            return fmt["ext"], params, info

        if choice == "5":
            picked = select_flac_options()
            if picked is None:
                continue
            return picked

        if choice == "6":
            picked = select_wav_options()
            if picked is None:
                continue
            return picked

        if choice == "0":
            return None

        print("Ungültige Auswahl!")
        pause()


# ---------------------------------------------------------------------------
# Extension-Check, Cover-Art-Erhalt, Encoder-Verfügbarkeit (Punkte 1, 2, 9)
# ---------------------------------------------------------------------------

def confirm_extension(output: Path, expected_ext: str) -> Path:
    """Punkt 1: Warnt, wenn die Endung der Ausgabedatei nicht zum gewählten
    Codec passt (z.B. FLAC-Daten in einer .mp3-Datei landen würden) und
    bietet an, die Endung automatisch zu korrigieren."""
    actual_ext = output.suffix.lstrip(".").lower()
    if actual_ext == expected_ext.lower():
        return output

    print()
    print(f'[WARNUNG] Die Endung ".{actual_ext}" passt nicht zum gewählten Format '
          f'(erwartet: ".{expected_ext}").')
    print("FFmpeg würde die Audiodaten trotzdem in diesen Container packen -")
    print("das Ergebnis wäre je nach Player fehlerhaft oder gar nicht abspielbar.")
    fix = ask(f'Endung automatisch zu ".{expected_ext}" korrigieren? (J=Ja, N=Nein, behalten): ').strip().lower()
    if fix in ("j", "ja"):
        return output.with_suffix(f".{expected_ext}")
    return output


def convert_with_cover_preservation(path: Path, codec_params: list[str],
                                     output: Path, target_ext: str) -> int:
    """Punkt 2: Bei der Audio-Konvertierung entfernte bislang '-vn' *alle*
    Videospuren - inklusive eingebettetem Album-Cover (das ffmpeg technisch
    als Videostream führt). Hier wird zuerst versucht, ein vorhandenes
    Cover als 'attached_pic' zu übernehmen. WAV kennt keine Bildanhänge,
    daher wird dort direkt ohne Cover konvertiert. Schlägt der Versuch mit
    Cover fehl (z.B. kein Cover vorhanden, Zielformat ungeeignet), wird
    automatisch ohne Cover (-vn) erneut versucht."""
    if target_ext != "wav":
        rc = run_ffmpeg([
            "-i", str(path), "-map", "0:a", "-map", "0:v?",
            "-c:v", "copy", "-disposition:v", "attached_pic",
            *codec_params, str(output),
        ])
        if rc == 0:
            return rc
        print("[INFO] Konvertierung mit Cover-Erhalt nicht möglich, versuche ohne Cover...")

    return run_ffmpeg(["-i", str(path), *codec_params, "-vn", str(output)])


@functools.lru_cache(maxsize=None)
def _get_available_encoders() -> frozenset[str]:
    """Fragt einmalig die Liste der in dieser ffmpeg-Version verfügbaren
    Encoder ab und cacht das Ergebnis für den Rest des Programmlaufs."""
    try:
        proc = subprocess.run([str(FFMPEG), "-hide_banner", "-encoders"],
                               capture_output=True, text=True)
        names = re.findall(r"^\s*[A-Z\.]{6}\s+(\S+)", proc.stdout, re.MULTILINE)
        return frozenset(names)
    except OSError:
        return frozenset()


def warn_if_encoder_missing(codec_params: list[str]) -> bool:
    """Punkt 9: Prüft, ob der in codec_params verwendete Encoder (nach
    '-c:a') in der vorhandenen ffmpeg-Version enthalten ist, *bevor* die
    Konvertierung gestartet wird. Gibt False zurück, wenn der Nutzer
    daraufhin abbrechen möchte."""
    if "-c:a" not in codec_params:
        return True
    encoder = codec_params[codec_params.index("-c:a") + 1]
    if encoder.startswith("pcm_") or encoder == "copy":
        return True  # PCM/Copy sind praktisch immer vorhanden

    available = _get_available_encoders()
    if not available or encoder in available:
        return True  # Liste leer (Abfrage fehlgeschlagen) -> im Zweifel weitermachen

    print()
    print(f'[WARNUNG] Der Encoder "{encoder}" scheint in dieser ffmpeg-Version')
    print("nicht enthalten zu sein. Die Konvertierung würde vermutlich mit einer")
    print("ffmpeg-Fehlermeldung fehlschlagen.")
    choice = ask("Trotzdem versuchen? (J=Ja, N=Nein/Abbrechen): ").strip().lower()
    return choice in ("j", "ja")


# ---------------------------------------------------------------------------
# 1) VIDEO SCHNEIDEN
# ---------------------------------------------------------------------------

def menu_schnitt() -> None:
    while True:
        header("Video schneiden")
        print("  [1] Anfang abschneiden")
        print("  [2] Mittleren Teil herausschneiden")
        print("  [3] Ende abschneiden (nur Anfangsteil behalten)")
        print("  [0] Zurück zum Hauptmenü")
        print()
        try:
            choice = ask("Deine Auswahl: ").strip()

            if choice == "1":
                schnitt_anfang()
            elif choice == "2":
                schnitt_mitte()
            elif choice == "3":
                schnitt_ende()
            elif choice == "0":
                return
            else:
                print("Ungültige Auswahl!")
                pause()
        except KeyboardInterrupt:
            interrupted()


def schnitt_anfang() -> None:
    clear()
    path = get_input_file()
    if path is None:
        pause()
        return
    dir_, basename, ext = get_file_info(path)

    print()
    start = ask_time("Zeitpunkt, ab dem behalten werden soll (z.B. 00:01:41): ")

    output = ask_custom_output(dir_ / f"{basename}_anfang_geschnitten{ext}")
    if not check_overwrite(output):
        print("Abgebrochen.")
        pause()
        return

    print()
    print("Schneide Anfang ab...")
    print("(Hinweis: Stream-Copy schneidet am nächsten Keyframe, kleine")
    print(" Abweichungen vom exakten Zeitstempel sind möglich)")
    rc = run_ffmpeg(["-ss", start, "-i", str(path), "-c", "copy", str(output)])
    report_result(rc, "Beim Schneiden ist ein Fehler aufgetreten",
                  f"Fertig! Datei gespeichert als: {output}")
    pause()


def schnitt_mitte() -> None:
    clear()
    path = get_input_file()
    if path is None:
        pause()
        return
    dir_, basename, ext = get_file_info(path)

    print()
    while True:
        start = ask_time("Startzeit des zu löschenden Bereichs (z.B. 00:01:41): ")
        end = ask_time("Endzeit des zu löschenden Bereichs (z.B. 00:02:03): ")

        start_s = parse_time_to_seconds(start)
        end_s = parse_time_to_seconds(end)
        if start_s is not None and end_s is not None and end_s <= start_s:
            print()
            print("[FEHLER] Die Endzeit muss nach der Startzeit liegen!")
            pause()
            continue
        break

    output = ask_custom_output(dir_ / f"{basename}_mitte_geschnitten{ext}")
    if not check_overwrite(output):
        print("Abgebrochen.")
        pause()
        return

    tmp_dir = Path(tempfile.gettempdir())
    uid = uuid.uuid4().hex[:10]
    tmp1 = tmp_dir / f"ffmpegmt_{uid}_part1.mkv"
    tmp2 = tmp_dir / f"ffmpegmt_{uid}_part2.mkv"
    tmplist = tmp_dir / f"ffmpegmt_{uid}_filelist.txt"

    print()
    print(f"[1/4] Erstelle ersten Teil (0 bis {start})...")
    rc = run_ffmpeg(["-i", str(path), "-t", start, "-c", "copy", str(tmp1)])
    if rc != 0:
        print("[FEHLER] Beim Erstellen des ersten Teils ist ein Fehler aufgetreten!")
        tmp1.unlink(missing_ok=True)
        pause()
        return

    print(f"[2/4] Erstelle zweiten Teil (ab {end})...")
    rc = run_ffmpeg(["-ss", end, "-i", str(path), "-c", "copy", str(tmp2)])
    if rc != 0:
        print("[FEHLER] Beim Erstellen des zweiten Teils ist ein Fehler aufgetreten!")
        tmp1.unlink(missing_ok=True)
        tmp2.unlink(missing_ok=True)
        pause()
        return

    print("[3/4] Erstelle Verkettungsliste...")
    with open(tmplist, "w", encoding="utf-8") as f:
        f.write(f"file '{tmp1}'\n")
        f.write(f"file '{tmp2}'\n")

    print("[4/4] Füge Teile zusammen...")
    rc = run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(tmplist), "-c", "copy", str(output)])
    report_result(rc, "Beim Zusammenfügen ist ein Fehler aufgetreten",
                  f"Fertig! Datei gespeichert als: {output}")

    tmp1.unlink(missing_ok=True)
    tmp2.unlink(missing_ok=True)
    tmplist.unlink(missing_ok=True)
    pause()


def schnitt_ende() -> None:
    clear()
    path = get_input_file()
    if path is None:
        pause()
        return
    dir_, basename, ext = get_file_info(path)

    print()
    end = ask_time("Bis zu diesem Zeitpunkt behalten, Rest abschneiden (z.B. 00:02:03): ")

    output = ask_custom_output(dir_ / f"{basename}_ende_geschnitten{ext}")
    if not check_overwrite(output):
        print("Abgebrochen.")
        pause()
        return

    print()
    print("Schneide Ende ab...")
    rc = run_ffmpeg(["-i", str(path), "-t", end, "-c", "copy", str(output)])
    report_result(rc, "Beim Schneiden ist ein Fehler aufgetreten",
                  f"Fertig! Datei gespeichert als: {output}")
    pause()


# ---------------------------------------------------------------------------
# 2) VIDEO ZUSAMMENSETZEN (MERGE / CONCAT)
# ---------------------------------------------------------------------------

def merge_collect_files() -> list[Path] | None:
    """Fragt nacheinander Videodateien ab (mind. 2), leere Eingabe beendet
    die Sammlung. Gibt None zurück, wenn abgebrochen wird."""
    files: list[Path] = []

    first = get_input_file("1. Videodatei")
    if first is None:
        return None
    files.append(first)

    print()
    print("Weitere Videodatei hinzufügen (Reihenfolge = Ausgabereihenfolge).")
    print("Leere Eingabe drücken, wenn alle Dateien hinzugefügt wurden.")
    print()

    while True:
        raw = ask(f"{len(files) + 1}. Videodatei (leer = fertig): ").strip().strip('"')
        if not raw:
            break
        path = Path(raw)
        if not path.is_file():
            print(f'[FEHLER] Datei "{raw}" wurde nicht gefunden!')
            continue
        files.append(path)
        print(f"  -> hinzugefügt: {path.name}")

    if len(files) < 2:
        print()
        print("[FEHLER] Es werden mindestens 2 Videodateien benötigt!")
        return None

    return files


def menu_merge() -> None:
    while True:
        header("Videos zusammensetzen (Merge)")
        print("Fügt mehrere Videodateien in der angegebenen Reihenfolge")
        print("zu einer einzigen Datei zusammen.")
        print()
        print("  [1] Schnell (Stream-Copy, verlustfrei)")
        print("      - erfordert identische Codecs/Auflösung/Format")
        print("  [2] Kompatibel (Re-Encoding)")
        print("      - funktioniert auch bei unterschiedlichen Quelldateien")
        print("  [0] Zurück zum Hauptmenü")
        print()
        try:
            choice = ask("Wähle Methode: ").strip()

            if choice == "1":
                merge_concat_copy()
            elif choice == "2":
                merge_concat_reencode()
            elif choice == "0":
                return
            else:
                print("Ungültige Auswahl!")
                pause()
        except KeyboardInterrupt:
            interrupted()


def merge_concat_copy() -> None:
    clear()
    files = merge_collect_files()
    if files is None:
        pause()
        return

    dir_, basename, ext = get_file_info(files[0])
    output = ask_custom_output(dir_ / f"{basename}_zusammengesetzt{ext}")
    if not check_overwrite(output):
        print("Abgebrochen.")
        pause()
        return

    tmp_dir = Path(tempfile.gettempdir())
    uid = uuid.uuid4().hex[:10]
    tmplist = tmp_dir / f"ffmpegmt_{uid}_filelist.txt"

    with open(tmplist, "w", encoding="utf-8") as f:
        for path in files:
            escaped = str(path.resolve()).replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")

    print()
    print(f"Füge {len(files)} Videos zusammen (Stream-Copy, verlustfrei)...")
    rc = run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(tmplist), "-c", "copy", str(output)])
    print()
    ok = report_result(rc, "Beim Zusammensetzen ist ein Fehler aufgetreten",
                        f"Fertig! Datei gespeichert als: {output}")
    if not ok:
        print("Mögliche Ursachen (siehe FFmpeg-Ausgabe oben für Details):")
        print(" - Die Videos haben unterschiedliche Codecs, Auflösungen")
        print("   oder Formate -> nutze die Methode [2] Kompatibel (Re-Encoding)")
        print(" - Zielordner nicht beschreibbar -> anderen Pfad wählen")

    tmplist.unlink(missing_ok=True)
    pause()


def merge_concat_reencode() -> None:
    clear()
    files = merge_collect_files()
    if files is None:
        pause()
        return

    dir_, basename, _ext = get_file_info(files[0])
    output = ask_custom_output(dir_ / f"{basename}_zusammengesetzt.mp4")
    if not check_overwrite(output):
        print("Abgebrochen.")
        pause()
        return

    args: list[str] = []
    for path in files:
        args += ["-i", str(path)]

    filter_parts = "".join(f"[{i}:v:0][{i}:a:0]" for i in range(len(files)))
    filter_complex = f"{filter_parts}concat=n={len(files)}:v=1:a=1[outv][outa]"

    print()
    print(f"Füge {len(files)} Videos zusammen (Re-Encoding)...")
    print("Dies kann je nach Anzahl und Länge der Videos einige Zeit dauern...")
    print()
    rc = run_ffmpeg([
        *args, "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", str(output),
    ])
    print()
    ok = report_result(rc, "Beim Zusammensetzen ist ein Fehler aufgetreten",
                        f"Fertig! Datei gespeichert als: {output}")
    if not ok:
        print("Mögliche Ursachen (siehe FFmpeg-Ausgabe oben für Details):")
        print(" - Zielordner nicht beschreibbar (z.B. Programm läuft in")
        print("   einem schreibgeschützten Verzeichnis) -> anderen Pfad wählen")
        print(" - Eine der Videodateien enthält keinen Audio-Stream")
        print("   (alle Eingabedateien benötigen Bild UND Ton)")
        print(" - Beschädigte Eingabedatei oder unzureichender Speicherplatz")
    pause()


# ---------------------------------------------------------------------------
# 3) AUDIO / VIDEO TRENNEN
# ---------------------------------------------------------------------------

def menu_trennen() -> None:
    while True:
        header("Audio / Video trennen")
        print("  [1] Nur Audio exportieren (verlustfrei)")
        print("  [2] Nur Video exportieren (verlustfrei, ohne Ton)")
        print("  [3] Beides gleichzeitig exportieren")
        print("  [0] Zurück zum Hauptmenü")
        print()
        try:
            choice = ask("Deine Auswahl: ").strip()

            if choice == "1":
                trennen_audio()
            elif choice == "2":
                trennen_video()
            elif choice == "3":
                trennen_beide()
            elif choice == "0":
                return
            else:
                print("Ungültige Auswahl!")
                pause()
        except KeyboardInterrupt:
            interrupted()


def trennen_audio() -> None:
    clear()
    path = get_input_file()
    if path is None:
        pause()
        return
    dir_, basename, _ext = get_file_info(path)
    a_ext = audio_ext_for_codec(detect_audio_codec(path))

    output = ask_custom_output(dir_ / f"{basename}_audio.{a_ext}")
    if not check_overwrite(output):
        print("Abgebrochen.")
        pause()
        return

    print()
    print("Exportiere nur Audio (verlustfrei)...")
    rc = run_ffmpeg(["-i", str(path), "-vn", "-c", "copy", str(output)])
    report_result(rc, "Beim Audio-Export ist ein Fehler aufgetreten",
                  f"Audio exportiert: {output}")
    pause()


def trennen_video() -> None:
    clear()
    path = get_input_file()
    if path is None:
        pause()
        return
    dir_, basename, _ext = get_file_info(path)

    output = ask_custom_output(dir_ / f"{basename}_video.mp4")
    if not check_overwrite(output):
        print("Abgebrochen.")
        pause()
        return

    print()
    print("Exportiere nur Video (verlustfrei, ohne Ton)...")
    rc = run_ffmpeg(["-i", str(path), "-an", "-c", "copy", str(output)])
    report_result(rc, "Beim Video-Export ist ein Fehler aufgetreten",
                  f"Video exportiert: {output}")
    pause()


def trennen_beide() -> None:
    clear()
    path = get_input_file()
    if path is None:
        pause()
        return
    dir_, basename, _ext = get_file_info(path)
    a_ext = audio_ext_for_codec(detect_audio_codec(path))

    audio_out = resolve_conflict_output(dir_ / f"{basename}_audio.{a_ext}", "Audio")
    video_out = resolve_conflict_output(dir_ / f"{basename}_video.mp4", "Video")

    print()
    if audio_out is not None:
        print("Exportiere Audio...")
        rc = run_ffmpeg(["-i", str(path), "-vn", "-c", "copy", str(audio_out)])
        report_result(rc, "Beim Audio-Export ist ein Fehler aufgetreten",
                      f"Audio exportiert: {audio_out}")
    else:
        print("Audio-Export übersprungen.")

    if video_out is not None:
        print("Exportiere Video...")
        rc = run_ffmpeg(["-i", str(path), "-an", "-c", "copy", str(video_out)])
        report_result(rc, "Beim Video-Export ist ein Fehler aufgetreten",
                      f"Video exportiert: {video_out}")
    else:
        print("Video-Export übersprungen.")
    pause()


# ---------------------------------------------------------------------------
# 4) MUXEN (AUDIO + VIDEO ZUSAMMENFUEGEN)
# ---------------------------------------------------------------------------

def menu_mux() -> None:
    while True:
        header("Audio + Video zusammenfügen (Muxen)")
        print("  [1] Audio unverändert übernehmen (verlustfrei)")
        print("  [2] Audio dabei konvertieren (z.B. bei WAV: MP3/AAC/Opus)")
        print("  [0] Zurück zum Hauptmenü")
        print()
        try:
            choice = ask("Deine Auswahl: ").strip()

            if choice == "1":
                mux_copy()
            elif choice == "2":
                mux_convert()
            elif choice == "0":
                return
            else:
                print("Ungültige Auswahl!")
                pause()
        except KeyboardInterrupt:
            interrupted()


def mux_copy() -> None:
    header("Muxen - Audio unverändert übernehmen")
    video = get_input_file("Videodatei")
    if video is None:
        pause()
        return
    print()
    audio = get_input_file("Audiodatei")
    if audio is None:
        pause()
        return

    dir_, basename, _ext = get_file_info(video)
    output = ask_custom_output(dir_ / f"{basename}_muxed.mp4")
    if not check_overwrite(output):
        print("Abgebrochen.")
        pause()
        return

    print()
    print("Füge Video und Audio zusammen...")
    rc = run_ffmpeg([
        "-i", str(video), "-i", str(audio), "-c", "copy",
        "-map", "0:v:0", "-map", "1:a:0", str(output),
    ])
    ok = report_result(rc, "Beim Muxen ist ein Fehler aufgetreten",
                        f"Muxen abgeschlossen: {output}")
    if not ok:
        print("Mögliche Ursache: Der Audio-Codec ist im Ziel-Container nicht erlaubt")
        print("(z.B. WAV direkt in MP4). Nutze in diesem Fall Option [2] im Muxen-Menü.")
    pause()


def select_mux_audio_format() -> tuple[list[str], str] | None:
    """Punkt 3: Zielformat-Auswahl fürs Muxen, generisch über
    AUDIO_FORMATS statt der alten, MP3-fixen select_mp3_bitrate(). Vorbis/
    OGG wird hier bewusst ausgelassen, da es im MP4-Container (Zielformat
    beim Muxen) nicht zuverlässig unterstützt wird. Gibt None zurück bei
    'Zurück'."""
    mux_formats = [fmt for fmt in AUDIO_FORMATS if fmt["ext"] in ("mp3", "m4a", "opus")]
    while True:
        header("Audioformat fürs Muxen wählen")
        for fmt in mux_formats:
            print(f"  [{fmt['key']}] {fmt['label']}")
        print("  [0] Zurück")
        print()
        choice = ask("Deine Auswahl: ").strip()

        for fmt in mux_formats:
            if choice == fmt["key"]:
                picked = select_bitrate(fmt["presets"], fmt["menu_title"], codec_args=fmt["codec_args"])
                if picked is None:
                    break
                return picked
        else:
            if choice == "0":
                return None
            print("Ungültige Auswahl!")
            pause()


def mux_convert() -> None:
    header("Muxen mit Audio-Konvertierung")
    print("Kombiniert eine Videodatei (ohne Ton) mit einer Audiodatei und")
    print("konvertiert das Audio dabei in ein kompatibles Format (z.B. WAV -> MP3).")
    print("=" * 51)
    print()
    video = get_input_file("Videodatei (ohne Audio)")
    if video is None:
        pause()
        return
    print()
    audio = get_input_file("Audiodatei (z.B. WAV)")
    if audio is None:
        pause()
        return

    picked = select_mux_audio_format()
    if picked is None:
        return
    audio_params, audio_info = picked

    if not warn_if_encoder_missing(audio_params):
        print("Abgebrochen.")
        pause()
        return

    dir_, basename, _ext = get_file_info(video)
    output = ask_custom_output(dir_ / f"{basename}_merged.mp4")
    if not check_overwrite(output):
        print("Abgebrochen.")
        pause()
        return

    header("Starte Muxing-Prozess")
    print(f"Video:    {video}")
    print(f"Audio:    {audio}")
    print(f"Format:   {audio_info}")
    print(f"Ausgabe:  {output}")
    print()
    print("Verarbeitung läuft (Video wird kopiert, Audio konvertiert)...")
    print()

    rc = run_ffmpeg([
        "-i", str(video), "-i", str(audio), "-c:v", "copy",
        *audio_params, "-map", "0:v:0", "-map", "1:a:0", str(output),
    ])
    print()
    ok = report_result(rc, "Beim Muxen ist ein Fehler aufgetreten", "Erfolgreich abgeschlossen!")
    if not ok:
        print("Mögliche Ursachen:")
        print(" - Video- und Audiolänge unterscheiden sich stark")
        print(" - Beschädigte Eingabedateien")
        print(" - Unzureichender Speicherplatz")
    else:
        print(f"Ausgabedatei: {output}")
        print(f"Audio-Format: {audio_info}")
        print("Video-Format: unverändert (verlustfrei kopiert)")
    print()
    pause()


# ---------------------------------------------------------------------------
# 5) VIDEO ROTIEREN
# ---------------------------------------------------------------------------

def menu_rotate() -> None:
    clear()
    path = get_input_file()
    if path is None:
        pause()
        return
    dir_, basename, ext = get_file_info(path)

    while True:
        header("Video Rotation - Winkel wählen")
        print(f"Datei: {basename}{ext}")
        print()
        print("  [1] 90 Grad im Uhrzeigersinn")
        print("  [2] 180 Grad drehen")
        print("  [3] 270 Grad im Uhrzeigersinn (90 Grad gegen den UZS)")
        print("  [0] Zurück zum Hauptmenü")
        print()
        try:
            choice = ask("Wähle Rotation: ").strip()

            if choice == "1":
                rotation, suffix = "90", "_rot90"
            elif choice == "2":
                rotation, suffix = "180", "_rot180"
            elif choice == "3":
                rotation, suffix = "270", "_rot270"
            elif choice == "0":
                return
            else:
                print("Ungültige Auswahl!")
                pause()
                continue

            if rotate_method_menu(path, dir_, basename, ext, rotation, suffix):
                return  # zurück zum Hauptmenü nach Erfolg/Ende
        except KeyboardInterrupt:
            interrupted()


def rotate_method_menu(path: Path, dir_: Path, basename: str, ext: str,
                        rotation: str, suffix: str) -> bool:
    while True:
        header("Rotations-Methode wählen")
        print("  [1] Metadaten-Rotation (instant, 100% verlustfrei)")
        print("      - keine Re-Encodierung, funktioniert in den meisten Playern")
        print("  [2] Pixel-Rotation (Re-Encoding, CRF 0 = verlustfrei)")
        print("      - dauert länger, funktioniert in allen Playern/Editoren")
        print("  [0] Zurück")
        print()
        try:
            method = ask("Wähle Methode: ").strip()

            if method == "1":
                return rotate_metadata(path, dir_, basename, suffix, rotation)
            if method == "2":
                return rotate_reencode(path, dir_, basename, suffix, rotation)
            if method == "0":
                return False
            print("Ungültige Auswahl!")
            pause()
        except KeyboardInterrupt:
            interrupted()


def rotate_metadata(path: Path, dir_: Path, basename: str, suffix: str, rotation: str) -> bool:
    output = ask_custom_output(dir_ / f"{basename}{suffix}_metadata.mp4")
    if not check_overwrite(output):
        print("Abgebrochen.")
        pause()
        return False

    print()
    print("Rotiere Video (Metadaten, verlustfrei)...")
    rc = run_ffmpeg([
        "-i", str(path), "-c", "copy",
        "-metadata:s:v:0", f"rotate={rotation}", str(output),
    ])
    ok = report_result(rc, "Beim Rotieren ist ein Fehler aufgetreten",
                        f"Video rotiert! Ausgabe: {output}")
    if ok:
        print("HINWEIS: Aendert nur Metadaten. Falls im Player nicht sichtbar,")
        print("nutze stattdessen die Pixel-Rotation.")
    pause()
    return True


def rotate_reencode(path: Path, dir_: Path, basename: str, suffix: str, rotation: str) -> bool:
    output = ask_custom_output(dir_ / f"{basename}{suffix}.mp4")
    if not check_overwrite(output):
        print("Abgebrochen.")
        pause()
        return False

    filters = {"90": "transpose=1", "180": "transpose=1,transpose=1", "270": "transpose=2"}
    vf = filters[rotation]

    print()
    print("Rotiere Video (Re-Encoding, CRF 0 = verlustfrei)...")
    print("Dies kann je nach Videolänge einige Zeit dauern...")
    print()
    rc = run_ffmpeg([
        "-i", str(path), "-vf", vf, "-c:v", "libx264", "-preset", "veryslow",
        "-crf", "0", "-c:a", "copy", str(output),
    ])
    ok = report_result(rc, "Beim Rotieren ist ein Fehler aufgetreten",
                        f"Video rotiert! Ausgabe: {output}")
    if ok:
        print("Einstellungen: CRF 0, Preset veryslow, Audio verlustfrei kopiert.")
    pause()
    return True


# ---------------------------------------------------------------------------
# 6) AUDIO KONVERTIEREN
# ---------------------------------------------------------------------------

def menu_convert() -> None:
    header("Audio konvertieren")
    path = get_input_file()
    if path is None:
        pause()
        return
    dir_, basename, _ext = get_file_info(path)

    result = select_audio_format()
    if result is None:
        return  # Nutzer hat [0] gewählt -> zurück zum Hauptmenü
    target_ext, codec_params, format_info = result

    if not warn_if_encoder_missing(codec_params):
        print("Abgebrochen.")
        pause()
        return

    output = ask_custom_output(dir_ / f"{basename}_converted.{target_ext}")
    output = confirm_extension(output, target_ext)
    if not check_overwrite(output):
        print("Abgebrochen.")
        pause()
        return

    print()
    print(f"Konvertierung läuft ({format_info})...")
    rc = convert_with_cover_preservation(path, codec_params, output, target_ext)
    print()
    report_result(rc, "Bei der Konvertierung ist ein Fehler aufgetreten",
                  f"Fertig! Datei gespeichert als: {output}")
    pause()


# ---------------------------------------------------------------------------
# HAUPTMENUE
# ---------------------------------------------------------------------------

def main_menu() -> None:
    while True:
        header("FFmpeg Multi-Tool")
        print("  [1] Video schneiden        (Anfang / Mitte / Ende)")
        print("  [2] Video zusammensetzen   (mehrere Videos mergen)")
        print("  [3] Audio / Video trennen  (exportieren, verlustfrei)")
        print("  [4] Audio + Video muxen    (zusammenfügen)")
        print("  [5] Video rotieren")
        print("  [6] Audio konvertieren     (MP3, AAC, Opus, Vorbis, FLAC, WAV)")
        print("  [0] Beenden")
        print()
        if _dropped_file:
            print(f"  Aktive Datei (Drag & Drop): {_dropped_file}")
            print()
        try:
            choice = ask("Deine Auswahl: ").strip()

            if choice == "1":
                menu_schnitt()
            elif choice == "2":
                menu_merge()
            elif choice == "3":
                menu_trennen()
            elif choice == "4":
                menu_mux()
            elif choice == "5":
                menu_rotate()
            elif choice == "6":
                menu_convert()
            elif choice == "0":
                sys.exit(0)
            else:
                print("Ungültige Auswahl!")
                pause()
        except KeyboardInterrupt:
            interrupted()


def main() -> None:
    global _dropped_file
    if os.name == "nt":
        os.system("title FFmpeg Multi-Tool (Python)")
    else:
        sys.stdout.write("\033]0;FFmpeg Multi-Tool (Python)\007")

    check_ffmpeg()
    cleanup_temp_files()

    if len(sys.argv) > 1:
        _dropped_file = sys.argv[1]

    main_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgramm mit Strg+C beendet.")
        sys.exit(0)
