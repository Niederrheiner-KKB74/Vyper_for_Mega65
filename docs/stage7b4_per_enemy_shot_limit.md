# Stage 7b4 — zwei aktive Projektile je ursprünglichem Schützen

Testbuild für Issue #59, Branch `stage7b4`, ausdrücklich **nicht Stable**.
Unveränderte getestete Ausgangsbasis: Stage7b3 Commit
`a41e92ab8e4994a0a3288d60d63984d8593c8332`.

## Ursache und gezielte Korrektur

Stage7b3 führt bereits in `shots.p_source_enemy` den ursprünglichen Gegner-Slot
mit. Die Auswahl `selection.fire_eligible` prüfte jedoch nur ENTRY/ATTACK,
Sichtbarkeit und Schussursprung, nicht die Anzahl seiner fliegenden Schüsse.
Ein einzelner Gegner konnte deshalb alle sechs globalen Slots belegen.

Stage7b4 ergänzt `selection.owner_room`: Die sechs aktiven Gegnerprojektile
in Slots 2–7 werden mit dem ursprünglichen Gegnerindex verglichen. Bei zwei
Treffern wird dieser Gegner aus der Schützenliste ausgeschlossen. Andere
geeignete Gegner bleiben auswählbar; ein gesättigter Gegner löst keinen
zusätzlichen Cooldown aus. Die bestehende Suche nach einem freien Slot 2–7
prüft weiterhin die globale Grenze sechs. Player-Slots 0/1 zählen nie mit.
Auch der vorhandene isolierte T-Testpfad prüft dieselbe Grenze.

Nur `stage7b4_selection.asm` und `stage7b4_shots.asm` unterscheiden sich nach
Normalisierung der Stage-Namen funktional von ihren Stage7b3-Vorgängern.
`releases/stage_7b4/base-comparison.json` dokumentiert dies sowie identische
Bytes aller fünf DAT-Dateien, Projektilgrafiken, Menüfont, Menüoverlay,
Color-Cycling-Daten, Titeltiles und Sternlayout.

## Besitz, Freigabe und Wiederverwendung

- `p_active`: acht Bytes `$1F00–$1F07`.
- `p_source_enemy`: acht Bytes `$1F58–$1F5F`; relevante Gegnerbesitzer
  stehen in `$1F5A–$1F5F`. Inhalt: ursprünglicher Level-Gegnerindex 0–21,
  **kein** Grafikkürzel und kein temporärer ATTACK-Listenrang.
- `owner_candidate` / `owner_count`: zwei temporäre Bytes `$1F9A/$1F9B`.
  Jeder Aufruf überschreibt sie. Sie sind keine persistenten Besitzerzähler.
- Prüfroutine innerhalb `$9C00–$9D16`; der RRB-Renderer beginnt unverändert
  erst bei `$9D70`. Der erweiterte Projektilkern endet weiterhin vor `$85B0`.

Der normale Spawn in `attack.a_fire_start` und der T-Spawn speichern bereits
korrekt den Original-Slot. Diese Schreibstellen bleiben unverändert.
ENTRY→FORMATION, ATTACK→RETURN→FORMATION und `game.c_enemy_hit`/Explosion/Tod
schreiben weder Besitzer noch bestehende Schüsse um. Sie fliegen weiter.

`p_update` deaktiviert Offscreen-Projektile über `p_deactivate`;
`game.c_collisions` benutzt denselben Pfad bei Treffern. Sobald `p_active=0`,
zählt der Eintrag nicht mehr. Ein inaktiver Besitzerwert ist belanglos.
Damit entstehen weder negative Zähler noch doppelte Freigaben; wiederholtes
Deaktivieren ist idempotent. Game Over und der Levelübergang löschen ebenfalls
die Active-Bits. Ein Levelstart und R-Neustart rufen `p_init` auf, das sämtliche
120 Bytes einschließlich Besitzerarrays zurücksetzt.

Gegner-Slots werden innerhalb eines Levels nicht neu besetzt: DEAD bleibt
DEAD. Erst die neue Levelinitialisierung erzeugt neue Gegner und setzt davor
die Projektilverwaltung zurück. Deshalb ist keine Generation-ID erforderlich.
Es gibt keinen zweiten asynchronen Spawn zwischen Schützenliste und freiem
Slot; die bestehende Frame-Reihenfolge bleibt erhalten.

## Unveränderte Parameter und Grafik

Angriffstimer 30 Frames, maximal drei ATTACK-Gegner, Schuss-Cooldown sechs
Frames und RNG-Maske 1 (1/2-Chance bei freiem Cooldown) bleiben unverändert.
Ebenso Zielaufnahme, Geschwindigkeiten, Hitboxen, Kurven, Einflug-Timing,
Drift, 100 Levels, Sterne, konzentrischer Übergang, Menü, Paletten und HUD.
Durch die kleinere gültige Schützenliste können einzelne RNG-Auswahlfolgen
abweichen; die Timer und der RNG-Algorithmus selbst wurden nicht verändert.

Die bereits vom Benutzer bestätigten **3×7**-Projektile aus Stage7b3 bleiben
bytegleich: rote Spitze beim Player oben, beim Gegner unten, weißer Schaft
und originale graue Randpixel. Die historische 1×4-Player-Formulierung in
Issue #59 wird durch die ausdrückliche vorherige Benutzerentscheidung und
„Grafiken unverändert“ im aktuellen Auftrag überholt. Die bestehenden
Kollisionsboxen bleiben Player 1×4 und Gegner 3×4.

## Reproduzierbarer Build

Python 3 mit Pillow, Java und unveränderte KickAssembler 5.25 JAR:
SHA256 `9592a39336e73a1db8b4a7749256d62d29b113b1c7f0f6c86ea43870ebd9ae1f`.
Im vollständigen Repository einschließlich Originalassets und Stable-Tags:

```sh
python tools/build_stage7b4.py --kickass /pfad/KickAss.jar
PYTHONPATH=tests:tools:/pfad/zu/py65 python -m unittest test_stage7b4 -v
PYTHONPATH=tests:tools:/pfad/zu/py65 python tools/measure_stage7b4_frequency.py \
  --stage 7b4 --frames 3000 --output releases/stage_7b4/7b4-frequency-measurements.json
python tools/package_stage7b4.py
```

Der Build schützt die vorhandenen früheren Quellen/Assets/Releases direkt
gegen ihre Git-Referenzen; Stage7b3 wird ausdrücklich gegen den getesteten
Commit geprüft. Er konvertiert die Originalgrafiken erneut, prüft Signaturen,
Dateigrößen, Datensummen und sämtliche D81-Dateiketten. Das vollständige D81
enthält `STAGE7B4` und `VYTI.DAT`, `VYMN.DAT`, `VYLV.DAT`, `VYGR.DAT`,
`VYCL.DAT`. PRG 45057 Bytes, D81 819200 Bytes. Separate Builds und Vergleiche
werden in `reproducibility-report.json` dokumentiert.

## Automatische Prüfungen und Grenzen

Die Hosttests führen die tatsächlichen assemblierten Instruktionen mit einem
begrenzten CPU-/DMA-/VIC-Modell aus. Sie ersetzen keine XEMU-Abnahme.
Getestet werden 1/2/3 Schützen, zwei pro Besitzer, insgesamt sechs, Freigaben
bei Offscreen/Kollision, wiederholtes Deaktivieren, fortbestehende Besitzer
über Zustand/Tod, Level-/R-Reset und acht sichtbare Hardware-Spritekanäle.
Die 1/2/3-Schützen-Tests verwenden verschiedene Slots desselben Level-1-
Gegnertyps und unterscheiden damit individuelle IDs von Grafiktypen.
Die bestehenden Tests decken außerdem Titel/Loader/Menü, Schussziele,
Kollision/Explosion/Respawn, alle 100 Levelpaletten, originale Angriffskurven,
Sterne, HUD, Übergang einschließlich 100→1, +/- und BASIC-/RUN-Restaurierung
im Modell ab. **50 Tests bestanden, keine Fehler oder übersprungenen Tests** (628,021 Sekunden).
Exakte Ergebnisse und PRG-Hash: `test-report.json` und
`host-tests.txt` im Release.

Die Frequenzmessungen verwenden 3000 isolierte 50-Hz-Hostticks, Level 1,
Seed `$C3A5`, 22/10/5/2/1 erhaltene Gegner. Keine Kollisionen und kein Renderer;
physische Kurvenläufe erhalten die Population künstlich konstant. Der
Kontrolllauf mit stets verfügbarer Formation isoliert die unveränderte
Angriffsauswahl vom veränderten Schuss-RNG-Verbrauch. Separate 1/2/3-Schützen-
Läufe prüfen die individuellen und globalen Spitzen. Ergebnisse siehe unten.

## XEMU-Abnahme

D81 einlegen, `LOAD"STAGE7B4",8`, `RUN`, Joystick **Port 2**; F1 startet.
Bitte prüfen:

1. 1/2/3 schießende Gegner: maximal zwei noch fliegende Schüsse je ursprünglichem
   Gegner und sechs insgesamt; nach Verschwinden eines Schusses wieder Schüsse.
2. Schüsse bleiben beim Rückflug, Erreichen der Formation und Tod ihres Schützen
   erhalten; übrige Gegner können währenddessen weiter feuern.
3. Bei 22/10/5/2/1 Gegnern weiterhin funktionierende Angriffsauswahl; maximal drei
   ATTACK. Zwei Player-Schüsse zusätzlich zu sechs gegnerischen sichtbar.
4. ENTRY/ATTACK-Schüsse, Grafiken, Ziele/Kollisionen, Explosionen, Respawn,
   Originalpaletten/Color-Cycling und HUD unverändert.
5. Level Clear/konzentrischer Übergang, 100→1, +/−, Game Over/R sowie X→BASIC,
   DIRECTORY und erneutes RUN ohne Ghost-Sprites oder alte Besitzerlimits.

Keine eigene XEMU-Ausführung; Stable erst nach ausdrücklicher Benutzerbestätigung.

## Messwerte (Hostmodell, 3000 Frames = 60 Sekunden)

| Verbleibende Gegner | Kontroll-Angriffe 7b3 / 7b4 | Kurven-Angriffe 7b3 / 7b4 | Schüsse 7b3 / 7b4 | Max. Schüsse je Besitzer 7b4 |
|---:|---:|---:|---:|---:|
| 22 | 99 / 99 | 48 / 48 | 215 / 189 | 2 |
| 10 | 98 / 98 | 48 / 48 | 212 / 186 | 2 |
| 5 | 98 / 98 | 47 / 47 | 180 / 174 | 2 |
| 2 | 100 / 100 | 23 / 23 | 179 / 88 | 2 |
| 1 | 100 / 100 | 12 / 12 | 134 / 46 | 2 |

In beiden Laufarten sind die Angriffszahlen von Stage7b3 und Stage7b4
identisch. Im Kontrolllauf sind außerdem ausgewählte Gegner-IDs und Due-Checks
identisch. Weniger Schüsse bei wenigen Gegnern sind das beabsichtigte
individuelle Limit. Im Originalkurvenlauf steht ein einzelner Gegner lange
in ENTRY/ATTACK/RETURN und ist dann nicht als FORMATION-Angreifer verfügbar;
deshalb ist die absolute Kurvenstartzahl kleiner als im ständig verfügbaren
Kontrolllauf. Der Algorithmus bleibt unverändert; in anderen Läufen können
Schützenlisten dennoch den gemeinsamen RNG-Verbrauch beeinflussen.

| Gleichzeitig schießende Gegner | Schüsse in 3000 Frames | Max. aktive insgesamt | Max. aktive je Besitzer |
|---:|---:|---:|---:|
| 1 | 36 | 2 | 2 |
| 2 | 72 | 4 | 2 |
| 3 | 108 | 6 | 2 |

Beide Versionen wurden neu mit demselben korrigierten Messskript ausgeführt.
Es behandelt 23 Combat-Zustände (einschließlich Sonderobjekt), aber nur die
22 originalen Entry-Koordinatenslots; die alte Messhilfe schrieb versehentlich
einen 23. Entry-Eintrag über benachbarte Koordinaten. Dieser Host-Testfehler
ist korrigiert; die eigentliche Spielengine war davon nicht betroffen.
Die historischen Stage7b3-Messdateien bleiben unverändert. Alle neuen
Messungen verwenden die in der jeweiligen JSON angegebenen PRG-Hashes.
