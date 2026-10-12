# Historische Referenz – durch Stage 6a2 Stable abgelöst

Stage6a1 ist laut Benutzer obsolet. Aktuelle eigenständige Menüreferenz: [Stage6a2 Stable](stage6a2_color_cycling.md), Tag `stage6a2-stable`. Dateien und ursprünglicher Bericht bleiben zur Nachvollziehbarkeit erhalten.

# Stage 6a1 – original animated start screen (Issue #43)

Eigenständiger Testbranch `stage6a1`, **nicht Stable**. Stage 5d-1a Stable (`stage5d1a-stable`, Commit `39890c0`) bleibt unverändert. Keine Einbindung in Loader oder Spielengine. Keine Menüfunktion außer X.

## Originalquellen und Rekonstruktion

- `assets/stage5b/original_sources/Vyper_Startscreen.uss`, SHA-256 `d836cbf88f0ac35b6ed3776df2add39f699113c1aeb9d02cdfe4651c82793916`.
- `assets/stage5b/VYGR.DAT`: korrigierte 38-Typen-/259-Frame-Datei, identisch mit Stable-Spieldaten.
- WinUAE-CRAM enthält die vier aktiven Menü-Bitplanes bei $27770/$29BB0/$2BFF0/$2E430; aktive COP2-Liste $184AE. Copper aktiviert vier Lowres-Bitplanes ($4200) für Raster 44–243, Fetch $38–$D0: 320×200 Pixel. Die Pixel werden direkt aus diesen Original-Bitplanes rekonstruiert, nicht aus einem Mockup.
- Kompakter CHIP-Chunk: COLOR0..31 ab Offset $E4. Alle von COP2 zuletzt geschriebenen Farben werden dagegen geprüft. COLOR2=$0EC und COLOR3=$DD0 bleiben von COP2 unbeschrieben; sie müssen aus dem gespeicherten Registerzustand übernommen werden. Sonst fehlen Banner und Hinweise im Rekonstruktionsbild. **Keine Levelpalette für das Menü.**
- Vollständiger Anfangsbildschirm: 64.000 Farbindex-Pixel inklusive Originalschrift, cyanfarbenem Rahmen, Anordnung und Zwischenräumen exakt wiederhergestellt. `original_menu_reference.png` und `original_menu_indices.bin` liegen im Release.

Die 32 Positionen werden durch vollständigen 16×16-Pixelvergleich aller 259 VYGR-Frames gefunden: je Position genau ein Typ. Typ 23 steht tatsächlich an Position 6 der ersten Reihe. Nicht sichtbar sind Typen 6, 7, 8, 12, 37 und 38. Die Werte sind VYGR-Typnummern (1-basiert), keine VYLV-Indices.

Zusätzliche unabhängige Prüfung der 32 Originalobjekte: CRAM $2404A, Stride $92. X/Y bei +$10/+$12 (gespeichertes Zeichnungs-Y = sichtbares Y+16), Framezeiger +$14, Basiszeiger +$54, Countdown +$58, Periodendauer +$5A, Frameanzahl +$5E. Die Routine BRAM $D890–$D8C8 dekrementiert Countdown, lädt die individuelle Dauer nach, erhöht den Deskriptorzeiger um $20 und setzt ihn bei Sequenzende zurück. Stage 6a1 übernimmt Countdown und Intervalle von 1–6 Frames. Das sichtbare Frontbild kann gegenüber dem vorbereiteten Deskriptor abweichen; als Anfangsphase wird eine nachgewiesene sichtbare Phase gewählt, bevorzugt aktuelle/vorherige. Symmetrische, pixelgleiche Frames sind in der JSON-Liste ausgewiesen. **Keine Aussage über einen eigenen ausgeführten WinUAE-Zeitverlauf.**

## Typen, Positionen und Animation

Koordinaten bezeichnen die linke obere Ecke im originalen 320×200-Bild.

| Slot | VYGR-Typ | X | Y | Frames | Startframe | Intervall (PAL-Frames) |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 40 | 20 | 4 | 3 | 4 |
| 2 | 2 | 72 | 20 | 7 | 0 | 4 |
| 3 | 3 | 104 | 20 | 10 | 9 | 4 |
| 4 | 4 | 136 | 20 | 6 | 4 | 5 |
| 5 | 5 | 168 | 20 | 8 | 1 | 4 |
| 6 | 23 | 200 | 20 | 4 | 0 | 3 |
| 7 | 9 | 232 | 20 | 8 | 5 | 5 |
| 8 | 10 | 264 | 20 | 4 | 2 | 2 |
| 9 | 11 | 24 | 44 | 6 | 1 | 5 |
| 10 | 13 | 56 | 44 | 4 | 2 | 3 |
| 11 | 14 | 88 | 44 | 8 | 1 | 4 |
| 12 | 15 | 120 | 44 | 6 | 1 | 6 |
| 13 | 16 | 152 | 44 | 6 | 4 | 5 |
| 14 | 17 | 184 | 44 | 12 | 7 | 5 |
| 15 | 18 | 216 | 44 | 12 | 4 | 5 |
| 16 | 19 | 248 | 44 | 4 | 0 | 1 |
| 17 | 20 | 280 | 44 | 8 | 6 | 4 |
| 18 | 21 | 40 | 68 | 9 | 3 | 2 |
| 19 | 22 | 72 | 68 | 4 | 2 | 3 |
| 20 | 24 | 104 | 68 | 12 | 1 | 2 |
| 21 | 25 | 136 | 68 | 6 | 4 | 3 |
| 22 | 26 | 168 | 68 | 8 | 2 | 6 |
| 23 | 27 | 200 | 68 | 4 | 2 | 3 |
| 24 | 28 | 232 | 68 | 8 | 0 | 3 |
| 25 | 29 | 264 | 68 | 6 | 3 | 5 |
| 26 | 30 | 56 | 92 | 8 | 2 | 3 |
| 27 | 31 | 88 | 92 | 8 | 0 | 4 |
| 28 | 32 | 120 | 92 | 8 | 5 | 3 |
| 29 | 33 | 152 | 92 | 12 | 8 | 4 |
| 30 | 34 | 184 | 92 | 4 | 2 | 6 |
| 31 | 35 | 216 | 92 | 3 | 1 | 2 |
| 32 | 36 | 248 | 92 | 4 | 1 | 5 |

## Originaltexte

Die Originalschrift wird als Pixelgrafik übernommen; kein Ersatzfont, keine komprimierten Zeichen. Die Formatstrings liegen zusätzlich im BRAM-Chunk und werden bei der Konvertierung geprüft:

- `- VYPER -` — Originalformat bei BRAM 0xc30e.
- `- BONUS SHIP EVERY 3 WAVES -` — Originalformat bei BRAM 0xc318.
- `- SELECT OPTION WITH JOYSTICK OR KEYBOARD -` — Originalformat bei BRAM 0xc336.
- `INITIAL LEVEL 001` — Originalformat bei BRAM 0xc362.
- `F1 START 1 PLAYER GAME` — Originalformat bei BRAM 0xc375.
- `F2 START 2 PLAYER GAME` — Originalformat bei BRAM 0xc38c.
- `F3 VIEW HIGH SCORES` — Originalformat bei BRAM 0xc3a3.

`BONUS SHIP EVERY 3 WAVES` ist der originale Wortlaut des Hinweises auf ein Extra-Leben alle drei Level. `INITIAL LEVEL 001` entspricht dem Originalformat `%03d` bei Ausgangswert 1. Sämtliche Texte sind rein grafisch; F1/F2/F3, Joystick, R, + und − haben keine Menüwirkung. Nur X/x beendet den Test.

## Rendererentscheidung und Kapazität

VIC-IV hat hier **keine globale Grenze von 24 RRB-Pixies**. Die vorhandene Spielengine ist jedoch auf 22 Gegner plus Player und ein 240-Pixel-Playfield mit HUD zugeschnitten. Ihre Arrays/Schleifen sind nicht für 32 Menügegner ausgelegt. Der RRB-Renderer verwendet `V014_CAPACITY=24` **Fragmente pro Bildschirmzeile**, 24×4 Bytes plus Terminator in einem 100-Byte-RRB-Bereich. Im Originalmenü befinden sich maximal neun Gegner nebeneinander, also grundsätzlich weniger als diese Zeilenkapazität. Das beweist keine direkt unverändert nutzbare 32-Objekt-Spielengine. Eine Engine-Erweiterung wäre unnötig und würde die geschützte Architektur betreffen.

Stattdessen separater **FCM-Renderer**: CHR16/FCLRHI, 40×25 Zellen zu 8×8 Pixeln, RRB/GOTOX/NCM/Hardware-Sprites abgeschaltet. Die festen Positionen liegen auf X-Vielfachen von 8, Y mod8=4. Jeder 16×16-Gegner belegt daher sechs FCM-Zellen (2×3). Vorberechnete komplette Zellen pro Originalframe enthalten schwarze transparente Flächen und die ursprünglichen Pixel. Alle sechs Zeiger werden gemeinsam ersetzt; dadurch bleiben keine alten Masken-/Framepixel zurück. Die Footprints sind disjunkt. Animation verändert ausschließlich diese 192 Zellen, niemals Text oder Rahmen.

984 deduplizierte Kacheln, 62.976 Grafikbytes. VYMN.DAT hat 63.093 Bytes: 18-Byte-Header (Magic VYMN, Version1, 320/200, 33 Palettenslots, Kachelbytes, Payloadsumme), 99 RGB-Bytes, FCM-Kacheln. COLOR0..15 sind original; unbenutzte Einträge16..32 sind Null für den wiederverwendeten, 33 Einträge sichernden Loader. Nach Laden/Prüfung wird der 117-Byte-Präfix per vorwärtsgerichteter DMA entfernt. Frames/Screen-Zeigertabellen liegen im PRG; die vollständige VYGR-Datei muss nicht zusätzlich eingelesen werden. Das generierte Menü-Asset stammt ausschließlich aus originalen USS/VYGR-Daten.

Bewährter eigenständiger Stage-5d-0-SEQ-Lader: SETBNK vor SETNAM, IRQs während KERNAL-I/O aktiv, DMA-Rückkopie/Bytevergleich, exakte EOF-Länge, Dateisumme und vollständiger Header-/Palettenvergleich. Fehler werden vor dem Moduswechsel als `STAGE 6A1 LOAD ERROR $xx` in BASIC ausgegeben; Kanäle werden geschlossen.

## Speicher und Exit

| Bereich | Verwendung |
|---|---|
| $2001–$200C | BASIC SYS 8448 |
| $2100–$2789 | Eigenständiger Loader, Palette/VIC-Restore |
| $2800–$28CB | Animationsroutine, private temporäre Werte |
| $4000–$47CF | FCM-Color-RAM-Nullvorlage |
| $5000–$57CF | Unveränderte Initial-Screenvorlage für wiederholtes RUN |
| $6800–$68FF / $6900–$69FF | SEQ-/DMA-Prüfpuffer |
| $7000–$77CF | Eigener 2.000-Byte-FCM-Screen |
| $8000–$8B9C | Frame-Zeigertabellen, Metadaten, 32 Frame-/Countdownzustände |
| $15000–$157CF | Sicherung des privaten Color-RAM-Fensters |
| $40000–$4F674 | SEQ-Staging VYMN.DAT |
| $40000–$4F5FF | Ausgerichtete FCM-Kacheln nach Prefixentfernung |
| $FF82000–$FF827CF | Privates Color-RAM-Fenster |

Kein Zugriff auf ROM $20000–$3FFFF oder DOS $10000–$11FFF. BASIC-Screen und BASIC-Color-RAM bleiben unberührt. Menu-VIC-Einstellungen nutzen Palettebank1, 320×200 logische Pixel, 2×2 native Pixel; Native-Origin X80/Y88, unterer Rand exklusiv488. Cyanrahmen ist Teil des Originalbildes, Außenborder schwarz.

IRQ wird während Anzeige/Animation gesperrt, Hardware-ASCII-FIFO $D610 bleibt nutzbar. X/x restauriert Palette, privates Color-RAM und alle veränderten VIC-Felder einschließlich Sprite/RRB, Screen-/Color-Zeiger, Charsetmodus, Rastervergleich und CPU-FAST. Die in Stage 5d-1a bestätigte HOTREG-Reihenfolge wird separat übernommen: Legacy-Updates vor präziser Geometrie abarbeiten, HOTREG abschalten, präzise Felder wiederherstellen, HOTREG zuletzt. BASIC-Cursorzustand/Screen wird nicht überschrieben. Ursprünglicher IRQ-Status wird wiederhergestellt. RUN setzt alle Frame-/Countdownzustände und den Screen zurück.

## Timing und automatisch ausgeführte Prüfungen

Ein Tick pro PAL-Frame an logischem Raster250 (nativ500), nach Menüende488; die Leave-Schleife verhindert einen zweiten Tick im selben Frame. `MENU_FRAME_DIVIDER=1` ist die zentrale Testgeschwindigkeits-Skalierung; individuelle Originalintervalle bleiben bestehen. CPU-FAST 3,5MHz wird für die Anzeige aktiviert und beim Exit restauriert.

Worst case: Alle 32 wechseln gleichzeitig. CPU-Modell 12,385 Zyklen, entsprechend 3.539 ms bei3,5MHz. Vergleichswert, keine Raster-/Busmessung unter XEMU. Keine DMA im Frameupdate.

Acht automatische Tests bestanden: reproduzierbare Konvertierung, vollständige Original-Pixel-/Paletten-/Textprüfung, 80 Tickupdates mit allen Frames sämtlicher 32 Typen gegen unabhängige originale Bitplanes/Masken, kein Ghosting, einmaliger Framegate, Framebudget, sichtbare Loaderfehler, Kanalabschluss, vollständiger Exit/HOTREG mit ursprünglichem IRQ-Zustand, F1/F2/F3/R/+/- ohne Wirkung, mehrfaches RUN, D81-Dateiketten und Stable-Dateischutz. Diese Tests laufen auf dem assemblierten PRG mit CPU/KERNAL/DMA-Modellen; **kein eigener XEMU-Lauf**.

## Reproduzieren und XEMU-Abnahme

```sh
python tools/convert_stage6a1_menu.py
python tools/build_stage6a1.py --kickass /path/to/KickAss.jar
PYTHONPATH=tests:tools:/path/to/py65 python -m unittest test_stage6a1 -v
python tools/package_stage6a1.py
```

KickAssembler5.25 wird durch SHA-256 geprüft; Python benötigt Pillow und py65. Für Konvertierung/Build ist Capstone nicht erforderlich; dessen lokale Nutzung diente nur der Amiga-Analyse. Originalassets und Stable-Tag müssen im Repository vorhanden sein. Release: `releases/stage_6a1/`, vollständige generierte ASM/Includes, PRG, VYMN.DAT, D81 und Diagnosebild.

In XEMU (PAL) `VYPER_STAGE6A1.d81` mounten, `LOAD"STAGE6A1",8`, `RUN`:

1. Alle vier Reihen (8/9/8/7) und Originalreihenfolge mit WinUAE vergleichen, insbesondere Typ23 in Reihe1. Jeder Gegner muss animieren, einschließlich Typ19 mit 1-Frame-Intervall.
2. Farben, cyanfarbener Rahmen, gelber VYPER-Titel, Hinweise und rote Initial-Level-Zeile mit dem Original vergleichen. Kein HUD.
3. Länger laufen lassen: keine alten Frames, Zeilenartefakte oder Flackern; 50-Hz-Stabilität ist noch vom Benutzer zu bestätigen.
4. F1/F2/F3 und Joystick dürfen nichts auswählen/starten. X/x → normaler BASIC-Screen/Cursor. DIRECTORY muss funktionieren; mehrfaches RUN reproduziert den Startzustand.
5. Keine Stable-Markierung bis zur ausdrücklichen Benutzerabnahme.

Bekannte Grenzen: feste PAL50Hz-Testgeometrie, keine NTSC-Abnahme; zeitliche Front-/Backbufferphase des Amiga-Snapshots ist nicht eindeutig für pixelgleiche Frames. Die Schrift und das Anfangsbild sind pixelgenau, jedoch ohne CRT-/Amiga-Ausgabefilter. Keine Titelbild-/Spielintegration, Sound, Menüsteuerung oder Bonuslogik.

Ausgeführter Testlauf: 8/8 erfolgreich in17,223s. Unabhängiger Zweitbuild: alle15 Build-Dateien byteidentisch. Das bereits konvertierte Release lässt sich auch direkt assemblieren: im Release-Verzeichnis `java -jar /path/to/KickAss.jar stage6a1.asm -o STAGE6A1.PRG -symbolfile`. Sämtliche dafür benötigten ASM/Include-/Binärdateien liegen dort.
