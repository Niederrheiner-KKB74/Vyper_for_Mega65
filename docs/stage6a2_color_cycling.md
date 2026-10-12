# Stage 6a2 – originales COLOR02-Cycling (Issue #45)

Eigenständiger Testbranch `stage6a2`, **nicht Stable**. Ausgangsbasis ist der vom Benutzer funktionierend bestätigte Stage-6a1-Testcommit `65e8b4e700626288906ea79954eb52641fd0bb15`. Stage6a1-Dateien und `stage5d1a-stable` bleiben unverändert. Keine Integration in Spielengine oder produktiven Loader.

## Nachgewiesener gemeinsamer Farbindex

Quelle: `assets/stage5b/original_sources/Vyper_Startscreen.uss`, SHA-256 `d836cbf88f0ac35b6ed3776df2add39f699113c1aeb9d02cdfe4651c82793916`. CRAM-/BRAM-/CHIP-Chunks enthalten gleichzeitig den Bildschirm, Code, aktiven Copper und lebende Zustandsdaten. Die vorhandene Original-VYGR-Datei bleibt identisch. Die frühere Levelpalettenanalyse `docs/color_palette_analysis.md` und die20 Originalpaletten werden nicht als Menü-Cyclingfolge verwendet.

**Amiga COLOR02 ($DFF184), im eigenständigen FCM-Menü direkt Pixelindex2.** Der Rahmen benutzt an allen vier Ecken Index2. Die BONUS-SHIP-Zeile enthält338, die SELECT-OPTION-Zeile530 Index2-Pixel (jeweils inklusive seitlicher Rahmenpixel in den geprüften Zeilenbereichen). VYGR verwendet sichtbare Originalfarbe+1 unter der Originalmaske: NCM-Nibble3 entspricht daher Originalfarbe2. Die FCM-Konvertierung setzt dies bereits zurück auf2. Anzahl und Verteilung der betroffenen Pixel pro Gegnerframe sind in `color-cycling-analysis.json` dokumentiert.

Alle diese Pixel benutzen denselben Menü-Paletteneintrag; es ist keine zusätzliche Indexreservierung und keine Änderung der Grafik-/Masken-/Textdaten erforderlich. Die synchron wechselnde Farbe folgt aus der Originalbelegung, nicht aus nachträglichem Übermalen. Die übrigen Menüfarben einschließlich Hintergrund0, Weiß1, gelber Titel3 und roter INITIAL-LEVEL-Zeile8 bleiben unverändert.

## Originalalgorithmus und IRQ-Beleg

- Registrierungs-Code BRAM $9D10–$9D24: PC-relativer Zeiger auf $C0CFF2, IS-Code im Interruptnode, Interruptnummer4.
- Gespeicherter Interruptnode CRAM $22E5E: `is_Code=$C0CFF2`; Userdata liefert A4=$2013E.
- API-Stub CRAM $1815E springt nach $C1180E. Bridge BRAM $1180E lädt d0/a1 und springt nach Exec−$A8: **AddIntServer**, Nummer4 = COPER.
- Aktive COP2-Liste $184AE enthält genau eine `INTREQ $8010`-Anforderung ($18572), COP1 ruft COP2 auf. Die Menü-Liste läuft einmal je Bild. Die ursprüngliche Farbsteuerung läuft somit im Copper-Interrupt, nicht in der Pixie-Animation.
- Handler BRAM $CFF2–$D07C: Aktualisierung nur wenn A4+$2C42 !=0. Kern $D042–$D074 addiert ein signed WORD-Delta zum RGB4-Wort, schreibt $DFF184, dekrementiert einen Abschnittszähler, lädt bei0 den Wert7 und erhöht den Tabellen-Byteoffset um2; bei12 beginnt die Tabelle erneut.
- Sechs Original-WORDs in CRAM $18214: `$0020,$FE00,$0002,$FFE0,$0200,$FFFE`, signed `+32,−512,+2,−32,+512,−2`.

Der Analysator prüft relevante Originalopcodes, API-Stub/Node, Delta-Tabelle und gespeicherte Zustandswerte bytegenau. Keine Capstone-Abhängigkeit für Reproduktion; lokale 68000-Disassemblierung diente nur der Untersuchung. Die Instruktionsbelege werden anhand der Originalbytes erneut geprüft.

| Abschnitt | Kanaländerung je Tick | Ticks | Vom kanonischen Start erreichte Ecke |
|---:|---|---:|---|
|0|Grün +2|7|$EE0 (Gelb)|
|1|Rot −2|7|$0E0 (Grün)|
|2|Blau +2|7|$0EE (Cyan)|
|3|Grün −2|7|$00E (Blau)|
|4|Rot +2|7|$E0E (Magenta)|
|5|Blau −2|7|$E00 (Rot)|

Die maximale Kanalstufe ist **14**, nicht15. Ein kompletter Zyklus umfasst42 Farbänderungen. Bei PAL50Hz ergibt der Code **20ms je Änderung,140ms je Abschnitt,840ms je Zyklus**. Dies ist durch Registrierung/Copper/Code abgeleitet; kein eigener WinUAE-Zeitmesslauf. Für Originalfolge und PAL-Zeitbasis ist keine angenäherte Regenbogentabelle nötig.

Globale Initialisierung BRAM $A1E4–$A1F2 setzt `$E00`, Tabellenoffset0, Countdown7. Der Savestate enthält dagegen bereits `$0EC`, Tabellenoffset4 (Abschnitt2), Countdown1; gespeichertes CHIP-COLOR02 entspricht `$0EC`. Stage6a2 startet bewusst in diesem **Snapshotzustand**, damit das Anfangsbild zu Stage6a1 passt. Erstes Update ist `$0EE`; danach folgt Grün-Abbau. Weiterlaufen innerhalb des Menüs ohne Reset; RUN startet reproduzierbar wieder beim Snapshotzustand.

Der Originalhandler lässt seinen Farbzustand bei geschlossenem Gate stehen. Der nachgewiesene Initialisierer setzt ihn zurück; eine vollständige Laufzeituntersuchung aller Spiel-/Levelübergänge ist hier nicht durchgeführt. Die32 Animationen und ihre Originalcountdowns bleiben unabhängig. Der Handler enthält zusätzlich ein COLOR03-Blinken (XOR `$DD0` alle20 IRQs); das wird **nicht** übernommen, da der Auftrag den COLOR02-Effekt und unveränderte übrige Texte verlangt.

## RGB4-Folge des integrierten Snapshotstarts

Tick0=$0EC. Danach42 Änderungen, mit anschließender Wiederholung:

```
$0EE,$0CE,$0AE,$08E,$06E,$04E,$02E,$00E,$20E,$40E,$60E,$80E,$A0E,$C0E,$E0E,$E0C,$E0A,$E08,$E06,$E04,$E02,$E00,$E20,$E40,$E60,$E80,$EA0,$EC0,$EE0,$CE0,$AE0,$8E0,$6E0,$4E0,$2E0,$0E0,$0E2,$0E4,$0E6,$0E8,$0EA,$0EC
```

## VIC-IV-Implementierung

Neue Quellen: `src/tests/stage6a2.asm`, byteidentischer Menüanimator `stage6a2_animation.asm` und isolierter Palettenalgorithmus `stage6a2_cycling.asm`. Das Hauptprogramm hat nur zwei neue Hooks: `cc_init` vor der Anzeige und `cc_tick` nach jedem bisherigen Menü-Tick am logischen Raster250 (nativ500, unterhalb des Menüendes488). Die Leave-Schleife verhindert Mehrfachupdates im selben Bild.

`cc_tick` führt das signed16-Bit-Addieren und die sieben Schritte je Abschnitt aus. `cc_publish` erweitert jeden RGB4-Kanal durch Nibble-Duplizierung (0..14→0..238) und schreibt **$D102/$D202/$D302**. Es mappt dafür explizit Palettebank1, erhält die Anzeige-Bankbits von $D070 und stellt den vorherigen Mappingwert wieder her. Nur Index2 in dieser Bank wird verändert. Kein Screen-/Grafik-DMA, keine Neukonvertierung, keine Änderungen an Pixel-, Masken-, Frame- oder Texttabellen pro Cycling-Tick. A/X/Y und CPU-Flags werden erhalten.

Einfacher Abgleichparameter: `COLOR_TICK_DIVIDER=1` am Beginn von `stage6a2_cycling.asm`. Wert2 halbiert die Farbgeschwindigkeit, ohne die Animationstimer zu verändern. `color_cycle.inc` enthält die aus dem Original generierten Startwerte, Abschnittslänge und signed Deltas; abweichende Testwerte wären ausdrücklich als Teständerung zu kennzeichnen. Standardbuild verwendet die Originalwerte.

## Speicher und Laufzeit

Bisherige Menü-/SEQ-/FCM-/Color-RAM-Bereiche bleiben identisch zu Stage6a1. Das Hauptsegment wächst um zwei JSRs von $2100–$2789 auf **$2100–$278F**, weiterhin unter dem Animator $2800. Neues isoliertes Cyclingsegment einschließlich Zuständen/Deltas: **$3000–$30BF**, weit vor Color-Vorlage $4000. Keine Änderung an High-RAM-Grafiken $40000–$4F5FF, Screen $7000–$77CF oder Frame-/Countdowntabellen $8000–$8B9C. IRQs bleiben während der Darstellung gesperrt; alle RGB-Kanäle werden im gleichen unsichtbaren Frameabschnitt gesetzt.

Zusatzaufwand im 6502-CPU-Modell: 231 Zyklen, 0.066ms bei3,5MHz. Der bisherige Worst Case aller32 Framewechsel beträgt12.385 Zyklen. Modellwerte ohne Bus-/Rastercontention, keine Hardwaremessung.

X-Exit verwendet denselben vollständigen Palette-/VIC-/HOTREG-/Color-RAM-Restore wie6a1. Der originale Palettebank1-Index2 wird ebenso restauriert wie alle33 gesicherten Einträge; auch nach mehreren Farbzyklen. BASIC-Cursor/Screen werden nicht überschrieben. Keine IRQ-Handlerinstallation auf dem MEGA65; nach Exit läuft kein Cycling weiter. Keine Player-/HUD-/Explosionspalette in der stabilen Engine geändert.

## Ausgeführte automatische Tests

12 Tests bestanden: alle8 Stage6a1-Darstellungs-/Animations-/Loader-/Exit-Prüfungen sowie vier zusätzliche Cyclingprüfungen. Getestet werden vier vollständige42-Schritt-Zyklen gegen Originaldelta-/Zustandsdaten, alle RGB4-Werte und Rückkehr zum Startzustand, Register-/Flagserhaltung, Mappingwechsel und ausschließliche Änderung von Bank1/Index2, unveränderte Pixel-/Screenbytes und keine DMA im Cycling, synchroner gemeinsamer Index, nur ein Cycling-Update je Rastergate, drei cycled X/RUN-Durchläufe mit vollständigem Restore sowie reproduzierbare Analyse. Originalmenü-Asset `VYMN.DAT`, FCM-Kacheln und Screen/Animationstabellen sind byteidentisch zu6a1.

Die Tests laufen auf dem tatsächlich assemblierten PRG mit CPU/KERNAL/DMA-Modellen. **Kein eigener XEMU-/WinUAE-Lauf.** Originalbefunde sind statisch verifiziert, die Zeitangabe ist code-/PAL-abgeleitet und die Startphase ist eine explizite Snapshotwahl.

## Reproduzieren und XEMU-Abnahme

```sh
python tools/analyze_stage6a2_cycling.py
python tools/build_stage6a2.py --kickass /path/to/KickAss.jar
PYTHONPATH=tests:tools:/path/to/py65 python -m unittest test_stage6a2 -v
python tools/package_stage6a2.py
```

KickAssembler5.25, Python/Pillow/py65, Repository mit Originalassets und Stable-Tags erforderlich. Release `releases/stage_6a2/` enthält vollständige ASM, Includes, Binärdateien, PRG, D81, Originalanalyse/Trace und Prüfberichte. Direktes Assembly im Releaseverzeichnis ist ebenfalls möglich: `java -jar /path/to/KickAss.jar stage6a2.asm -o STAGE6A2.PRG -symbolfile`.

PAL-XEMU: `VYPER_STAGE6A2.d81` mounten, `LOAD"STAGE6A2",8`, `RUN`. Rahmen, BONUS-SHIP-/SELECT-OPTION-Zeilen und entsprechende Gegnerdetails müssen synchron den cyan/blau/magenta/rot/gelb/grün-Zyklus durchlaufen. Geschwindigkeit mit WinUAE vergleichen (Standard42 Frames pro Runde). Alle32 Gegner, Originalschrift/-anordnung und sonstigen Farben müssen wie6a1 bleiben. F1/F2/F3/Joystick bleiben ohne Funktion. Länger laufen lassen, dann X, DIRECTORY und mehrfaches RUN testen. Kein Flackern/Ghosting oder Paletteverlust nach Exit.

Stage6a2 bleibt **nicht Stable** bis zur ausdrücklichen Abnahme. Gameplay-Cycling wird später separat integriert; der Menü-FCM-Index2 darf nicht ungeprüft als Spieler-/Gegner-NCM-Palettenindex übernommen werden.

Testlauf:12/12 erfolgreich in21,883s. Unabhängiger Zweitbuild: alle18 Builddateien byteidentisch. Sämtliche sieben bestehenden Menü-Assetdateien stimmen bytegenau mit6a1 überein. ZIP enthält die vollständigen generierten Assembly-/Include-/Binärdateien und wird deterministisch geprüft.
