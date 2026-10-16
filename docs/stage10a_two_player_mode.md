# Stage 10a1 – Nachbesserung in PR #88

Entwicklungsstand im bestehenden Branch `stage10a`; Ausgangspunkt
`dd11d2a50fd777162946479098796c55c61fcd53`. Stage 9c3a/`main` und die bisherigen
Stage-10a-Dateien bleiben unverändert. Kein Stable-Tag und kein Merge.

## HUD-Nachbesserung nach Funktionsbestätigung (PR88, 16.10.2026)

Der Benutzer bestätigt die bisherigen Stage10a1-Funktionen. Zwei zusätzliche
HUD-Korrekturen bleiben bis zur erneuten XEMU-Abnahme Entwicklungsstand:

- F2 erhält einen zweiten Balken in Zeile21, unmittelbar nach den P2-Lebenszeilen
  16–20. Der bestehende Balken12 bleibt. Beide kopieren dieselben 42 Screen- und
  Color-Präfixbytes der Vorlage6. Form./Att. bleiben22/23, Rand24 bleibt frei.
- Bei jedem statischen HUD-Neuaufbau werden alle25 Shadowbytes `$1A20–$1A38`
  invalidiert. Die vorhandene dynamische Ausgabe zeichnet anschließend Werte
  und Lebenssymbole neu, bevor die Hauptschleife und ENTRY sichtbar werden.

**Nachgewiesene Ursache:** `hud_init` zeichnete bereits drei P1-Leben und setzte
`shadow+10=3`. Danach löschte `integration.start_ready` mit `hud_draw_static` die
Lebenszellen erneut. `hud_render` sah unveränderte Leben und übersprang die
Ausgabe. Am ersten Hauptschleifenaufruf des unveränderten Vorgängers wurden in
F1 **und** F2 Leben=3, Shadow=3, aber null Lebensglyphen gemessen. Allein das
Invalidieren dieses Shadows und erneutes Rendern brachte neun Glyphen zurück
(drei Symbole mit je drei RRB-Zeilen). Keine Änderung an Lebenswerten erforderlich.
P2 erschien, weil dessen Life-Shadow beim ersten F2-Render noch ungültig war.

Der Fix hängt die Invalidierung an die bestehende25-Zeilen-Schleife des statischen
Aufbaus. Er benötigt weder zusätzliche Zustandsbytes noch Framearbeit. HUD-Code
endet nun exklusiv bei `$3E7E`, vor den Defaults `$3E80`; native Identitätslabels enden bei `$9A29`
(vor `$9A56`). Controller/Audio-ABI,
Screenstride192, RRB-Suffix, Pixie-Puffer, Charset und sämtliche Originaldaten
bleiben unverändert. Die neue Zeile21 wird nur im Zweispielermodus überschrieben.

Die frühere Aussage „F1-HUD bytegleich“ bezog sich auf den fehlerhaften Start ohne
Symbole. Nun werden das P1-Lebensfeld und der tatsächliche Angriffspunktwert beim Start
korrekt gezeichnet: Die statische Vorlage zeigte115, der unveränderte dynamische
Wert ist175. Der Fix ändert diesen Spielparameter nicht, sondern zeigt ihn sofort
an. Alle übrigen F1-Präfixe, Farben und der komplette Font bleiben bytegleich.
Aktuelle Prüfergebnisse stehen am Anfang von `stage10a1_test_results.txt`.

XEMU-Abnahme: F1/F2 zunächst in Level001 und einem anderen Startlevel starten.
Vor dem ersten Treffer müssen je drei Lebenssymbole vorhanden sein. F2 zeigt
Balken12 und21 ohne Überlappungen. Danach Lebensverlust, Wechsel, Bonus, normalen
und Test-Levelwechsel, R-Neustart, GameOver/Highscore→Menü→Neustart sowie
F3→Menü→F1/F2 prüfen. Werte1/2/8/9/29/30 dürfen maximalacht Symbole zeigen.
X→BASIC und erneutes RUN prüfen. Keine erneute Stable-/Mergefreigabe vorweggenommen.

## Menü: Nutzerkorrektur übernommen

Der Nutzer hat den F2-Menüstart als funktionierend bestätigt: Die gegenteilige
Beobachtung war ein Konfigurationsfehler. Der Menüquellcode bleibt nach
Dateinamen-/Stage-Normalisierung bytegleich. Cursor/Joystick-Auswahl und
RETURN/Feuer, direkte F2-Taste und Feuer-Loslasssperre werden zusätzlich getestet.
F1, F3, INITIAL LEVEL und Menü-Color-Cycling sind unverändert.

## Exit-Diagnose: ausführbarer Code wurde als Grafik-/Color-RAM wiederverwendet

Der Nutzer grenzt den Fehler auf den Zustand nach einem Lebensverlust/Wechsel
ein; direkt nach Levelstart funktioniert X. Die Meldung lautet
`Unhandled memory read ... $AA6CFD (PC=$FF4C)`.

Zwei konkrete Lebenszyklusfehler wurden am unveränderten dd11d2a nachgewiesen:

1. `exit_to_basic` wird auch intern beim Spielerwechsel verwendet.
   `titlecache.tc_restore` restauriert dabei `$4000–$47FF` und setzt `tc_saved=0`.
   `twop.resume` startete anschließend die HUD-Initialisierung erneut, die den
   gleichen Bereich mit dem Originalmenü-Font überschreibt. Das Cache-Flag wurde
   nicht wieder gesetzt. Beim nächsten Exit blieb Font statt Titel-/Loadercode
   im RAM. Stage 10a1 ruft vor jedem Resume und jedem neuen Spiel aus dem Menü
   `titlecache.tc_save` erneut auf.
2. `entry.e_save_colour` verwendet `$5000–$563F` als BASIC-Color-RAM-Sicherung.
   Dort liegen vorher Audio-Lader und Highscore-Bootstrap (`$5448…$55C3`).
   Der Highscore-Bootstrap wurde für einen echten erneuten BASIC-RUN nicht
   restauriert. Im lokalen XEMU sprang `s3b.entry` bei `$4802` nach `$5519`, wo
   Farbbytes als Befehle ausgeführt wurden; `$5529: JMP (...)` führte nach `$0000`.
   Der CPU-Verlauf liegt in `stage10a1_evidence/stage10a_original_pc0_trace.txt`.
   Der neue `bootstrapcache` sichert diese 1600 Bytes einmal je PRG-Load im
   Attic und restauriert sie **nach** dem Color-RAM-Restore bei jedem Exit.
   Wiederholtes RUN verwendet weiter diese gültige Sicherung. Ein erneutes LOAD
   initialisiert das private Cache-Flag mit dem neuen PRG wieder auf null.

Das ist ein Code-/Daten-Überlagerungsfehler, kein Anlass zum Übermalen des
BASIC-Bildschirms. Die gesicherte Titelkopie enthält auch die beim Boot erfassten
VIC-/Palettenwerte; sie wird nach der Restaurierung erneut vor Fontüberschreibung
bewahrt. Die zusätzliche Loaderkopie wird niemals aus bereits überschriebenen
Farbbytes neu erzeugt.

**Grenze des Befunds:** Die exakte Nutzeradresse `$AA6CFD/$FF4C` wurde lokal nicht
identisch reproduziert. Nachgewiesen und korrigiert sind die beiden ungültigen
Codezustände und der reale Wiederstartabbruch. Bei nativem ROM-Mapping ist
`$FF4C` das Operandbyte `$FA` des JMP bei `$FF4A`, kein regulärer Routinenanfang.
Das passt zu verlorener Kontrolle über den Befehlsstrom, beweist allein aber
keinen bestimmten Stack-/MAP-Fehler. Eine behauptete exakte Ursachenverkettung
zu dieser einzelnen Nutzeradresse wäre ohne dessen Ablauftrace nicht belegt.

Der vorhandene Stage-9c3a-Exit mit VIC/HOTREG, Screen-/Color-/Charset-Restore,
Sprites, Audio-/Mixer-Restore bleibt erhalten. Keine neuen Schreibzugriffe auf
KERNAL-Zero-Page oder IRQ-Vektoren. Originale Samples, DMA-Puffer und Klanglogik
wurden nicht verändert.

Zusätzlich wird der normale Wechsel jetzt **nach Rückkehr der vollständigen
Tastenaufrufkette in der Hauptschleife** gestartet. Das fragile Verwerfen von fünf
Stackbytes in `twop.poll` entfällt. X hat dort weiterhin Vorrang. Der Resume-Pfad
maskiert IRQs bis zum vollständig initialisierten nächsten Spielstart. Diese
Härtungen werden nicht als nachgewiesene alleinige Ursache der Nutzeradresse
behauptet. Der bisherige separate Game-Over-/Highscore-Abschluss bleibt erhalten.

## Zweispieler-HUD nach dem bereitgestellten Screenshot

Das Vorher-Bild liegt unverändert unter
`stage10a1_evidence/user_stage10a_before.png`.

| Inhalt | RRB-Textzeilen im 2P-Modus |
| --- | --- |
| HI-SCORE | 0/1, unverändert |
| PLAYER 1 / Score / Level | 3/4/5, unverändert |
| P1-Leben | 7–11, unveränderte 4×2-Anordnung |
| Horizontaler Trennbalken | 12 |
| PLAYER 2 / Score / Level | 13/14/15 |
| P2-Leben | 16–20, dieselbe 4×2-Anordnung, Y=130/147 |
| Zweiter horizontaler Trennbalken | 21 |
| Form. / Att. | 22/23, direkt untereinander |
| Unterer Abstand | 24 |

P/S/X- und NO-P2-Texte entfallen im 2P-HUD vollständig. Labels/Score/Level der
aktiven, noch lebenden Identität verwenden Gelb/Rot/Blau; die andere Identität
ist grau. Auch null Leben aktualisiert die Farben. Die Farbe wird beim
Identitäts-/Lebensstatuswechsel oder nach statischem Neuaufbau aktualisiert,
nicht durch zusätzliche Palette-Umschaltungen pro Raster.

Die internen WORD-Zähler bleiben auf 30 begrenzt; sichtbar sind weiterhin
`min(lives,8)` Schiffe einschließlich des aktuellen Schiffs. Kein Abziehen eines
zusätzlichen Lebens für die Anzeige. Hi-Score, Font, Playfield `[0,240)`,
Y-Clipping `[0,200)`, RRB-Zeilenbreite 192 und dynamische Gegnerplätze bleiben
unverändert. F1 verwendet weiterhin sein bestehendes HUD.

## Speicheränderungen gegenüber Stage 10a

| Bereich | Stage 10a1 |
| --- | --- |
| `$1B1A/$1B1B` | Privater HUD-Stilcache und Zeilenzähler; innerhalb bestehender Zustandsreserve |
| `$38BE–<$3963` | Bisher unerreichbare Legacy-Fontkopierroutine durch HUD-Stilhelfer ersetzt; Font kommt weiter aus dem Originalmenü |
| `$8880–$88BE` | Nativer Loadercache-Helfer, Flag und zwei DMA-Listen; vorher frei zwischen Ende `$8878` und Spritetabelle `$8900` |
| `$9900–$99B2` | Vorhandene native Gates/Resume, ohne manuelles Stack-Abwerfen |
| `$99B9–$9A27` | F2-Labels, Stilaktualisierung und Punktzeilenlayout |
| `$080A0000–$080A063F` | Neue 1600-Byte-Sicherung der ausführbaren Phase `$5000–$563F` |

Der neue Attic-Bereich liegt hinter dem Highscore-Archiv
`$08090000–$0809AFFF` und außerhalb aller PCM-, Titel-, Menü- und Streamingpuffer.
Kein neues ChipRAM jenseits `$5FFFF`, kein DOS-RAM und kein ROM-RAM als freier
Speicher beansprucht. Bestehende Typ-2-Animationsdaten `$A200–$A57F` bleiben
bytegleich. Die vier Audio-Engine-ABI-Adressen bleiben unverändert; vier
ursprüngliche NOPs und der ohnehin wirkungslose O-Vergleich geben die nötigen
acht Bytes für den Hauptschleifen-Wechsel frei. Die 50-Hz-Taktung bleibt erhalten.

## Reproduktion und Abnahme

```sh
python tools/build_stage10a1.py --kickass /pfad/KickAss.jar
PYTHONPATH=tests:tools:/pfad/py65 python -m unittest test_stage10a1 test_stage10a1_engine test_stage10a1_two_player -v
# Optional: bereits laufendes XEMU mit ROM V920413, Kopie der D81 und UART-Socket
python tools/check_stage10a1_xemu.py --socket /tmp/vyper.sock --output /tmp/stage10a1-xemu.json
```

Release: `releases/stage_10a/stage10a1/STAGE10A1.PRG` und
`releases/stage_10a/stage10a1/VYPER_STAGE10A1.d81`, neun SEQ-Dateien einschließlich
VYHI, sämtliche ASM-/Include-/Daten-Dateien, Symbole, Speicherkarte und SHA256.

Für den vorherigen Programmcommit914aaff gibt es echte lokale
**headless XEMU/ROM-V920413-Tests** mit unverändertem
UART-Monitorprotokoll: null, ein und zwei kontrollierte Spielerwechsel, X über
den ROM-GETIN-Puffer, bytegenauer Restore beider Codebereiche, Audio aus,
anschließend echtes BASIC-RUN bis zum Menü und DIRECTORY. Zusätzlich beide
Game-Over-Overlays mit kontrolliertem quit → Menü → neues F1 → X sowie X bei
tatsächlich laufender Original-Player-Death-PCM (DMA-CTRL geprüft, kein Hörtest).
Die Zustände
Menüauswahl und bereits abgeschlossene Player-Explosion (WAIT) werden dabei
gezielt im Emulator gesetzt. Das ist **kein** Test natürlicher Kollisionen,
physischer Joystickeingabe, subjektiver Bildqualität oder Stereoausgabe.
Maschinenprotokoll: `stage10a1_evidence/xemu_regression.json`.

Hosttests prüfen die assemblierten vollständigen Pfade einschließlich natürlicher
Explosions-Timer und modellierter DMA-Soundbeendigung, getrennte Spieler-/Bonus-
zustände, 30-Leben-Grenze/8-Symbole, Respawn/Unverwundbarkeit, Highscores bei
beiden Ausscheidereihenfolgen, neue Gleichstände vor alten, VYHI-Speicherung,
F1/F2/F3, Menüauswahl, Levelwechsel und Original-Assets. Hostmodell und physischer
MEGA65 sind ausdrücklich zu unterscheiden. Vollständiges Protokoll und noch
offene Benutzerabnahme: `stage10a1_test_results.txt`.

Unter dem Benutzer-XEMU bitte besonders erneut prüfen: tatsächlicher Treffer
mit vollständigem Explosionssound → P2 → X, danach RUN; P1→P2→P1→X; X während
BLINK und Audio; Highscore-Eingabe bei erstem/zweitem Ausscheiden; F3 und X aus
dem Menü; HUD-Farben und Lebenssymbole bei Bonus/Verlust sowie unverändertes F1.
Erst diese ausdrückliche Bestätigung erlaubt Stable/ Merge.

---

# Historische Dokumentation Stage 10a (vor Stage 10a1)


Ausgangsbasis ist der bestätigte Stage-9c3a-Stand aus `main`,
`36d5a4b546fb514e435d4567b36c68e8cd18b6e2` (getesteter Programmstand
`1f767223bb916fba9eb0d8bc5bad3503da2c30d4`). Entwicklung ausschließlich im
Branch `stage10a`; keine Stable-Markierung oder Merge vor XEMU-Freigabe.
Alle bisherigen Quellen, Assets, Buildwerkzeuge und Releases bleiben erhalten.

## Bedienung und Zustandsmodell

F1 startet wie bisher ein Einspielerspiel. F2 startet zwei abwechselnde Spieler
mit je drei Leben, Score null und dem ausgewählten INITIAL LEVEL (1–100).
Spieler 1 beginnt; beide benutzen weiterhin Joystick Port 2. Es gibt nur einen
aktiven Player und dieselbe unveränderte Kampfengine.

Je Identität werden Score (u32), Level (u16) und Leben (u16) getrennt gespeichert.
Zwei getrennte Bonuszähler zählen ausschließlich erfolgreich abgeschlossene
Level; ein Bonus nach drei Abschlüssen, unabhängig vom INITIAL LEVEL.
`+`/`−` ändern nur das Level des aktiven Spielers, ohne Bonus oder Umlauf.
Der normale Abschluss von Level 100 führt weiterhin zu Level 1.

Die Engine arbeitet unverändert mit einem aktiven Feldsatz bei `$1A04–$1A0B`.
Vor Wechsel und HUD-Ausgabe wird dieser in den Datensatz der tatsächlichen
Identität übernommen. Während der HUD-Ausgabe liegen beide Identitäten in den
vorhandenen P1/P2-HUD-Feldern. Vor weiterer Spiel-/Audioausführung wird der aktive
Arbeitssatz zurückkopiert. Ein gemeinsamer Session-Highscore überlebt dabei die
HUD-Neuinitialisierung; die Bestmarke aus der persistenten Tabelle wird ebenfalls
berücksichtigt.

Nach verbrauchtem Leben läuft zuerst die vollständige Explosion (sieben Frames,
je drei Ticks) ab. Solange der andere Spieler lebt, wird der normale WAIT→BLINK-
Respawn zurückgehalten. Die Original-Audio-DMA wird weiter bedient. Erst wenn
auch der erzwungene Player-Explosionssound auf Quelle 0 beendet ist, wird
umgeschaltet. Kein Wechsel bei bloßem Treffer während Unverwundbarkeit.

Der nächste Spieler startet seinen gespeicherten Level neu, mit seinem Score,
seinen Leben und seinem Bonusfortschritt. Geschosse, Gegner-/Explosionszustände,
RRB-Zeilen, Audio-Pending/BUSY und Eingabelatches werden über die vorhandenen
Exit-/Level-/Startpfade bereinigt. Der neue Player steht zentriert bei Y=184 und
startet mit 150 Frames Schutz, 25 Frames Blinkhalbperiode und sofortiger
Bewegungs-/Schussmöglichkeit, auch in unsichtbaren Blinkphasen.

Wenn der andere Spieler bereits ausgeschieden ist, bleibt der Überlebende aktiv:
keine Umschaltung, sondern der vorhandene normale Respawn in seinem laufenden
Level. Bei Verlust seines letzten Lebens wird auch sein Ergebnis verarbeitet.

## Game Over und Highscores

Bei null Leben bleibt das vorhandene 150-Frame-Game-Over-Fenster nach der Explosion
erhalten. Anschließend bekommt genau der ausgeschiedene Spieler die unveränderte
Qualifikationsprüfung und gegebenenfalls dreistellige Namenseingabe. Nach
Speichern/Tabellenende, fehlender Qualifikation oder Abbruch der Namenseingabe
setzt der noch lebende Spieler fort. Erst wenn beide ausgeschieden sind, geht es
zum Startmenü. Jeder ausgeschiedene Spieler wird durch den bestehenden
Einmalabschluss und die Identitätswechsel nur einmal eingetragen; zusätzliche
identitätsbezogene Abschlussflags protokollieren dies.

Gleichstände bleiben unverändert: Der neuere Eintrag kommt unmittelbar vor alle
alten Einträge gleicher Punktzahl, auch bei Rang 80; alte Gleichstände behalten
ihre Reihenfolge. VYHI-v1, Count/CRC16, TMP-/BAK-/Rename-/Readback-Verfahren und
Fehlerbehandlung sind unverändert. Schreibfehler führen weiterhin zur vorhandenen
Fehleranzeige und erlauben Rückkehr; kein Überschreiben beschädigter Recoverydaten.

F3 zeigt weiterhin die vierseitige Tabelle und kehrt zum Menü zurück. X beendet
auch im Zweispielermodus sauber nach BASIC; X aus der Tabelle verwendet weiterhin
den expliziten BASIC-Exit. R behält im Einspielermodus den bisherigen
Game-Over-Neustart bei. Im Zweispielermodus darf R einen ausgeschiedenen Spieler
nicht wiederbeleben oder dessen erforderliche Highscore-Prüfung überspringen;
dort erfolgt der automatische Abschluss, ein neues F2-Spiel beginnt im Menü.

## Leben und HUD

Die bisherige Symbolsemantik ist **lives**, einschließlich des gerade gespielten
Schiffs, nicht `lives−1`. Die Spielgrenze ist jetzt 30; Bonus 29→30 und 30→30.
Die Anzeige begrenzt unabhängig davon auf `min(8,lives)`. Ein unerwarteter
nichtnuller WORD-Highbyte-Wert wird sicher mit acht Symbolen dargestellt.

P1 behält Titel/Score/Level und das 4×2-Lebensfeld an den bisherigen Positionen.
Im bislang inaktiven P2-Bereich werden Titel, Score und Level auf Textzeilen
12/13/14 und ein gleichartiges 4×2-Lebensfeld bei Y=122/139 verwendet (RRB-Zeilen
15–19). Es gelten dieselben horizontalen Symbolpositionen, Farben und Abstände
wie bei P1 (Y=58/75). Die bisher unbenutzten P2-Platzhalter entfallen im F2-Modus;
für die zusätzlich benötigten Lebenszeilen stehen die Bedienkürzel P/S/X
kompakt in Zeile 21. Die vorhandene X-Zeile 20 bleibt erhalten. Playfield,
HUD-Außenbreite, Pixie-Geometrie und Paletten werden nicht verändert.
Ein `>` vor PLAYER 1 beziehungsweise PLAYER 2 markiert die aktive Identität.
F1 behält seine bisherige HUD-Darstellung.

## Original-Amiga-Untersuchung und ausdrücklich gewählte Einschränkung

`tools/analysis/analyze_amiga_player_switch.py` prüft die SHA256-Werte der drei
Originaldateien, extrahiert den Shot-HUNK aus der ADF, rekonstruiert dessen
Relokationen und vergleicht die untersuchten Codebereiche mit **beiden**
Original-Laufzeitkopien (ChipRAM-Dump und USS-BRAM). Befunde:

| USS-Adresse | Dump-Adresse | Nachgewiesener Codebefund |
| --- | --- | --- |
| `$C09528` | `$0228E8` | `SUBQ.W #1,$2C5E(A4)`, anschließend Aufruf `$C0B3AE` und Nullprüfung |
| `$C097B0–$C097C2` | `$022B70…` | Index `$2C3E(A4)` adressiert WORD-Einträge ab `$2C9E(A4)` und prüft den gewählten Eintrag |
| `$C09872–$C09888` | `$022C32…` | Summe der beiden WORDs `$2C9E/$2CA0`; bei null Sprung zum Menüpfad `$C08E68` |
| `$C0989A–$C098A0` | `$022C5A…` | Statuswort `$2C0C` wird 1; Rücksprung zum Rundenpfad `$C08EF4` |
| `$C08F1A/$C08F64` | `$0222DA/$022324` | Rundenpfad ruft `$C0A286` beziehungsweise `$C0A2EA` auf |
| `$C0A286–$C0A2E8` | `$023646…` | Zwei 12-Byte-Audiozustände initialisieren; `$000F` nach Paula-DMACON, keine Gegnerkopie in dieser Routine |
| `$C0A2F2–$C0A2FC` | `$0236B2…` | Levelindex `$2C10` × `$72` (114 Byte), Original-Levelbasis `$2C8E` |

Dies belegt konkrete Zähler-/Index-/Rundenpfade, aber **keine vollständige
Rekonstruktion**, welche laufenden Gegner das Amiga-Original bei einem Wechsel
speichert oder rekonstruiert. Der Datentyp dieser WORDs allein beweist auch keine
komplette Level-Snapshot-Semantik. Deshalb implementiert Stage 10a ausdrücklich
den im Auftrag erlaubten **Neustart des jeweiligen gespeicherten Levels**,
keine behauptete Originalwiederaufnahme. Bereits zerstörte Gegner erscheinen
beim erneuten Zug wieder. Original-Leveldaten und Kurven bleiben unverändert.
Disassemblierung und Prüfmetadaten: `docs/stage10a_amiga_evidence/`.

## Speicher und sichere Phasenwechsel

| Bereich | Stage-10a-Verwendung |
| --- | --- |
| `$1B00–$1B0F` | Zwei persistente Identitätsrecords à acht Byte |
| `$1B10–$1B19` | Modus, aktive Identität, Abschlussflags, Resume-/Gate-/HUD-Zustand |
| `$1B20–$1B23` | Gemeinsamer Session-Highscore |
| `$1FD9/$1FDA` | Bestehende, jetzt beide verwendete Bonuszähler |
| `$9900–$9A04` | Native Gate-/Wechsel-/Resume-Routinen, ersetzt unbenutzte dünne HUD-Fontkopie |
| `$A000–$A1E5`, `$A580–$A5E9` | Identitäts-/HUD-Controller, ersetzt unbenutzte eingebettete Legacy-Typ-1-Frames und bisher freien Platz nach Typ 2 |
| `$1920–<1A00`, `$6F00–<6F80` | Bestehende residente Highscore-Gates, gezielt um Capture/Return ergänzt |

`$1B00–$1B23` war im aktuellen Stand nur reservierter RRB-Arbeitsbereich;
kein ausführender Zugriff verwendete RRB_WORK. Es liegt vor dem unveränderten
Projektil-Registerbackup `$1B60`. Dieser Zustand liegt außerhalb der vom
Highscore-Overlay ersetzten Region `$2000–$CFFF` und überlebt die Tabellenphase.
Kein neuer Speicher im DOS-RAM `$10000–$11FFF`, im ROM `$20000–$3FFFF` oder
jenseits der tatsächlich vorhandenen ChipRAM-Grenze `$5FFFF`.

Der verwendete HUD-Font kommt seit Stage 6b1 aus dem Originalmenü, nicht aus der
retirierten Legacy-Fonttabelle. Tatsächliche Gegnerframes stammen aus VYGR und
privaten Puffern. Die Orbit-Initialisierung und die über `s3b2.animate` noch
aufgerufene `s2ja_animate_pixies`-Routine bleiben unverändert: Alle sieben
Typ-2-Frames bei `$A200–$A57F` werden ausdrücklich erhalten und mit der
Stable-PRG byteweise verglichen. Nur die unbenutzten Typ-1-Kopien werden ersetzt.
Es werden keine Originalassets überschrieben.

Der native Gate maskiert IRQs, schaltet nur D030.ROMA aus und restauriert D030
und Status vor Rückkehr. Im neuen A000-Controller erfolgen keine KERNAL-Aufrufe.
Vor Tabellen-I/O wird die vorhandene vollständige BASIC-/VIC-/Color-/Audio-
Restaurierung ausgeführt; VYHI verwendet weiterhin SETBNK vor SETNAM und native
ROM-/IRQ-Abbildung. Nach Tabellenende ist erst das Engineabbild restauriert,
dann wird über das native Gate die nächste Identität gewählt. Vor dem Sprung
zum Engine-Start wird ROMC wie bei der vorhandenen Menübrücke freigegeben.
Bei einem normalen Wechsel werden die fünf ausstehend gebliebenen Stackbytes
(bereits gelesene Taste, Rücksprung poll→key und key→main_loop) verworfen.
Der spätere X-Exit erreicht damit unmittelbar den ursprünglichen BASIC-Aufrufer.
Der Highscore-Pfad hat dagegen weiterhin seinen eigenen bisherigen Drei-Byte-
Abschluss. Tests vergleichen den Stackpointer nach P1→P2→P1 und prüfen X genau
im freigebenden Wechselframe.
Menüoverlay, ursprünglicher Titel-/Loadercode für RUN und Audio-Core bleiben
über ihre bestehenden Archive erhalten. Audio-Core, PCM-Datei und Original-
Level-/Grafik-/Farb-/Schussdaten werden bytegleich mit der Referenz geprüft.

## Reproduzieren und prüfen

KickAssembler 5.25 (SHA256-Prüfung im Builder), Java, Python 3 und Pillow wie bei
der Baseline; für CPU-Tests py65 1.2.0, für die Analyse Capstone 5.0.7.

```sh
python tools/build_stage10a.py --kickass /pfad/zu/KickAss.jar
PYTHONPATH=tests:tools:/pfad/zu/py65 python -m unittest test_stage10a test_stage10a_engine test_stage10a_two_player -v
PYTHONPATH=/pfad/zu/capstone python tools/analysis/analyze_amiga_player_switch.py
```

Ausgabe: `releases/stage_10a/STAGE10A.PRG`, `VYPER_STAGE10A.d81`, vollständige
Quellen/Includes, Overlay-/Audio-Dateien, Symbolfiles, Memory-Map, Buildbericht
und SHA256-Manifest. Das D81 enthält PRG und alle neun notwendigen SEQ-Dateien:
VYLV, VYGR, VYCL, VYTI, VYMN, VYSH, VYSO, VYHS und VYHI.

Die Hostprüfungen führen den tatsächlichen assemblierten Code in begrenzten
CPU-/VIC-/Audio-DMA-/KERNAL-/DOS-Modellen aus. Sie ersetzen weder XEMU noch echte
1541/1581-Sektorschreibvorgänge und belegen keine hörbare Wiedergabe.
Der Gesamtlauf enthält Kaltstart/Loader, erneutes RUN, F1/F3-Regression,
150/25-Respawn, F2-Wechsel, beide Ausscheidungsreihenfolgen, Gleichstände,
Lebens-/Bonusgrenzen, HUD-Zeichenzellen und simuliert fortschreitende Audio-DMA.
Ergebnisse im [Prüfprotokoll](stage10a_test_results.txt).

## XEMU-Abnahme (offen)

1. ROM V920413, Joystick Port 2; F1/F2/F3, Levelauswahl und `>`-Markierung prüfen.
2. P1→P2→P1 nach Tod, unterschiedliche Scores/Level/Bonusstände; erste, vierte
   und spätere Level. Kein Wechsel vor Explosions-/Soundende, keine Audio-/RRB-Reste.
3. P1 zuerst und P2 zuerst eliminieren, Namenseingabe/Speichern/Abbrechen,
   Gleichstand einschließlich Platz 80; nur der Überlebende spielt weiter.
4. Im neuen Zug 150-Frame-Schutz mit 25-Frame-Blinken; Bewegung und Schüsse auch
   während unsichtbarer Frames. Beim Überlebenden normaler Respawn ohne Wechsel.
5. Drei echte Abschlüsse pro Person → Bonus; Testnavigation erzeugt keinen Bonus.
   Level 100→1, HUD maximal acht Schiffe bei 9–30 tatsächlichen Leben.
6. Nach beiden Ergebnissen Menü/F3 prüfen, D81 beschreibbar neu starten und VYHI
   kontrollieren. R im F1-Game-Over-Fenster, X und anschließendes RUN/DIRECTORY.
7. Hörbare Originaleffekte, Sterne, Titel, Cycling, Levelübergang und hohe RRB-
   Belastung ohne neue Artefakte bestätigen. Erst danach Stable-Freigabe.
