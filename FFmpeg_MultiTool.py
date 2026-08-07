#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FFmpeg Multi-Tool (Python-Version)
Vereint: Video-Schnitt, Audio/Video-Trennung, Muxen, Rotation, MP3-Konvertierung

Funktioniert unter Windows, Linux und macOS. FFmpeg wird an zwei Stellen
gesucht (in dieser Reihenfolge):
  1. Lokaler Unterordner "FFmpeg" neben diesem Skript (portable Variante,
     unter Windows ffmpeg.exe/ffprobe.exe, sonst ffmpeg/ffprobe ohne
     Endung) - genau wie bei der .bat-Version.
  2. Systemweit installiertes FFmpeg im PATH (z.B. nach
     "sudo apt install ffmpeg" unter Linux oder "brew install ffmpeg"
     unter macOS).

Vorteil gegenueber der Batch-Version: Dateinamen mit Klammern, "&", "%%",
Umlauten etc. funktionieren hier ganz normal, weil Python Pfade als echte
Strings behandelt und FFmpeg-Argumente als Liste uebergibt (kein
Shell-Parsing, kein Quoting-Aerger).
"""

from __future__ import annotations

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
    System-PATH. Gibt den lokalen Pfad zurueck, falls gar nichts gefunden
    wird (fuer eine aussagekraeftige Fehlermeldung in check_ffmpeg)."""
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

TIME_RE = re.compile(r"^[0-9:.]+$")

# Wird beim Start ggf. mit einer per Drag & Drop uebergebenen Datei belegt
_dropped_file: str | None = None


# ---------------------------------------------------------------------------
# Kleine Hilfsfunktionen fuer die Konsole
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
    # sondern nach oben durchgereicht: die jeweilige Menue-Schleife faengt
    # sie ab und kehrt zum Menue zurueck, statt das ganze Programm zu
    # beenden (siehe run_menu_loop / main_menu / menu_*).


def interrupted() -> None:
    """Einheitliche Meldung, wenn eine Aktion per Strg+C abgebrochen wurde."""
    print("\n\n[ABBRUCH] Vorgang mit Strg+C abgebrochen - zurueck zum Menue.")


# ---------------------------------------------------------------------------
# FFmpeg-Grundcheck
# ---------------------------------------------------------------------------

def check_ffmpeg() -> None:
    ffmpeg_name = f"ffmpeg{_EXE_SUFFIX}"
    if not FFMPEG.is_file():
        print(f'[FEHLER] "{ffmpeg_name}" wurde nicht gefunden!')
        print(f'Gesucht wurde im Ordner "{FFMPEG_DIR}" sowie im System-PATH.')
        print()
        print("Loesungsmoeglichkeiten:")
        print(f'  - Unterordner "FFmpeg" neben diesem Skript anlegen und')
        print(f"    {ffmpeg_name} (und optional ffprobe{_EXE_SUFFIX}) dort hineinlegen,")
        print("    oder")
        if os.name == "nt":
            print("  - FFmpeg systemweit installieren und zum PATH hinzufuegen")
        else:
            print("  - FFmpeg ueber den Paketmanager installieren, z.B.:")
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
    uebergebene Datei, danach manuelle Eingabe. Gibt None zurueck, wenn
    die Datei nicht existiert."""
    global _dropped_file
    if _dropped_file:
        raw = _dropped_file
        print(f"Verwende per Drag & Drop uebergebene Datei als {label}: {raw}")
        _dropped_file = None
    else:
        print(f"Tipp: {label} per Drag & Drop in dieses Fenster ziehen und Enter druecken,")
        raw = ask(f"oder Dateiname/Pfad eingeben ({label}): ")

    raw = raw.strip().strip('"')
    path = Path(raw)
    if not path.is_file():
        print()
        print(f'[FEHLER] Datei "{raw}" wurde nicht gefunden!')
        return None
    return path


def get_file_info(path: Path) -> tuple[Path, str, str]:
    """Gibt (Verzeichnis, Basisname, Endung-mit-Punkt) zurueck."""
    return path.parent, path.stem, path.suffix


def ask_custom_output(default_output: Path) -> Path | None:
    """Schlaegt einen Standard-Ausgabepfad vor und erlaubt einen eigenen
    Namen. Prueft, dass das Zielverzeichnis existiert.

    Wird nur ein blanker Dateiname ohne Pfad eingegeben (z.B. "neu.mp4"),
    wird dieser im selben Ordner wie der Standard-Vorschlag gespeichert -
    NICHT im aktuellen Arbeitsverzeichnis des Programms. Das verhindert
    "Permission denied"-Fehler, wenn das Programm z.B. aus einem
    schreibgeschuetzten Ordner (Programme, System32 o.ae.) gestartet wurde.
    """
    output = default_output
    while True:
        print()
        print(f"Ausgabedatei: {output}")
        custom = ask("Anderen Dateinamen verwenden? (Enter fuer Standard): ").strip().strip('"')
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


def check_overwrite(path: Path) -> bool:
    """Prueft ob eine Datei bereits existiert und fragt ggf. nach.
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


def ask_time(prompt: str) -> str:
    """Fragt eine Zeitangabe ab und wiederholt, bis das Format plausibel
    ist (nur Ziffern, ':' und '.', nicht leer)."""
    while True:
        value = ask(prompt).strip()
        if value and TIME_RE.match(value):
            return value
        print("[FEHLER] Ungueltiges Zeitformat! Erlaubt sind nur Ziffern, ':' und '.'")
        print("(z.B. 00:01:41 oder 95.5).")


# ---------------------------------------------------------------------------
# FFmpeg-Aufrufe
# ---------------------------------------------------------------------------

def run_ffmpeg(args: list[str]) -> int:
    """Ruft ffmpeg mit einer Argumentliste auf (kein Shell-Parsing noetig,
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
    vorhanden, sonst ffmpeg-Fallback ueber die stderr-Ausgabe."""
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
        print("[INFO] ffprobe.exe nicht gefunden, verwende ffmpeg fuer Codec-Erkennung")
        cmd = [str(FFMPEG), "-i", str(path)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        for line in proc.stderr.splitlines():
            if "Audio:" in line:
                after = line.split("Audio:", 1)[1].strip()
                codec = after.split(",")[0].strip()
                break

    if not codec:
        print("[WARNUNG] Kein Audio-Stream gefunden oder Codec konnte nicht erkannt werden!")
        return None
    print(f"Erkanntes Audioformat: {codec}")
    return codec


def audio_ext_for_codec(codec: str | None) -> str:
    if not codec:
        return "mka"
    return AUDIO_EXT_MAP.get(codec.lower(), "mka")


def select_mp3_bitrate() -> tuple[list[str], str] | None:
    """Zeigt das MP3-Bitraten-Menue an. Gibt (ffmpeg_params, info_text)
    zurueck."""
    while True:
        header("MP3-Bitrate auswaehlen")
        print("  [1] 128 kbps  (kleine Dateigroesse, ok fuer Sprache)")
        print("  [2] 160 kbps  (Standard)")
        print("  [3] 192 kbps  (guter Kompromiss)")
        print("  [4] 256 kbps  (hohe Qualitaet)")
        print("  [5] 320 kbps  (maximale MP3-Qualitaet)")
        print("  [6] VBR V0    (~245 kbps, variabel, beste Qualitaet)")
        print("  [7] VBR V2    (~190 kbps, variabel, sehr gut)")
        print("  [8] VBR V4    (~165 kbps, variabel, gut fuer Sprache)")
        print("  [9] Eigene Bitrate eingeben")
        print()
        choice = ask("Deine Auswahl: ").strip()

        if choice in MP3_BITRATES:
            return MP3_BITRATES[choice]

        if choice == "9":
            print()
            print("Empfohlene Werte: 96, 128, 160, 192, 224, 256, 320")
            custom = ask("Bitrate in kbps eingeben: ").strip()
            if custom.isdigit():
                return (["-c:a", "libmp3lame", "-b:a", f"{custom}k"],
                         f"{custom} kbps CBR (benutzerdefiniert)")
            print()
            print("[FEHLER] Ungueltige Eingabe! Bitte nur eine Zahl eingeben.")
            pause()
            continue

        print("Ungueltige Auswahl!")
        pause()


# ---------------------------------------------------------------------------
# 1) VIDEO SCHNEIDEN
# ---------------------------------------------------------------------------

def menu_schnitt() -> None:
    while True:
        header("Video schneiden")
        print("  [1] Anfang abschneiden")
        print("  [2] Mittleren Teil herausschneiden")
        print("  [3] Ende abschneiden (nur Anfangsteil behalten)")
        print("  [0] Zurueck zum Hauptmenue")
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
                print("Ungueltige Auswahl!")
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
    print("(Hinweis: Stream-Copy schneidet am naechsten Keyframe, kleine")
    print(" Abweichungen vom exakten Zeitstempel sind moeglich)")
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
    start = ask_time("Startzeit des zu loeschenden Bereichs (z.B. 00:01:41): ")
    end = ask_time("Endzeit des zu loeschenden Bereichs (z.B. 00:02:03): ")

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

    print("[4/4] Fuege Teile zusammen...")
    rc = run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(tmplist), "-c", "copy", str(output)])
    report_result(rc, "Beim Zusammenfuegen ist ein Fehler aufgetreten",
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
    die Sammlung. Gibt None zurueck, wenn abgebrochen wird."""
    files: list[Path] = []

    first = get_input_file("1. Videodatei")
    if first is None:
        return None
    files.append(first)

    print()
    print("Weitere Videodatei hinzufuegen (Reihenfolge = Ausgabereihenfolge).")
    print("Leere Eingabe druecken, wenn alle Dateien hinzugefuegt wurden.")
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
        print(f"  -> hinzugefuegt: {path.name}")

    if len(files) < 2:
        print()
        print("[FEHLER] Es werden mindestens 2 Videodateien benoetigt!")
        return None

    return files


def menu_merge() -> None:
    while True:
        header("Videos zusammensetzen (Merge)")
        print("Fuegt mehrere Videodateien in der angegebenen Reihenfolge")
        print("zu einer einzigen Datei zusammen.")
        print()
        print("  [1] Schnell (Stream-Copy, verlustfrei)")
        print("      - erfordert identische Codecs/Aufloesung/Format")
        print("  [2] Kompatibel (Re-Encoding)")
        print("      - funktioniert auch bei unterschiedlichen Quelldateien")
        print("  [0] Zurueck zum Hauptmenue")
        print()
        try:
            choice = ask("Waehle Methode: ").strip()

            if choice == "1":
                merge_concat_copy()
            elif choice == "2":
                merge_concat_reencode()
            elif choice == "0":
                return
            else:
                print("Ungueltige Auswahl!")
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
    print(f"Fuege {len(files)} Videos zusammen (Stream-Copy, verlustfrei)...")
    rc = run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(tmplist), "-c", "copy", str(output)])
    print()
    ok = report_result(rc, "Beim Zusammensetzen ist ein Fehler aufgetreten",
                        f"Fertig! Datei gespeichert als: {output}")
    if not ok:
        print("Moegliche Ursachen (siehe FFmpeg-Ausgabe oben fuer Details):")
        print(" - Die Videos haben unterschiedliche Codecs, Aufloesungen")
        print("   oder Formate -> nutze die Methode [2] Kompatibel (Re-Encoding)")
        print(" - Zielordner nicht beschreibbar -> anderen Pfad waehlen")

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
    print(f"Fuege {len(files)} Videos zusammen (Re-Encoding)...")
    print("Dies kann je nach Anzahl und Laenge der Videos einige Zeit dauern...")
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
        print("Moegliche Ursachen (siehe FFmpeg-Ausgabe oben fuer Details):")
        print(" - Zielordner nicht beschreibbar (z.B. Programm laeuft in")
        print("   einem schreibgeschuetzten Verzeichnis) -> anderen Pfad waehlen")
        print(" - Eine der Videodateien enthaelt keinen Audio-Stream")
        print("   (alle Eingabedateien benoetigen Bild UND Ton)")
        print(" - Beschaedigte Eingabedatei oder unzureichender Speicherplatz")
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
        print("  [0] Zurueck zum Hauptmenue")
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
                print("Ungueltige Auswahl!")
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

    audio_out = dir_ / f"{basename}_audio.{a_ext}"
    video_out = dir_ / f"{basename}_video.mp4"

    audio_ok = check_overwrite(audio_out)
    video_ok = check_overwrite(video_out)

    print()
    if audio_ok:
        print("Exportiere Audio...")
        rc = run_ffmpeg(["-i", str(path), "-vn", "-c", "copy", str(audio_out)])
        report_result(rc, "Beim Audio-Export ist ein Fehler aufgetreten",
                      f"Audio exportiert: {audio_out}")
    else:
        print("Audio-Export uebersprungen.")

    if video_ok:
        print("Exportiere Video...")
        rc = run_ffmpeg(["-i", str(path), "-an", "-c", "copy", str(video_out)])
        report_result(rc, "Beim Video-Export ist ein Fehler aufgetreten",
                      f"Video exportiert: {video_out}")
    else:
        print("Video-Export uebersprungen.")
    pause()


# ---------------------------------------------------------------------------
# 4) MUXEN (AUDIO + VIDEO ZUSAMMENFUEGEN)
# ---------------------------------------------------------------------------

def menu_mux() -> None:
    while True:
        header("Audio + Video zusammenfuegen (Muxen)")
        print("  [1] Audio unveraendert uebernehmen (verlustfrei)")
        print("  [2] Audio dabei zu MP3 konvertieren (z.B. bei WAV)")
        print("  [0] Zurueck zum Hauptmenue")
        print()
        try:
            choice = ask("Deine Auswahl: ").strip()

            if choice == "1":
                mux_copy()
            elif choice == "2":
                mux_mp3()
            elif choice == "0":
                return
            else:
                print("Ungueltige Auswahl!")
                pause()
        except KeyboardInterrupt:
            interrupted()


def mux_copy() -> None:
    header("Muxen - Audio unveraendert uebernehmen")
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
    print("Fuege Video und Audio zusammen...")
    rc = run_ffmpeg([
        "-i", str(video), "-i", str(audio), "-c", "copy",
        "-map", "0:v:0", "-map", "1:a:0", str(output),
    ])
    ok = report_result(rc, "Beim Muxen ist ein Fehler aufgetreten",
                        f"Muxen abgeschlossen: {output}")
    if not ok:
        print("Moegliche Ursache: Der Audio-Codec ist im Ziel-Container nicht erlaubt")
        print("(z.B. WAV direkt in MP4). Nutze in diesem Fall Option [2] im Muxen-Menue.")
    pause()


def mux_mp3() -> None:
    header("Muxen mit MP3-Konvertierung")
    print("Kombiniert eine Videodatei (ohne Ton) mit einer")
    print("Audiodatei und konvertiert das Audio dabei zu MP3.")
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

    dir_, basename, _ext = get_file_info(video)
    bitrate = select_mp3_bitrate()
    if bitrate is None:
        return
    mp3_params, mp3_info = bitrate

    output = ask_custom_output(dir_ / f"{basename}_merged.mp4")
    if not check_overwrite(output):
        print("Abgebrochen.")
        pause()
        return

    header("Starte Muxing-Prozess")
    print(f"Video:    {video}")
    print(f"Audio:    {audio}")
    print(f"Bitrate:  {mp3_info}")
    print(f"Ausgabe:  {output}")
    print()
    print("Verarbeitung laeuft (Video wird kopiert, Audio zu MP3 konvertiert)...")
    print()

    rc = run_ffmpeg([
        "-i", str(video), "-i", str(audio), "-c:v", "copy",
        *mp3_params, "-map", "0:v:0", "-map", "1:a:0", str(output),
    ])
    print()
    ok = report_result(rc, "Beim Muxen ist ein Fehler aufgetreten", "Erfolgreich abgeschlossen!")
    if not ok:
        print("Moegliche Ursachen:")
        print(" - Video- und Audiolaenge unterscheiden sich stark")
        print(" - Beschaedigte Eingabedateien")
        print(" - Unzureichender Speicherplatz")
    else:
        print(f"Ausgabedatei: {output}")
        print(f"Audio-Format: MP3 ({mp3_info})")
        print("Video-Format: unveraendert (verlustfrei kopiert)")
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
        header("Video Rotation - Winkel waehlen")
        print(f"Datei: {basename}{ext}")
        print()
        print("  [1] 90 Grad im Uhrzeigersinn")
        print("  [2] 180 Grad drehen")
        print("  [3] 270 Grad im Uhrzeigersinn (90 Grad gegen den UZS)")
        print("  [0] Zurueck zum Hauptmenue")
        print()
        try:
            choice = ask("Waehle Rotation: ").strip()

            if choice == "1":
                rotation, suffix = "90", "_rot90"
            elif choice == "2":
                rotation, suffix = "180", "_rot180"
            elif choice == "3":
                rotation, suffix = "270", "_rot270"
            elif choice == "0":
                return
            else:
                print("Ungueltige Auswahl!")
                pause()
                continue

            if rotate_method_menu(path, dir_, basename, ext, rotation, suffix):
                return  # zurueck zum Hauptmenue nach Erfolg/Ende
        except KeyboardInterrupt:
            interrupted()


def rotate_method_menu(path: Path, dir_: Path, basename: str, ext: str,
                        rotation: str, suffix: str) -> bool:
    while True:
        header("Rotations-Methode waehlen")
        print("  [1] Metadaten-Rotation (instant, 100% verlustfrei)")
        print("      - keine Re-Encodierung, funktioniert in den meisten Playern")
        print("  [2] Pixel-Rotation (Re-Encoding, CRF 0 = verlustfrei)")
        print("      - dauert laenger, funktioniert in allen Playern/Editoren")
        print("  [0] Zurueck")
        print()
        try:
            method = ask("Waehle Methode: ").strip()

            if method == "1":
                return rotate_metadata(path, dir_, basename, suffix, rotation)
            if method == "2":
                return rotate_reencode(path, dir_, basename, suffix, rotation)
            if method == "0":
                return False
            print("Ungueltige Auswahl!")
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
    print("Dies kann je nach Videolaenge einige Zeit dauern...")
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
# 6) AUDIO IN MP3 KONVERTIEREN
# ---------------------------------------------------------------------------

def menu_convert() -> None:
    header("Audio in MP3 konvertieren")
    path = get_input_file()
    if path is None:
        pause()
        return
    dir_, basename, _ext = get_file_info(path)

    bitrate = select_mp3_bitrate()
    if bitrate is None:
        return
    mp3_params, mp3_info = bitrate

    output = ask_custom_output(dir_ / f"{basename}_converted.mp3")
    if not check_overwrite(output):
        print("Abgebrochen.")
        pause()
        return

    print()
    print(f"Konvertierung laeuft ({mp3_info})...")
    rc = run_ffmpeg(["-i", str(path), *mp3_params, "-vn", str(output)])
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
        print("  [4] Audio + Video muxen    (zusammenfuegen)")
        print("  [5] Video rotieren")
        print("  [6] Audio in MP3 konvertieren")
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
                print("Ungueltige Auswahl!")
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
