# Stage 3b-5c – Vorprüfung zu Issue #8

## Status: Original-Explosionsframes fehlen

Stage 3b-5c ist **noch nicht implementiert, gebaut oder als Stable markiert**.
Es gibt deshalb noch kein Stage-3b-5c-PRG oder D81. Der Entwicklungsbranch
`stage3b-5c` beginnt exakt bei `stage3b5b-stable`, Commit
`e4540557938b342fbf8935cfce787410a3d77512`.
Alle stabilen Quellen, Tags und Release-Dateien bleiben unverändert.

Issue #8 verlangt die acht bereits extrahierten Original-Amiga-Explosionsframes.
Die Vorprüfung vom 10.10.2026 findet diese Dateien weder im GitHub-Branch
`stage3b-5b` noch im lokalen Repository, den verschachtelten Archiven oder
dem ursprünglich bereitgestellten `Vyper_for_Mega65_import_package.zip`.
Issue #8 enthält zum Prüfzeitpunkt keine Kommentare mit weiteren Assets.

### Nachweise

- `assets/vyper_all_enemy_types_exact_ncm.zip`: Das Manifest hat 239 Einträge,
  globale Frames **8 bis 246**. Es enthält **keinen** globalen Frame 0 bis 7.
- `assets/VYGR.DAT`: 36 Typen, 239 Frames, 30.888 Bytes. Jeder Frame stimmt
  bytegenau mit dem entsprechenden `type_NN/anim_NN_ncm.bin` des Gegnerarchivs
  überein. Es gibt keinen zusätzlichen Explosionsblock.
- `assets/STAGE3A_DATA_PREPARATION.zip`: DAT-Dateien, Daten-D81, Builder und
  README; keine separaten Explosionsframes.
- `releases/stage_2ja_stable/Stage_2ja_STABLE_ARCHIVE.zip`: Auch das darin
  verschachtelte Build-Archiv enthält lediglich die Animationen der ersten
  sechs Gegnertypen; keine Explosionsframe-Dateien.
- `assets/player/` enthält das bestätigte einzelne Spielerschiff und seine
  Palette. `docs/player_graphics.md` beschreibt acht vorangehende Explosionen
  im damaligen Amiga-Dump, liefert aber nicht deren Pixeldaten. Der Dump ist
  nicht im Repository vorhanden. Aus der Lage eines Spielerframes wird keine
  unbelegte Explosionsextraktion abgeleitet.

Alte Quellen enthalten `explosion_top_char_lo` / `explosion_bottom_char_lo`
und den Kommentar „Original Vyper explosion frames 0..7“. Diese Tabellen sind
**Glyphreferenzen, keine Grafikdaten**. Ihre alten Adressen `$83C0–$87BF`
enthalten in Stage 3b-4a Nullen und in Stage 3b-5b teilweise neuen Projektilcode.
Die alten Tabellen dürfen deshalb nicht als funktionierende Originalanimation
reaktiviert werden. Ein Gegnertyp mit acht Animationsframes ist ebenfalls kein
Nachweis für acht Explosionsframes.

Benötigt werden die acht Originalframes in bestätigter Reihenfolge mit
Format-/Palettebeschreibung, vorzugsweise 16×16-NCM-Dateien à 128 Bytes
(linkes Pixel im Low-Nibble, Transparenzindex 0). Alternativ ist die vorhandene
Originalextraktion samt Quellmaterial und Formatbeschreibung geeignet.
Keine Ersatzgrafiken, leeren Platzhalter oder erfundenen Daten werden erzeugt.

## Geprüfte Integrationsbasis

- Zwei Spielerschuss-Slots 0–1 und vier Gegnerschuss-Slots 2–5; signed-8.8-
  Geschwindigkeiten, gespeicherte Zielposition und Software-Deaktivierung.
- Ein Spieler, 22 Pfadgegner und ein zusätzlicher Orbitgegner: 24 Pixies
  insgesamt. Neue Kollisionen müssen **alle 23 Gegner** berücksichtigen;
  die alten, ungenutzten 16-Gegner-Zustandsarrays reichen nicht aus.
- Hauptupdate synchronisiert auf Rasterzeile 250; Explosionen und Respawn
  benötigen eigene 50-Hz-Zähler unabhängig vom Animations-Pause-/Speed-Regler.
- Testangriff des bestehenden Gegners Nr. 19: 96/128 Ticks, T schaltet um.
  Ein echter Gegnerstatus muss künftig Bewegung, Feuer, Treffer und
  WAIT_FORMATION gemeinsam steuern; Originalkurven werden nicht erfunden.
- Mapping VYLV 14 → VYGR-Typ 15 mit sechs Frames bleibt erhalten.
- HUD verwendet siebenstellige Scoreanzeigen, drei Startleben und inaktiven
  Spieler 2. Der neue Attack-Grundwert muss 175 statt des alten Mockwerts 115
  sein. Highscore muss beim Neustart gesondert erhalten bleiben.
- BASIC-Exit sichert zusätzliche Sprite-/VIC-IV-Register und den kompletten
  verwendeten Color-RAM-Bereich. Neustart darf die ursprünglichen
  Registersicherungen und `hud_saved_scale` nicht mit Spielmoduswerten ersetzen.

## Speicherprüfung und vorgesehenes Vorgehen

Die bestehenden Belegungen in `docs/memory_map.md` bleiben gültig.
`$1C00–$1EFF` ist innerhalb des reservierten Engine-Arbeitsbereichs noch frei
und für separate Gegner-/Spielerzustände prüfbar. KERNAL-RAM `$1000–$15FF`,
SEQ-/DMA-Puffer `$6800/$6900`, Levelkopie `$7600–$7950`, Spritepointer `$8900`,
Grafik-Mapping und die geladenen DAT-Dateien dürfen nicht überschrieben werden.

Für unabhängige Explosionen bieten sich acht unveränderliche Frame-Glyphsätze
an, jeweils mit eigenem transparenten Vor-/Nachlaufglyph. Sie ersetzen im
bestehenden RRB-Renderer nur die Grafikreferenz des betroffenen Objekts;
Position und Framezustand werden je Objekt gespeichert. `$C100–$C7FF` und
ein zusätzlicher freier 256-Byte-Bereich unter `$9000` sind Kandidaten für
die insgesamt 2.048 Bytes. Dies ist **noch keine implementierte Belegung**;
die endgültigen Grenzen müssen der neue Builder und Assembly-Guards prüfen.

Die neuen Routinen sollen über gezielte Aufruf-Hooks in einer separaten Kopie
der Stage-3b-5b-Quellen integriert werden. Keine aktuelle Änderung an Loader,
RRB-Layout, Pixiepfaden, Grafikzuordnung oder Exit.

## Automatisch geprüfte stabile Basis

Reproduzierbarer Build in ein separates temporäres Verzeichnis:

```sh
python tools/build_stage3b5b.py \
  --kickass /pfad/zu/KickAss.jar --output /tmp/stage3b5c-baseline-build
python -m unittest discover -s tests -p test_stage3b5b.py -v
```

KickAssembler 5.25 ist per SHA-256 festgelegt. Der Build prüft Original-DAT-
Hashes, erlaubte Engineänderungen sowie D81-Dateiketten und BAM. PRG und D81
des neuen Baseline-Builds stimmen bytegenau mit dem stabilen Release überein:

| Datei | SHA-256 |
| --- | --- |
| `STAGE3B5B.PRG` | `e0ff91a9ce13a737f4e389af830b9d41beb9adbf2a8c5b3fc1a53f5b59d03a53` |
| `VYPER_STAGE3B5B.d81` | `d999d58f773719c9df8a8024ab17c6c48d721abf173ea5e4b68ff8722839dcb4` |

Ergebnis: **9/9 bestehende CPU-/DMA-/Sprite-/RRB-Hosttests bestanden**
(42,292 Sekunden). Diese Tests sind **keine** neuen Stage-3b-5c-Tests und kein
vollständiger XEMU-Lauf. Die bisherige Stage-3b-5b-XEMU-Abnahme stammt vom Benutzer.

Die Stage-3b-5c-Abnahmekriterien aus Issue #8 bleiben vollständig offen:
Kollisionen, unabhängige Originalexplosionen, Score/Highscore, Leben,
WAIT_FORMATION, 150-Tick-Respawn, GAME OVER, wiederholter Neustart und Exit.
Eine Stable-Markierung erfolgt erst nach ausdrücklicher Benutzerbestätigung.
