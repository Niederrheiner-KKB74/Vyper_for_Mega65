# Stage9c3 – Highscore-Integration (Issue85, Entwicklung)

**Aktueller Testbuild: Stage9c3a, Nachbesserungen in PR86 (16.10.2026).**
Der Benutzer bestätigt den vorherigen Stand als funktional; keine Stable-Freigabe
für die Nachbesserung. Frühere Stage9c3-Artefakte bleiben unverändert.
Neue vollständige Artefakte: `releases/stage_9c3/stage9c3a/`.
Build: `python tools/build_stage9c3a.py --kickass /pfad/KickAss.jar`.
Start: `LOAD "STAGE9C3A",8` und `RUN`.
Die nachfolgende ursprüngliche Integrationsbeschreibung gilt mit den unten
aufgeführten Änderungen an Darstellung und Schussfreigabe.

Basis: main/Stage9b1 Stable6052f677a8b84a841549561e874cd2f3290b2129;
Highscore-Referenz Stage9c2 bbf996531f31920f2baa1111f74722d075fceba0.
Kein Stable, kein Merge vor XEMU-Bestätigung.

## Gemeinsame Speicherkarte vor der Integration

Die isolierte Tabelle darf nicht gleichzeitig mit der Engine im unteren RAM
liegen. Deshalb wird sie nur nach Audio-Stopp und BASIC-Video-Restore eingeblendet.

| Bereich | Verwendung |
|---|---|
|2000–CFFF|Engine oder Highscore-Overlay; vollständige Phasensicherung|
|1FE0–1FEF|Neue Übergangs-Mailbox, nach bestehenden Audio-/Bonusdaten bis1FDA|
|1920–19FF,6F00–6F7F|Residente Gates; nach Diagnosen1900–191F, vor HUD1A00/ATTACK6F80|
|5448–56FF|Transienter Gate-Seed/Loader vor BASIC-Colorsicherung; vom vorhandenen Audiobootstrap für RUN mitgesichert|
|A000–A7CF|Highscore-Seitenstaging statt6800–6FCF, Gates bleiben ausführbar|
|7000–77CF,8000–87FF|Highscore-Screen und privater WOM-Font nur in Tabellenphase|
|FF82000–FF827CF,15000–157CF|Highscore-Colorfenster und Sicherung|
|40000–47FFF|Overlay-Ladestaging ausschließlich vor dem anschließenden VYLV-Load|
|08080000–08087FFF|Neue unveränderliche Highscore-Codekopie im Attic|
|08090000–0809AFFF|Neue Sicherung2000–CFFF für Phasenwechsel|
|08000000–080252BF|Bestehende Titel-/Engine-/Menüsicherungen unverändert|
|0802C000–0802CFFF|Bestehender Audioloader für erneutes RUN|
|08030000–080574BF|Bestehendes Soundarchiv inklusive PCM unverändert|
|16400–173FF,5C500–5D4FF|Audio-Ringe; vor Tabellenphase gezielt gestoppt|
|1E000–1FFFF|Audio-Core unverändert|
|40000–53F80,54000–5C2B7|Originale Level-/Gegnerdaten unverändert|
|10000–11FFF,20000–3FFFF|DOS/ROM: keine neuen Puffer|

Menüaufbau lädt Atlas/Font erneut, bevor die32 Gegner wieder animiert werden.
Die neue Tabelle verwendet keine RRB- oder Audio-DMA-Wiedergabe.

Der neue Loader verwendet bewusst denselben nachgewiesenen Bank4-Stagingbereich
wie VYMN, bevor VYLV geladen wird. Bank6 ab60000 ist kein freies Chip-RAM.

## Zustandsmaschine und Bedienung

1. Boot zeigt weiterhin die Titelgrafik, lädt VYSO, das neue VYHS-Modul,
   VYMN und die Original-Spieldaten. VYHS wird wie die bisherigen SEQ-Dateien
   in256-Byte-Blöcken mit DMA-Rücklesevergleich geladen. Erwartete Länge und
   additive Prüfsumme sind fest im Build verankert; Attic-Prefix wird rückgelesen.
2. Vor dem ersten Menü wird VYHI einmal geprüft, ohne einen Tabellenbildschirm
   aufzublenden. Bei F3 und Game Over wird erneut gelesen, damit auch ein
   veränderter oder reparierter Diskettenbestand berücksichtigt wird.
3. F3 beendet den Menücontroller, sichert Initial Level und Auswahl, stellt
   den BASIC-Videokontext her und öffnet die vierseitige Tabelle. Links/rechts
   blättert; Feuer, RETURN oder andere Tasten führen wieder zum Menü. X in
   der Tabellenansicht beendet wie im Hauptprogramm nach BASIC. S ist jetzt
   eine normale Exit-Taste: keine simulierten Ergebnisse im integrierten Build.
4. Nach dem letzten Leben läuft die gesamte Player-Explosion weiter. Erst
   ab c_OVER läuft ein150-Frame-Fenster im normalen50-Hz-Loop; GAME OVER,
   Original-Sound und Audio-Streaming bleiben aktiv. R kann während dieses
   bestehenden Game-Over-Fensters wie bisher neu starten, X jederzeit beenden.
   Ein R-Neustart setzt den Übergangszähler zurück, ohne einen Score einzutragen.
5. Nach Ablauf wird der finale unsigned32-Bit-Score einmalig übernommen.
   Nicht qualifiziert: direkt Menü. Qualifiziert: exakt drei Namenszeichen,
   DEL korrigiert, RETURN bestätigt, ESC bricht ohne Dateischreiben ab.
   Nach Bestätigung wird die erreichte Seite gezeigt; deren Exit führt zum Menü.
6. Tabelle und Menü verlangen nach jedem Übergang die Freigabe von Feuer und
   Menü-/Cursortasten, bevor neue Eingaben angenommen werden. FIFO wird geleert.
   Gehaltenes F3 darf die Tabelle nicht unmittelbar wieder öffnen.

Die Input-/Gameplay-Routine bleibt bei normalen Frames gleich; nur der äußere
Key-Hook beobachtet den tatsächlichen Playerstatus. Weder Player-Tod mit Leben,
Levelwechsel, Bonusleben noch +/- können einen Tabellenübergang auslösen.
Der Original-Player-Death-Sound ID19 hat21546 Samples bei PAL-Paula3546895/388Hz,
also ungefähr2,36s. Das3s-Fenster beginnt erst nach der21-Frame-Explosion und
unterbricht diesen Sound deshalb nicht. Es gibt keinen neuen Game-Over-Sound.

## Video, Speicher und Audio beim Wechsel

Residente Gates1920/6F00 bleiben ausführbar, während die Phasensicherung die
Engine2000–CFFF auslagert. Beim Öffnen aus dem Menü wird zuvor dessen Overlay
7000–9FFF durch die ursprünglichen Enginebytes ersetzt. Beim Öffnen aus dem
Spiel läuft die bestehende vollständige Exit-Routine, einschließlich Audio-Stopp,
Sprite-, Sternen-, Übergangspaletten-, Skalierungs-, BASIC-Color- und VIC-Restore.
Nur der endgültige RTS nach BASIC wird durch den Phasenwechsel ersetzt.

Das Highscore-Modul verwendet weiter den bestätigten nativen80×25-Textmodus,
privaten WOM-Font und eigenes Colorfenster. Der Seitenpuffer wurde nachA000
verlegt, damit6800–6FFF nicht länger über residente Gates gerendert wird.
Die getestete CRC-/Sortier-/Dateilogik wurde ansonsten übernommen.
Auf dem Rückweg wird erst das Highscore-Video restauriert, dann die gesicherte
Engine zurückkopiert und das Originalmenü neu aufgebaut. Damit werden die
Menüatlasbereiche, Palette, Font und alle32 Pixies definiert initialisiert.
Der nächste F1-Start benutzt weiterhin s3b2.prepare, Audio-Install und den
Original-Engine-Start. Titel-/Audioloader bleiben für DIRECTORY und erneutes RUN
verfügbar. Die gespeicherte Tabellenbestmarke wird in den HUD-Highscore übernommen.

Es streamt kein Sample während Tabellenphase oder Disketten-I/O. Stop wird vor
jedem Einblenden aufgerufen, bevor Puffer oder KERNAL/DOS verwendet werden.
Während des Game-Over-Fensters läuft der unveränderte Audio-Service dagegen weiter.
Audio-Core, Originalsamples, Panning, Schuss-/Angriffsevents und Levelsequenz24→22
bleiben byteidentisch zur Stage9b1-Baseline.

## Datei und Sicherheit

VYHI v1 bleibt exakt592 Byte:32-Byte-Kopf, explizite Belegung0..80,80 Records
zu7 Byte (Name3, Score4 LE), CRC16-CCITT-FALSE ohne Prüfsummenfeld8/9.
Scorebereich0..4294967295 ohne Dezimaltrunkierung; echte0-Punkte-Einträge werden
von unbelegten Slots unterschieden. Neuer Score wird vor dem ersten kleineren
oder gleichen eingeordnet; bisherige gleiche Einträge bleiben stabil sortiert.
Bei80 belegten Plätzen qualifiziert daher auch Gleichstand mit Platz80.

VYHI.TMP schreiben, schließen, rücklesen, prüfen und bytevergleichen; vorhandene
VYHI.DAT erneut gegen Snapshot prüfen; alte BAK entfernen, DAT→BAK und TMP→DAT,
danach wieder prüfen. Keine behauptete atomare DOS-Transaktion. Beschädigtes DAT,
verwertbares BAK/TMP oder unklare I/O-Fehler führen zum konservativen Schreibschutz.
Keine automatische Löschung eines rettbaren TMP. Abgebrochene oder nicht
qualifizierte Eingaben schreiben nicht. Savefehler zeigen IO-/DOS-Codes und
Statusmeldung, rollen die RAM-Liste zurück und erlauben weiterhin den Menüweg.
SETBNK0 vor SETNAM, CLRCHN, CLOSE2 mit CLC und CLOSE15 mit SEC wie Stage9c2.

Dauerhafte Speicherung erfordert eine beschreibbare D81-Kopie und das Behalten
bzw. Exportieren der von XEMU geänderten Diskette. Ein erneuter Download ersetzt
sie durch die mitgelieferte leere Liste. Andere SEQ-Assets werden nur gelesen;
Schreib-/Scratch-/Renamebefehle betreffen ausschließlich VYHI.*.
Die D81 enthält jetzt10 Dateien und zwei verkettete Verzeichnissektoren;
BAM und sämtliche Dateiketten werden vom Builder geprüft.

## Reproduzierbarer Build

```sh
python tools/build_stage9c3.py --kickass /pfad/zu/KickAss.jar
PYTHONPATH=tests:tools:/pfad/zu/py65 python -m unittest test_stage9c3 -v
```

KickAssembler5.25 wird per SHA256 verifiziert, Java und Python3 erforderlich.
Hosttests benötigen py65-1.2.0 und Pillow wie die bestehenden Modelle.
Gebootet wird ausschließlich STAGE9C3.PRG, auf D81 als STAGE9C3:

```basic
LOAD "STAGE9C3",8
RUN
```

HIGHSCORE.PRG ist ein internes Overlay mit Rücksprung in die residenten Gates,
kein zusätzliches eigenständig ladbares Testprogramm. Die unveränderten
Stage9c1/9c2-Referenzdateien werden als explizite Quellen mitgeführt und nicht
pauschal in die Engine gemergt.

## XEMU-Abnahme (noch offen)

- Titel bleibt beim gesamten Laden korrekt; Menü mit32 Animationen/Cycling.
- Initial Level029 einstellen, F3 öffnen, alle vier Seiten per Cursor/Joystick
  prüfen, zurück;029 und Auswahl bleiben erhalten. Wiederholen, F3/Feuer halten.
- F1 startet029, F2-Platzhalter und X-BASIC einschließlich DIRECTORY/RUN testen.
- Game Over nach letztem Leben: vollständige Explosion und Sound, dann Name;
  Namen korrigieren/bestätigen/abbrechen. Bei Bestätigung neue Rangseite prüfen.
- Für alle Grenzfälle eine vorbereitete VYHI-Kopie verwenden: Score über Rang1,
  dazwischen, gleich Rang1, gleich Rang80 und darunter. Gleiche Einträge behalten
  ihre Reihenfolge, neuer gleicher steht jeweils zuerst.
- Geänderte D81 behalten, Emulator neu starten und F3 prüfen. Schreibschutz,
  volle Diskette, fehlende Datei, CRC-/Versionsfehler und BAK/TMP separat testen.
- Level1/4/99/100, zyklische ATTACKs, +/- Navigation, Bonusleben, Sterne,
  Übergangsanimation/Sounds24→22, Schüsse, Explosionen und R-Neustart vergleichen.
- Keine tatsächlichen XEMU-/Hardwaretests werden hier als ausgeführt behauptet.

Die Laufzeitdaten6A00–6AD7 und6F80–6FF8 (Gruppen, Grafikdeskriptoren,
Angriffsdaten) bleiben unverändert. Sie sind trotz Lücken in der Assembler-Codekarte
belegt. Die Gates liegen deshalb nach explizitem Laufzeit-Abgleich in1920–19FF
(ungenutzter Bereich nach den32 Diagnosebytes) und6F00–6F7F. Der Gate-Seed
wird bei jedem RUN vor dem Loader dorthin kopiert. Der bestehende Audiobootstrap
sichert5000–5FFF inklusive des neuen transienten Loaders und restauriert ihn
vor dem erneuten RUN. Keine Änderung der Audio-Core- oder Panning-Adressen.

## Automatisch geprüft und Grenzen des Modells

Die sieben integrierten Tabellentests führen den assemblierten Manager aus:
Startup ohne Anzeige/Schreiben, direkte Game-Over-Namenseingabe, unsigned32-Bit-
Grenzen, Gleichstände an Rang1/80, stabile Alt-Reihenfolge, Save/Reload,
Abbruch/Nichtqualifikation, gehaltenes RETURN, schreibgeschützte/volle Diskette,
unterbrochene Promotion, BAK-Recovery, Seiten/Farben/Rahmen sowie D81/BAM.
Zusätzlich läuft die unveränderte14-Test-Referenzsuite von Stage9c2.

Fünf vollständige Engine-Tests durchlaufen den tatsächlichen Assemblerstart
inklusive aller Datei-Lader und versteckter Erstvalidierung; F3 wiederholt,
alle Seiten, Auswahl/Level029 erhalten, gehaltene Öffnungs-/Exit-Tasten,
Game Over mit Save und Reload, Abbruch/Nichtqualifikation, R ohne Eintragung,
neuer F1-Start, Level1/4/99/100 über mehrere Frames, gestoppte Audiokanäle,
Original-PCM-Erhalt, BASIC-Exit und vollständiger erneuter RUN.
Die Engine-Suite wurde ohne vorgefertigten Boot-Snapshot ausgeführt.

Das sind eingeschränkte CPU/VIC/DMA/KERNAL/DOS-Modelle, keine XEMU-Ausführung.
Das DOS-Modell persistiert logische Dateien und injiziert Fehler, emuliert aber
keine realen Schreibsektoren. Audio-Core und alle Originalsamples sind byteidentisch;
die Tests ersetzen keine Hörprüfung oder Messung realer Audio-Unterläufe unter Last.
Die Gameplay-Testframes sind keine vollständigen100 durchgespielten Levels.
Die oben aufgeführte XEMU-Abnahme einschließlich tatsächlicher Neustartpersistenz,
Originalsounds und langer RRB-/Audio-Last bleibt deshalb erforderlich.

[Ausführungsprotokoll und SHA256](stage9c3_test_results.txt).

## Stage9c3a – Nachbesserungen aus PR86

### Bereinigte Highscore-Ansicht

In der normalen Tabellenansicht werden keine Statusmeldung, IO-/DOS-Zahlen,
Save-Bestätigung oder PAGE/Testzeile mehr gezeichnet. Das gilt auch bei regulär
fehlender VYHI.DAT bzw. nicht vorhandenem TMP: Diese normalen Erststartzustände
sind keine Benutzerfehler. Intern bleiben sämtliche Statuswerte, CRC-Prüfungen,
Recovery- und Schreibschutzregeln unverändert.

Übrig bleiben die Originalüberschrift, zwei Tabellenköpfe, die80 Einträge auf
vier Seiten, die originale Fußzeile und genau ein zusätzlicher Navigationshinweis:
`CURSOR / JOYSTICK LEFT-RIGHT: CHANGE PAGE` (Zeile18, horizontal zentriert).
Überschrift (Zeile3), Navigation (Zeile18) und Originalfußzeile (Zeile21) verwenden
fest den unveränderlichen gelben Palettenindex4 (RGB4 FF0). Der Rahmen behält
Index2 und den Original-Farbzyklus. Die Tabellenzeilen wechseln weiterhin einzeln
zwischen den Indizes3/4/5 für Blau/Gelb/Rot, beide Spalten pro Zeile identisch.
Der VIC-IV-Modus erzwingt wie bisher80 Zeichen pro Zeile/H640; alle Texte liegen
innerhalb der Rahmeninnenfläche X5..74 und außerhalb der Tabellenzeilen7..16.

Bei Namenseingabe bleibt die notwendige Eingabe-/Korrekturanweisung sichtbar.
Tatsächliche Datei-/Recovery-/Schreibfehler zeigen weiterhin ihre Erklärung und
in der Fehleransicht die vorhandenen IO-/DOS-Codes. Die Navigationszeile bleibt
auch dann frei. Name und Cursorfeld erhalten Vorrang vor Diagnosezahlen;
spätestens nach fehlgeschlagener Bestätigung ist der Fehler mit Codes sichtbar.
Es wurden keine Fehlerbehandlung oder Dateibefehle abgeschaltet.

### Game Over und Respawn

GAME OVER bleibt nach vollständiger Explosion sichtbar, die beiden veralteten
Zeilen R–RESTART und X–EXIT werden nicht mehr ausgegeben. Das150-Frame-Fenster,
Originalsound, einmalige Qualifikation, Namenseingabe, Speicherung und Rückweg
ins Startmenü bleiben gleich. Bestehende R-/X-Tastenfunktionen bleiben erhalten.

Die vorhandene BLINK-Zustandsmaschine war bereits deterministisch implementiert:
Beim Respawn setzt c_wait Sichtbarkeit1, Blinktakt25 und Schutzzeit150. c_timers
wechselt nach25/50/75/100/125 Frames sichtbar/unsichtbar; bei150 Frames endet
der Schutz mit Sichtbarkeit1 und ACTIVE. Dieser Timer und die Unverwundbarkeit
wurden bewusst unverändert übernommen. Der tatsächliche RRB-Renderer unterdrückt
den Player-Pixie nur visuell, ohne seine X-/Y-Koordinaten zu verändern.

Die bisherige c_tick-Schussfreigabe ließ ausschließlich ACTIVE zu und setzte
während BLINK den Feuer-Latch immer wieder. Ein gleich großer JSR ersetzt nun
nur die ursprüngliche Zustandsabfrage: c_fire_state erlaubt ACTIVE oder BLINK.
WAIT, Explosion und OVER bleiben gesperrt. Die frei gewordene zweite Game-Over-
Hinweisroutine bietet Platz für diesen kleinen Helper; der gepackte Koordinator
und alle Audio-ABI-/Projektildatenadressen bleiben an ihren bisherigen Stellen.

p_player_fire selbst bleibt byteidentisch: maximal zwei Projektile, bestehender
Feuer-Latch mit Freigabe vor neuem Druck, Geschwindigkeit und3×7-Grafik unverändert.
Der Ursprung wird aus dem aktuellen Player-X+8 und dem konstanten Player-Y
gebildet, unabhängig von c_visible. Keine zusätzlichen oder doppelten Schuss-
und Audioereignisse. Der Player bleibt auch im unsichtbaren Intervall steuerbar;
Kollisionen können während BLINK weiterhin kein Leben abziehen.

### Build und Prüfung von Stage9c3a

```sh
python tools/build_stage9c3a.py --kickass /pfad/zu/KickAss.jar
PYTHONPATH=tests:tools:/pfad/zu/py65 python -m unittest test_stage9c3a test_stage9c3a_engine -v
```

Die Quellen sind separat als stage9c3a angelegt. Der Builder schützt zusätzlich
den vollständigen Stage9c3-Stand daf45af4a95f34e45c84103c55d6fc25d79a0a1d;
Originale Stage9c3-Quellen, Builder und bisheriges Release werden nicht überschrieben.
Das neue vollständige Release liegt im Unterordner stage9c3a des bisherigen
Stage9c3-Releases. Alle Original-DAT-/Sound-/Menüdateien bleiben identisch;
VYHI-v1-Datenformat und sichere Schreibtransaktion ändern sich nicht.

Neue Hostprüfungen kontrollieren feste gelbe Farben trotz laufendem Rahmenzyklus,
leere normale Statuszeilen, echte Fehleranzeige, vollständige Rahmen/Textgrenzen,
GAME OVER ohne weitere RRB-Hinweiszeilen sowie jeden der150 Schutzframes. Sie prüfen
auch tatsächliche RRB-Sichtbarkeit, Bewegung und beide Schüsse während Unsichtbarkeit,
keine Wiederholung bei gehaltenem Feuer, Poollimit und wieder normale Verwundbarkeit.
Die vollständigen bisherigen Übergangs-/Persistenztests werden weiter ausgeführt.

XEMU-Neuabnahme bleibt erforderlich: F3/Paging/Navigation und feste Farben,
Game Over mit und ohne Eintrag, echte D81-Persistenz, blinkender steuer-/schießbarer
Player, zwei Schüsse, unveränderte Sounds, RRB-/Audio-Last und X→BASIC/RUN.
Keine Stable-Markierung oder Merge vor ausdrücklicher Bestätigung.
[Stage9c3a-Prüfprotokoll](stage9c3a_test_results.txt).

Stage9c3a-Prüfergebnis: **16 Hosttests bestanden**, inklusive Kaltstart und erneutem
RUN; alle94 Ausgabedateien zweier Builds byteidentisch. Blinken verändert nur
c_visible und RRB-Einträge, nicht Hardware-Spritefreigabe oder Audio-DMA.
XEMU-Abnahme weiterhin offen.
