# Stage 4b-2 – Originalkurven, Angriffe und pendelnde Formation

Issue #16, Testbranch `stage4b-2`, aus `stage4b1-stable`
(`e124112d517ea85bea2216f34614d11a12be7238`). **Stable: vom Benutzer unter XEMU bestätigt; Referenz `stage4b2-stable`.**
Stage 4b-1, seine Quellen, Artefakte und Tags bleiben unverändert.

## Tatsächliche Daten und Rekonstruktionsgrenzen

`tools/analyze_stage4b2_attack.py` parst den vollständigen Levelrecord mit den
vorhandenen Längenprüfungen. Ergebnis in `stage4b2-attack-analysis.json` und
im Build-Report. Level 1 beginnt bei Datei `$0328`, Länge 849 Bytes; Gruppen,
Gegner und Angriffe werden im Laufzeitparser durchlaufen, nicht über feste
Gegnerlistenoffsets adressiert. Der bestehende Loader prüft weiterhin beide
vollständigen DAT-Dateien und lädt sie nach `$40000`/`$54000`.

| Datenbefund | Kurve 0 | Kurve 1 |
|---|---|---|
| Längenwort in VYLV | `$0507` | `$05C0` |
| Beginn Kurvenbytes | `$0509` | `$05C2` |
| Laufzeit in der Levelkopie | `$77E1` | `$789A` |
| Länge | 183 Bytes | 183 Bytes |
| Erste Bytes | `92 92 02 92 92 02` | `12 12 02 12 12 02` |
| Schritt 58, integriertes (X,Y) | (49,102) | (-49,102) |
| Letzter integrierter Punkt | (80,168) | (-80,168) |
| Integrierter Y-Bereich | 2–168 | 2–168 |

Für **jedes** Byte ist die zweite Kurve horizontal gespiegelt: gleiche
Y-Deltas, negierte X-Deltas. Kein Aneinanderhängen. Bit 7/6–4: X-Vorzeichen/
Betrag; Bit 3/2–0: Y-Vorzeichen/Betrag, sign-magnitude. `$92` → (-1,+2),
`$12` → (+1,+2), `$AA` → (-2,-2), `$88` → (0,0), einschließlich negativer Null.
Alle 183 Originalbytes werden einmal gelesen; negative Y-Deltas innerhalb
der Schleife sind Bewegung und **kein** Endmarker.

Die Gegnerrecords enthalten bei Slots 0–10 jeweils Index 0, bei Slots 11–21
jeweils Index 1. Dass dieses Feld vorhanden und in diesem Bereich liegt, ist
belegt. Seine exakte Auswahlsemantik im Original ist **nicht** unabhängig
belegt. Insbesondere die historischen WinUAE-Beispiele (IDs 1, 8, 11 nutzten
Kurve 1) beweisen keine allgemeine 0/1-Zuordnung; die zusätzliche Original-
Bedingung bei `$88`, ID-Konvention und Kurvenwechsel bleiben offen. Der
Originalinterpreter und die WinUAE-Dumps fehlen im Repository.

**Dokumentierte MEGA65-Zuordnung:** Der rohe Recordindex wird direkt als
Variante 0/1 benutzt. Das ist eine reproduzierbare, datengetriebene
Übergangsregel, keine Behauptung einer verifizierten Originalauswahl.

Die historische Analyse beschreibt X relativ zum gespeicherten Angriffsbeginn,
50-Hz-Punkte, einen negativen **expandierten** Y-Endmarker und Rückkehr mit ±1
pro Achse. Die endlichen VYLV-Kurven enthalten keine negative integrierte
Y-Endmarkierung. Eine vollständige Originalrekonstruktion aus diesen Bytes
allein ist deshalb nicht möglich. Die genaue absolute/relative Y-Verankerung
und originale Angriffsauswahl/-wahrscheinlichkeit bleiben ausdrücklich offen.

## Zustandsmaschine und Originalbewegung

Die bestätigte WAIT-/ENTRY-Logik und ihre Sichtbarkeitsfreigabe bleiben erhalten.
Erst nach Abschluss des gesamten Einflugs (ohne Abschüsse Update 353) wird der
neue Controller freigegeben. DEAD/EXPLOSION blockieren diese Aufbau-Barriere
nicht dauerhaft; noch wartende/einfliegende lebende Gegner blockieren sie.

| Spielzustand | `c_es` | `e_phase` | Verhalten |
|---|---|---|---|
| Formation | 1 | 3 | Grundslot plus gemeinsamer Offset |
| Angriff | 3 | 4 | Nächster Originalkurvenpunkt |
| Auslauf unten | 3 | 5 | Kurve fertig; unsichtbarer/auslaufender Angreifer |
| Rückkehr | 2 | 2 | ±1 je Achse zum aktuellen Slot |
| Explosion / tot | 4 / 0 | unverändert | Bewegung/Neu-Auswahl gesperrt |

Beim Start werden X/Y gespeichert und der Kurvenindex auf 0 gesetzt. X ist
relativ zu diesem Start; **Y wird als explizite MEGA65-Regel ebenfalls relativ
integriert**, damit kein sichtbarer Sprung vom Formations-Y zur Kurven-Y=2
entsteht. Es wird ein Originalbyte je Bewegungsupdate verarbeitet. Keine
Ersatzkurve, keine Änderung der Einflugbytes oder des Einflug-Timings.

Beim ersten Erreichen von Y≥200 wird die Darstellung/Kollision des Angreifers
für den restlichen Angriff verriegelt. Weitere Originalpunkte laufen noch ab,
auch wenn sie den Gegner rechnerisch wieder höher führen würden. Das verhindert
sichtbares Wiederauftauchen unten während der noch laufenden Schleife.

**End-/Reentry-Regel für das aufbereitete Format:** Nach 183 Bytes bleibt X
konstant; falls nötig läuft Y mit +2 pro Update bis vollständig unterhalb des
Playfields weiter. Beispielsweise endet der Start bei Y=25 zunächst bei 193:
195,197,199,201 sind die Auslaufpositionen. Bei Y≥200 folgt erst im nächsten
Update der Wechsel auf Y=-16 und RETURN. Beide Übergangspositionen sind
vollständig unsichtbar. Die ersten Rückkehrschritte sind -15,-14,… und werden
vom unveränderten Clipping pixelgenau von oben sichtbar. Es gibt keinen
sichtbaren Sprung bei Y=0. Diese Anpassung ersetzt weder den fehlenden
historischen Sentinel durch eine behauptete Originalregel noch verändert sie
Kurvenbytes; sie ist die notwendige, ausdrücklich vorläufige MEGA65-Randlogik.

RETURN ist kein ATTACK und kann nicht erneut ausgewählt werden. Jede Rückkehr
berechnet das Ziel erneut aus originalem `e_tx` + aktuellem Offset, Y=`e_ty`.
Originaldaten in VYLV bleiben unverändert; nur die eingelesenen Y-Ziele
werden um acht Pixel angepasst. Getroffene Gegner explodieren sieben
Originalframes lang und bleiben DEAD; kein Wiederbeleben durch den Controller.
Score bleibt FORMATION 100, ATTACK/RETURN 175 (Level 1); Rammen und Respawn
verwenden die vorhandene Kampfmechanik.

## Pendeln und Zufallsparameter

Alle Konstanten stehen am Anfang von `stage4b2_attack.asm`:

| Parameter | Vorgabe | Bedeutung |
|---|---|---|
| `a_FORM_STEP_TICKS` | 10 | ein Offset-Schritt pro 10 Gameplay-Updates |
| `a_FORM_Y_SHIFT` | 8 | Originalslot-Y minus eine Bildschirmzeile |
| `a_FORM_MIN/MAX` | -8/+8 | insgesamt 16 Pixel zwischen den Umkehrpunkten |
| `a_INITIAL_INTERVAL` | 100 | erste Startchance nach Aufbau-Barriere |
| `a_START_INTERVAL` | 60 | weitere Angriffsversuche |
| `a_SEED` | `$C3A5` | fester, von Boot/R reproduzierbarer LFSR-Start |
| `a_EXIT_DY` | 2 | dokumentierter Auslauf nach endlichem Record |

Die Grenzen ergeben mit den Originalslot-X 30–195 den Bereich 22–203
(16-Pixel-Pixies vollständig innerhalb X<240, kein HUD-Kontakt). Beginn bei
Offset 0, Richtung +1; exakt 10 spätere Updates ergeben +1, nach 80 +8;
Umkehr ohne zusätzliche Pause oder Drift. Die Geschwindigkeit beträgt bei
50 Hz fünf Pixel pro Sekunde; dies ist die ausdrückliche Benutzervorgabe.
Die Formationsziele werden beim Einlesen zentral um acht Y-Pixel nach oben
verschoben. Einflug und RETURN benutzen beide diese Ziele. Originaldaten,
Startkoordinaten, Kurvenbytes und Startabstände bleiben unverändert; die
höheren Ziele sind vollständig nach Update 353 statt 361 erreicht. Der
Parser lehnt Y unter 8 oder über 184 ab, statt die Subtraktion umbrechen zu lassen.

Der vorhandene 16-Bit-Galois-LFSR wird mit festem Seed initialisiert und weiter
für Schüsse verwendet. Beim Startversuch ein weiterer LFSR-Schritt: untere
5 Bits wählen einen Slot 0–31; 22–31 sowie nicht lebende FORMATION-Slots werden
verworfen. Keine erzwungene Suche nach einem anderen Gegner. Vor jedem Versuch
wird ATTACK gezählt; bei drei ist kein weiterer Start möglich. Unsichtbare
Auslauf-Angreifer zählen dabei mit. RETURN, WAIT, ENTRY, EXPLOSION und DEAD
werden nie ausgewählt. Seed und beide Intervalle sind **MEGA65-Spielregeln**,
keine nachgewiesenen Originalwahrscheinlichkeiten.

Gegnerschüsse nutzen weiterhin ausschließlich globale Hardware-Sprite-Kanäle
2–5 (maximal vier), Spieler 0–1. Nach globalem Cooldown: 1/8-Roll, dann Slotwahl
über die unteren 5 Bits des PRNG-Highbytes. Nur ein lebender, sichtbarer ATTACK
mit geeignetem Schussursprung vor dem Player darf feuern. Diese zusätzliche
Slotwahl kann Startversuche verwerfen; die Schussfrequenz ist entsprechend
geringer als 1/8 aller Frames. Ursprung (X+8,Y+16), Ziel beim Schuss gespeichert
(Player-X+8, Player-Y). Vorhandene 8.8-Richtung, VX-Begrenzung ±2, VY=1,
12-Frame-Cooldown, Bewegung und Sprite-Publisher bleiben erhalten. Kein Homing;
vorhandene Schüsse laufen nach Gegner-Death weiter. Ein gerade explodierter,
unsichtbarer oder zurückkehrender Gegner erzeugt keine neuen Schüsse.

F/N/P-Offscreen-Test, T-Legacytest und D-Diagnose bleiben verfügbar. Während
F ist die Kampfmechanik wie zuvor isoliert; während T pausiert die neue
Auswahl/Pendel-Zeit und der bisherige Testpfad bleibt ausdrücklich ein Test.
Auch dieser Legacy-Angreifer teilt die globale Drei-ATTACK-Grenze; bei drei
aktiven Originalangreifern wird kein vierter Testangreifer gestartet.
GAME OVER pausiert Controller/Schüsse; R setzt Level 1, Offset/Flags/Seed und
Einflug neu auf und erhält den Highscore. X/BASIC-Exit unverändert.

## Korrektur nach dem XEMU-Test

Der Player erreichte nach sieben Explosionsframes korrekt WAIT. `c_wait`
wartet auf DEAD oder FORMATION aller Gegner. Die automatische Angriffssteuerung
startete währenddessen weitere Angriffe: ein Lauf mit drei bestehenden
Angreifern blieb nach 4.000 Updates ohne Respawn (46 neue Starts).
Neue Starts sind jetzt während PLAYER_EXP und WAIT gesperrt, einschließlich
des isolierten T-Testmodus. Bereits fliegende Gegner führen ihre Kurven und
RETURN weiter aus; sobald die Formation wieder vollständig ist, folgt der
unveränderte steuerbare Respawn mit 150 Updates Unverwundbarkeit.

Ein neuer Regressionstest löst eine echte Rammkollision mit aktivem Scheduler
aus, prüft Explosion/Lebensabzug, erzwingt jeden Update eine neue Startchance
und prüft ausbleibende Starts, anschließenden Respawn, horizontale Steuerung
sowie den Übergang zur normalen Verwundbarkeit. Keine Explosions-, Kollisions-,
Schuss- oder Player-Bewegungsroutine wurde geändert.

## Speicher, Build und Basisschutz

Neu `$6F80–$6FFF` (freie 128-Byte-Lücke hinter dem Color-Backup): Indizes,
Startanker, Unsichtbarkeitsflags, Kurvenpointer und Diagnose. Neuer Code nutzt
ausschließlich zuvor nullgefüllte, einzeln gegen die Stable-Referenz geprüfte
Lücken **unter `$A000`**:

| Bereich | Inhalt |
|---|---|
| `$36B0–$36F2` | Auslauf und Reentry |
| `$4B4A–$4BEB` | begrenzter Angriffsparser |
| `$4F00–$4FBC` | Formation und Angriffsauswahl |
| `$7951–$79F1` | Schussinitialisierung; nach Ende der Levelkopie |
| `$895C–$89D3` | Schussauswahl |
| `$9A56–$9AE7` | Angriffsbeginn und Sichtbarkeit |
| `$9F10–$9FE2` | Kurvenbewegung |

Wichtig: `$D030` ROMA/ROMC und C64-Banking können CPU-Reads in `$A000–$CFFF`
auf ROM umleiten, obwohl Stores darunterliegendes RAM treffen. Diese Bereiche
werden deshalb nicht für neuen ausführbaren Code benutzt. Der Test aktiviert
ROMC zusätzlich zur bestehenden SYS-MAPH-Abbildung für Boot, Angriff/Rendern,
R und X; die neuen Controller-/Schussroutinen werden außerdem mit ROMA
ausgeführt. Der vorhandene Renderer bei `$B800` behält dabei wie in der
Stable-Referenz seine RAM-Sichtbarkeit. Kein CPU-Read aus den geprüften
ROM-Overlays tritt auf.
Der Modellvertrag folgt dem XEMU-Memorymapper (`BANK_POLICY_ROM`: Read
`$20000+CPU-Adresse`, Write darunterliegendes RAM). Kein zusätzliches MAP-
Umschalten oder Eingriff in ROM. Renderer bleibt 25 Zeilen/Y=0–199, 24 Slots;
keine neue Renderarchitektur, Grafiken oder DMA-Listen.

Der Builder pinnt Stage-4b-1-PRG-SHA256 und erlaubt nur den Controller, die
vorhandenen Return-/Sichtbarkeitshooks, nachgewiesen freie Codebereiche sowie
exakt verifizierte JSR/JMP-Neuverweise. Loader, Palette, HUD, Projektiltechnik,
Kampf-/Exitcode und Originalassets bleiben außerhalb der gezielten Hooks
byteidentisch. PRG bleibt **43.777 Bytes**, D81 bleibt **819.200 Bytes**.
Exakte Grenzen: Release-`memory-map.txt`.

```sh
python3 tools/analyze_stage4b2_attack.py
python3 tools/build_stage4b2.py --kickass /pfad/KickAss.jar
python3 -m pip install -r tests/requirements-stage3b1.txt
PYTHONPATH=tools:tests MEGA65_ROM=/pfad/MEGA65.ROM \
  python3 -m unittest test_stage4b2
```

Java, Python 3, gepinnter KickAssembler 5.25 und vorhandene Importassets wie
bei Stage 4b-1. Ausgabe `releases/stage_4b_2/`: neun vollständige ASM-Dateien,
PRG, D81, Symbole, Build-/Memory-Report, Mapping und SHA256SUMS. Der Builder
prüft die originalen DAT-Hashes und die vollständigen D81-Dateiketten/Inhalte.
Ein unabhängiger Zweitbuild erzeugt alle 16 Release-Dateien byteidentisch.

## Automatische Prüfung und XEMU-Abnahme

Die Tests führen assemblierten Code im CPU-/DMA-/SYS-MAP-Modell aus. Die
36 übernommenen Regressionen isolieren die neue Automatik durch ein Test-
Fixture-Flag; im ausgelieferten Programm ist sie standardmäßig aktiv. Neue
Tests prüfen den aktiven Aufbau bis Update 353, 10-Frame-Pendeltakt über mehr
als einen Zyklus, alle Punkte beider Angriffskurven, Seed/Wiederholbarkeit,
Drei-Angreifer-Limit, globale Vier-Schuss-Grenze, Zielmomentaufnahme, DEAD- und
unsichtbare Quellen, RETURN zum während des Flugs bewegten Ziel, Original-
Explosionen/Score, Neustart sowie tatsächlich aus RRB-Records gefetchte Pixel
am unteren und oberen Rand. Ein zusätzlicher Hauptschleifentest durchläuft
160 echte Gameplay-Frames mit drei Angreifern und publizierten Sprites; für
die erste Schusschance benutzt er den expliziten gültigen Testseed `$0100`.
Ein Zufallslauf muss nicht innerhalb kurzer Zeit einen Schuss erzeugen.

Finales Ergebnis: **49/49 Tests bestanden**, keine übersprungenen Tests,
511,317 s mit bereitgestelltem ROM V920395. Hauptschleifentest: durchschnittlich
112.575, maximal 117.725 Modellzyklen/Frame; maximal drei aktive Gegnerschüsse
in diesem Szenario (die separate Pool-Prüfung belegt die globale Grenze vier).
Boot/Controller/Render/R/X unter ROMC sowie neue Routinen unter ROMA bestanden.
Alle 16 Release-Dateien sind im unabhängigen Zweitbuild byteidentisch.
Der anschließend ergänzte gezielte Parsertest bestätigt zusätzlich alle
22 Y-Ziele gegen VYLV und die Grenzen 0/7/8/25/184/185/255.

| Artefakt | SHA256 |
|---|---|
| `STAGE4B2.PRG` | `d55a4309aa6d431cb56b812393215a36bc5512d5b7b0d7846a150325183ddb66` |
| `VYPER_STAGE4B2.d81` | `a2cbbc69f4d934ea228e40b3c2ef9f7cc9088ff252344147f0bcaabb16458aea` |

CPU-Zyklen des Modells und DMA-Records sind Regressionsevidenz, keine Messung
der wirklichen Rasterzeit. Raster-/50-Hz-Abnahme muss unter XEMU erfolgen.
Keine unabhängige WinUAE-/Hardware-Abnahme behauptet; Originalreferenzen fehlen.

XEMU: D81 einlegen, ROM V920395/80×25 wie bei Stage 4b-1:

```basic
LOAD "STAGE4B2",8
RUN
```

Den vollständigen Einflug ohne Schießen vergleichen; rechts kein stehender
Vorlauf, um eine Zeile höhere Formation erreicht. Danach das schnellere Pendeln mehrere
Sekunden beobachten (Endpunkte 16 px auseinander), zufällige Angriffe beider
Varianten und Rückkehr oben zu den bewegten Slots prüfen. Nie mehr als drei
ATTACK bzw. vier Gegnerschüsse. HUD/obere Zeilen dürfen nicht flackern;
Randclipping, Explosionen, 100/175 Punkte, Rammen, Leben, drei Sekunden
steuerbare Unverwundbarkeit, GAME OVER/R und X mit erneutem LOAD/RUN testen.

Im XEMU-Monitor: `c_es` ab `$1C00` (22 Einträge), `e_phase` `$1EC6`, signed
X/Y `$1E00/$1E16/$1E2C/$1E42`, Kurvenindex `$1E9A`, rohe Varianten `$6F80`,
Startanker `$6F96/$6FAC`, Bottom-Latches `$6FC2`, bereit `$6FDF`, Offset
`$6FE0` signed, Tick `$6FE2`, Starttimer `$6FE3`, ATTACK-Zähler `$6FE4`,
Schusszahl `$6FE5`, letzte Start-ID `$6FE6`, Ereignis/ID `$6FEA/$6FEB`
(1 Start, 2 unten unsichtbar, 3 Reentry). Zähler werden vor Kollisionen
abgetastet; nach einem Treffer zeigt der direkte `c_es`-Status den aktuellen
Stand. PRNG `$1B49/$1B4A`, Projektilaktivität sechs Bytes ab `$1B00`.

Der Benutzer hat den korrigierten Build als Stable bestätigt. Programmcommit: `5b88b9fa4a78d0340676a32bf9a10493fc73f79f`. Quellen und Release-Dateien sind bei der Stable-Sicherung unverändert.
