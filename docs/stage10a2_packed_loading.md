# Stage10a2 – gepackte Dateien und schnelleres Laden (Testbuild)

Basis: Stage10a1-HW2 (Branch `stage10a1-hw`, vom Benutzer am 17.10.2026 auf
MEGA65-Hardware mit Core 0.97 `aaf4542`, ROM 920413, PAL bestätigt).
Gameplay, Grafik, Sound und alle Speicheradressen der Daten bleiben unverändert.

## Ausgangslage

Von `RUN` bis zum Startbildschirm dauerte es auf echter Hardware 22 Sekunden.
Die Lader lesen jede Datei byteweise über KERNAL `CHRIN`/`READST`; vor dem
Startbildschirm werden 454.669 Byte gelesen (VYTI, VYSO, VYHS, VYMN, VYLV, VYGR,
VYCL, VYSH). Das sind etwa 21 KB/s, die Ladezeit hängt fast nur an der Bytezahl.

## Änderung

Alle über `s3b.load_file` oder den Audio-Lader gelesenen Dateien liegen ZX0-gepackt
auf der Diskette (Dateinamen unverändert). VYHI bleibt ungepackt, weil das
Highscore-Overlay sie mit eigenem Diskcode liest und schreibt. Die PRG-Datei wird
wie bisher mit `LOAD` geladen und ist nicht gepackt.

| Datei | Original | auf Diskette |
|---|---:|---:|
| VYSO.DAT | 160.960 | 109.804 |
| VYMN.DAT | 86.720 | 14.464 |
| VYLV.DAT | 81.793 | 23.436 |
| VYTI.DAT | 60.365 | 12.701 |
| VYGR.DAT | 33.464 | 6.809 |
| VYHS.DAT | 29.183 | 4.478 |
| VYSH.DAT | 1.116 | 228 |
| VYCL.DAT | 476 | 337 |
| **gelesen vor Startbildschirm** | **454.077** | **172.257** |

Erwartung: Das Lesen der gepackten Bytes dauert bei unverändertem KERNAL-Durchsatz
rund 8 s. Der Entpacker braucht im Modell durchschnittlich etwa 100 Befehle pro
entpacktem Byte; bei 40 MHz kommen dafür grob 2–3 s hinzu. Insgesamt also etwa
10–12 s statt 22 s (Schätzung, auf der Hardware noch zu messen).

### Format

`"Z0"`, Gesamtlänge (24 Bit), Länge des nicht deltakodierten Anfangs (24 Bit),
danach ein ZX0-v2-Datenstrom (Kompressor von Einar Saukas,
https://github.com/einar-saukas/ZX0). In VYSO wird der PCM-Teil ab Offset 6.656
vor dem Packen deltakodiert (`out[i] = out[i-1] + d[i]`), das spart weitere 8 KB.
`tools/pack_stage10a2.py` packt und prüft jede Datei mit einem Python-Modell des
Entpackers, bevor sie auf die Diskette kommt.

### Entpacker (`src/engine/stage10a2_unpack.asm`)

- Streaming-Entpacker, liefert pro Aufruf genau ein entpacktes Byte.
- In beiden Ladeschleifen werden nur die KERNAL-Aufrufe ersetzt, jeweils mit
  identischer Bytezahl, damit keine Adresse verrutscht:
  `SETNAM` → `unpack.setnam`/`setnam_rom` (setzt den Entpacker zurück),
  `CHRIN` → `unpack.chrin`, `READST` → `unpack.readst`.
- `READST` meldet `$40` genau nach dem letzten entpackten Byte; echte
  Lesefehler werden weitergereicht, ein zu kurzer oder defekter Datenstrom wird
  als `$02` gemeldet. Alle bestehenden Längen-, Summen-, CRC- und
  Rücklesevergleiche laufen unverändert über die entpackten Daten.
- Lage: freies Ende des Titel-Bootstrap `$45CD–$47F7`, Ring-Zeiger `$47F8–$47FF`
  (Basepage `$47`). Der Bereich wird erst nach dem letzten Ladevorgang von
  `titlecache.tc_save` gesichert und bei jedem BASIC-Exit wiederhergestellt, ein
  erneutes `RUN` findet also wieder einen gültigen Entpacker.
- 64-KB-Ringpuffer im freien Attic `$080B0000–$080BFFFF` (Attic war bis
  `$080A063F` belegt). ZX0-Offsets sind höchstens 32.640 Byte.
- X und Y bleiben erhalten; IRQs werden nur während des Basepage-Wechsels gesperrt.

## Prüfungen

- Der KickAssembler 65CE02/45GS02 5.25 des Benutzers reproduziert Stage10a1 und
  Stage10a1-HW2 byte-genau.
- `STAGE10A2.PRG` unterscheidet sich von Stage10a1-HW2 nur im Entpackerbereich
  `$45CD–$47FF`, an den drei JSR-Operanden in `load_file` und an den drei
  10-Byte-Aufrufstellen im Audio-Lader. Menü-, Audio- und Highscore-Module sind
  byte-identisch.
- `tools/test_stage10a2_unpack.py` führt den assemblierten Entpacker-Code in einem
  45GS02-Modell aus (KERNAL nachgebildet, beide Aufrufarten) und vergleicht jede
  entpackte Datei byteweise mit dem Original, einschließlich `READST`-Verhalten,
  Register-, IRQ- und Basepage-Erhalt.

## Build

```
python3 tools/build_stage10a2.py --kickass KickAss65CE02-5.25.jar --zx0 /pfad/zu/zx0
```

ZX0 v2 aus https://github.com/einar-saukas/ZX0 (`gcc -O2 -o zx0 src/compress.c src/memory.c src/optimize.c src/zx0.c`).

## Hardwaretest

Start: `LOAD "STAGE10A2",8`, `RUN`. Zu prüfen: Ladezeit bis zum Startbildschirm,
Titel, Menü, Sound, Levelstart, Highscore und ein zweites `RUN` nach `X`.
Noch nicht vom Benutzer bestätigt.
