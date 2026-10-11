# Stage 4b-3 – Drift, ENTRY-Schüsse und Formationsoberkante

Issue #18; Branch `stage4b-3`, Basis `stage4b2-stable` (Dokumentationscommit
`fd7d9fe`, unveränderter bestätigter Programmcommit
`5b88b9fa4a78d0340676a32bf9a10493fc73f79f`). **Stable: vom Benutzer unter XEMU bestätigt; Referenz `stage4b3-stable`.**

Die separate Untersuchung der Level-Deskriptoren verändert diese Stage nicht.
Kurvenwahl und dokumentierte Übergangsregeln bleiben wie in
[Stage 4b-2](stage4b2_attack_formation.md). Keine Ersatzkurven oder neuen Assets.

## Drei gezielte Änderungen

| Parameter | Stage 4b-2 Stable | Stage 4b-3 |
|---|---|---|
| X-Drift | −8..+8, 1 Pixel/10 Updates | −8..+8, 1 Pixel/5 Updates |
| gemeinsamer Y-Offset | −8 | −25 |
| Schussquellen im normalen Spiel | ATTACK nach Aufbau-Barriere | sichtbare echte ENTRY oder ATTACK |

Bei 50 Hz: 10 px/s, erster Umkehrpunkt +8 nach 40 Updates, ganzer Zyklus
160 Updates. Die Drift startet weiterhin erst nach dem kompletten Einflug;
ENTRY und ATTACK erhalten keinen zusätzlichen X-Offset. RETURN berechnet
bei jedem Update das aktuelle individuelle Ziel. Initialisierung und R
setzen Offset, Richtung, Timer, Seed und Schusszustände reproduzierbar zurück.

### Zentrale Y-Transformation

Originale Level-1-Top-Left-Y: 25..99, Minimum 25. Deshalb
`target_y = original_y - 25`, Zielbereich 0..74. Gegenüber Stage 4b-2 sind alle
Ziele weitere 17 Pixel höher. `a_FORM_Y_SHIFT=25` wird vom Build gegen den
vollständig geparsten Original-Levelrecord geprüft; der Parser transformiert
jeden Zielwert genau einmal. VYLV bleibt byteidentisch. `e_ty` enthält den
bereits transformierten Wert für ENTRY→FORMATION und ATTACK→RETURN→FORMATION.
Die relativen X/Y-Abstände bleiben erhalten. Unterlauf/ungültige Y-Werte werden
vor der Subtraktion verworfen.

**Sichtbarer Pixelrand und Transparenz:** Typ 15 hat sechs Originalframes.
Deren erste opake Zeilen sind 0,1,2,2,2,1. Top-Left der höchsten Slots ist
exakt Y=0; im ersten Frame liegt auch der tatsächlich sichtbare Pixelrand
bei Y=0. In anderen Frames liegt er wegen Originaltransparenz bei Y=1 oder 2.
Eine statische Transformation kann nicht alle Animationsframes gleichzeitig
auf eine opake Zeile Y=0 zwingen. Individuelle Frameverschiebungen würden die
Originalanimation bzw. Slotabstände verändern und werden nicht angewendet.
Der Rendering-Test prüft die tatsächlich aus RRB-Records gefetchten Pixel aller
sechs Frames, zusätzlich zur unabhängigen Prüfung aller Originalslot-Abstände.

### Einflug und Angriffsendpositionen

Gruppenstarts in beiden Gruppen weiterhin bei Updates 1,17,33,49,65,81,97,113,
129,145,161; linker erster sichtbarer Bewegungstick 2, rechts bleibt die
bestehende Null-Delta-/WAIT-Sichtbarkeitssperre erhalten. Originalstartpunkte,
158/165 Einflugbytes, Punktfrequenz und 16-Update-Abstände bleiben unverändert.
Wegen höherer Ziele liegt die vollständige Formation ohne Abschüsse bei
Update 336 (Stage 4b-2: 353); die Anschlussbewegung bleibt kontinuierlich ±1.

Beide Angriffskurven enthalten weiterhin genau 183 Delta-Bytes, Enddelta
X=−80/+80 und Y=+168. Mit neuen Ankern liegen ihre möglichen End-Y zwischen
168 und 242. Die höchsten Slots erreichen durch die Originalkurve allein
also nicht den unteren Rand. Der **bestehende** endliche Auslauf mit X konstant
und Y+=2 ergänzt dort bis zu 16 Updates, bis Y≥200 erreicht ist. Kein Byte wird
übersprungen, gestreckt oder erfunden. Nach der unsichtbaren unteren Phase
folgt Reentry bei Y=−16 und kontinuierliche Rückkehr zum driftenden Ziel.
Die unverifizierte historische Endmarker-/Variantenauswahl bleibt separat offen.

### ENTRY-Schussregeln

Normaler Kandidat ist ein lebender ATTACK (`c_es=3`) oder echte ENTRY
(`c_es=2`, `e_phase=1`). RETURN (`c_es=2`, `e_phase=2`) schießt nicht.
`entry.e_is_visible` ist dieselbe Freigabe wie für Renderer/Kollisionen:
WAIT_ENTRY, stehender Starttick/rechte Null-Deltas, DEAD/EXPLOSION und unten
verriegelte Angreifer werden ausgeschlossen. Die frühere `a_ready`-Sperre
betrifft Schüsse nicht mehr; Drift/Angriffsauswahl behalten ihre Aufbau-Barriere.

Ursprung ist unverändert `(signed_x+8, signed_y+16)`. Sichere Freigabe:
Mündung X=0..237 (dreipixelbreites Projektil komplett innerhalb X<240),
Mündung Y=16..183 (oberhalb des Players Y=184 und innerhalb Y<200).
Damit sind Quellkoordinaten X=−8..229 und Y=0..167 zulässig. Seitlich teilweise
sichtbare Gegner können schießen; oben angeschnittene warten bis Y≥0, um
auch transparente, noch unsichtbare Unterkanten nicht als Quelle freizugeben.
Unten/offscreen oder mit Mündung außerhalb liegende Pixies schießen nicht.
16-Bit-Vorzeichen und Überträge werden vor der Freigabe geprüft; kein Wraparound.

Unverändert: 1/8-Roll, Kandidat 0..31 mit Verwerfen ungeeigneter Slots,
12-Update-Cooldown, global nur Sprite-Slots 2..5. ENTRY und ATTACK teilen
also **vier**, nicht vier pro Quelle. Playerziel wird beim Abschuss gespeichert;
vorhandene 8.8-Geschwindigkeit bleibt danach fest, kein Homing. Testmodus T
bleibt isoliert. Kampf, Explosionen, Punkte, Leben, Respawn und Exit unverändert.

## Speicher und Basisschutz

Keine neuen RAM-Puffer, DMA-Listen oder Renderer-Architektur. Einziger vergrößerter
Codeblock: Schussauswahl `$895C–$89F0`, weiterhin vor den Grafiken `$8A00`.
Sonst identische Speicherbelegung zu Stage 4b-2. RRB: 25 Zeilen, Y=0..199,
24 Slots pro Zeile, Playfield X<240, HUD geschützt. PRG bleibt 43.777 Bytes.

Builder vergleicht gegen gepinnte Stage-4b-2-PRG-Prüfsumme
`d55a4309aa6d431cb56b812393215a36bc5512d5b7b0d7846a150325183ddb66`.
Nur beide Timerinitialisierungen, Y-Konstanten, begrenzter Schussauswahlblock
und ggf. Stage-Titel dürfen abweichen; aktuell 137 geänderte PRG-Bytes.
Loader, Originalkurven, Renderer, Kollisions-/Respawn-/Exitcode, Palette,
Schussrichtung/-publisher und sämtliche bisherigen Stable-Releases bleiben
byteidentisch. Neuer Code liegt weiter unter `$A000`, keine ROMA/ROMC-Overlays.

## Reproduzierbarer Build und Tests

```sh
python tools/build_stage4b3.py --kickass /pfad/zu/KickAss.jar
python tools/analyze_stage4b3_attack.py
PYTHONPATH=/pfad/zu/py65:tests:tools MEGA65_ROM=/pfad/zu/MEGA65.ROM \
  python -m unittest test_stage4b3
```

KickAssembler 5.25 mit bestehender gepinnter Prüfsumme, Java, Python 3 und
py65 1.2.0 für den bestehenden CPU-/DMA-Testadapter. Keine neuen Abhängigkeiten.
Release `releases/stage_4b_3/`: neun ASM-Dateien, PRG, vollständiges 819.200-Byte-D81
mit STAGE4B3/VYLV.DAT/VYGR.DAT, Symbole, Mapping, Build-/Speicherbericht und
SHA256SUMS. Alle 16 Dateien im unabhängigen Zweitbuild byteidentisch.

**52 unterschiedliche automatische Checks abschließend bestanden**, keine
ungeklärten Fehler. Protokoll: [stage4b3-test-results.json](stage4b3-test-results.json).
Der Gesamtlauf führte 51 Tests in 521,079 s aus: 49 bestanden, zwei übernommene
Testannahmen waren nach der beabsichtigten Parameteränderung veraltet:
RETURN-Auswertung behandelte −8 als unsigned248; Spitzenbelegung wurde noch
als >8 statt der neuen Zeilenbelegung exakt8 erwartet. Beide Test-Fixtures
wurden korrigiert und gezielt wiederholt (8,211 bzw.13,303 s), beide bestanden.
Die unveränderten anderen Tests wurden deshalb nicht erneut breit ausgeführt.
Ein zusätzlicher echter Hauptschleifen-ENTRY-Test bestand (18,233 s): erster
Schuss bei Update179 aus Slot14, echte ENTRY-Phase1, Sichtbarkeit1,
Aufbau-Barriere noch0; Zielmomentaufnahme (120,184). Insgesamt sind damit
alle 52 verschiedenen Tests der endgültigen Datei geprüft; ein erneuter
Gesamtlauf der endgültigen 52-Test-Datei wird nicht behauptet.

Hauptschleifenmodell Ø116.340/max.121.548 Zyklen/Frame, maximal drei aktive
Gegnerschüsse im gemessenen Szenario; die eigene Pool-Prüfung belegt die globale
Grenze vier. Loader/DAT-Verifikation, sechs Originalframes, signed/teilweise
sichtbare Quellen, WAIT-Sperre, fixe Zielposition, sämtliche Einflugpunkte und
Starts, Pendelzyklus, Kurven-/RETURN-Geometrie, Clipping und tatsächlich gefetchte
RRB-Pixel, HUD, Treffer/Score/Explosion/Leben/Respawn, R, X und zweiter Start sowie
ROMA/ROMC/SYS-MAP-Sicherheit sind geprüft.
CPU-/DMA-Modell ist keine Messung der Rasterzeit und keine XEMU-Abnahme.

## XEMU-Abnahme und Referenzcheckliste

Der Benutzer hat den Build `a8766f8df9fcea8279181a5d13b772db15ecc954` als stabil bestätigt: er läuft
stabil und verhält sich genau wie vorgesehen. Die folgende Tabelle bleibt eine
Referenzcheckliste; separate Raster-/Frame-Einzelmesswerte wurden nicht geliefert.
Ein unabhängiger Hardwaretest wird nicht behauptet.

ROM V920395, BASIC 80×25, D81 einlegen:

```basic
LOAD "STAGE4B3",8
RUN
```

| Prüfung | Erwartung | XEMU-Ergebnis |
|---|---|---|
| Loader | Originaldaten geladen/verifiziert, Typ 15/sechs Frames | offen |
| Einflug | Starts wie oben, kein sichtbares WAIT/stehender rechter Vorlauf | offen |
| Formation | Top-Left Y=0, opake Framekanten 0/1/2/2/2/1, Abstände unverändert | offen |
| Drift | Schritt jede 5 Frames, +8 bei 40, Zyklus 160, keine HUD-Berührung | offen |
| ENTRY-Schüsse | vor Formationsabschluss; unsichtbares WAIT nie Quelle | offen |
| Schusspool | ENTRY/ATTACK zusammen max.4, Ziel nach Abschuss unverändert | offen |
| Angriffe | komplette Kurven, End-Y168..242, ggf. bis16 Auslaufupdates | offen |
| Rückkehr | von oben ins aktuell driftende Ziel, kein Teleport | offen |
| Kampf | Treffer/Score/Leben, sieben Explosionsframes, steuerbarer Respawn | offen |
| Ende | GAME OVER nach Explosion, R behält Highscore, X/BASIC, erneut RUN | offen |
| Clipping | Y=0..199, keine Spuren/Wraps/HUD-Flackern | offen |

Diagnoseadressen unverändert: X-Offset `$6FE0` signed, Drift-Timer `$6FE2`,
Schusszahl `$6FE5`, `c_es` `$1C00`, `e_phase` `$1EC6`, gemeinsame Freigaben
`$1D64`, transformierte Y-Ziele `$1E6E`, signed Live-Y `$1E2C/$1E42`,
Kurvencursor `$1E9A`, Projektilaktivität `$1B00` (Gegnerslots2..5).
Kein unabhängiger Hardwaretest. Stable-Freigabe durch den Benutzer liegt vor.

## Bereitstellung

GitHub-Push der Stable-Referenz und des neuen Branchs wurde von der automatischen
Freigabeprüfung wegen eines Nutzungslimits blockiert; die Aktion wurde nicht
ausgeführt und nicht als unsicher bewertet. Remote-Veröffentlichung/PR stehen
daher aus. Lokale Quellen und Release sind vollständig; `stage4b3-stable` ist lokal gesichert.

Stable-Sicherung: bestätigter Programmcommit `a8766f8df9fcea8279181a5d13b772db15ecc954`.
Quellen und alle 16 Release-Dateien bleiben byteidentisch zum getesteten Build;
Buildberichte enthalten bewusst ihren ursprünglichen Status vor der Abnahme.
