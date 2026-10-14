# Stage7b5b – Player und originale Gegnerprojektilbewegung (Issue65)

Teststand, **nicht Stable**. Basis ist der vom Benutzer erfolgreich in XEMU
getestete Stage7b5a-Commit `2954dc57418f3898b8f958a9d15d79a57b2dd6bb`.
Branch `stage7b5b`; alle früheren Quellen, Releases und Tags bleiben unverändert.

## Player: bewiesen ist der Schritt, offen bleibt die Originalfrequenz

`tools/analysis/analyze_stage7b5b_motion.py` prüft SHA-256 der drei Originaldateien,
extrahiert `/Vyper/Shot` aus der OFS-Diskette, verarbeitet HUNK_RELOC32 und vergleicht
jeden ausgewählten Bytebereich mit **beiden** gespeicherten Laufzeitkopien.
Die vollständigen Adressen, Offsets, Instruktionsbytes und Disassemblierungen stehen
in [den Belegen](stage7b5b_motion_evidence/68000-excerpts.txt) und
[der maschinenlesbaren Evidenz](stage7b5b_motion_evidence/evidence.json).
Kein vollständiger Gleichheitsnachweis des gesamten CODE-Hunks: außerhalb der
geprüften Bereiche bestehen bereits bekannte Unterschiede.

Die Referenzadressen gehören zum gelieferten Menü-Savestate:
CODE `$C08760`, DATA `$18140`, A4 `$2013E`. Im ChipRAM-Dump liegt CODE bei `$21B20`.
CODE-Offset = USS-Adresse minus `$C08760`; Shot-Dateioffset = CODE-Offset plus `$28`.

| Befund | USS-Adresse / CODE-Offset | Beleg |
|---|---|---|
| Player-Bewegung | `$C0D728` / `$4FC8` | `0839000100dff00d`: rechts JOY1DAT low byte bit1; links `$C0D748`: high byte bit1 |
| Rechte Grenze | `$C0D738` / `$4FD8` | `b07c00e2`: X mit226 vergleichen |
| Rechts-Schritt | `$C0D73E` / `$4FDE` | `5440`: ADDQ.W #2,D0; direkt nach `(A0)` und `$16(A0)` speichern |
| Links-Schritt | `$C0D75A` / `$4FFA` | `5540`: SUBQ.W #2,D0; Grenze0 |
| Startposition | `$C0B5D0` / `$2E70` | Beide angehängten Player-Spritehälften X120,Y184 |
| Sprite-Publisher | `$C0D56E` / `$4E0E` | X+128, niederwertiges Bit in CTL erhalten, Rest nach HPOS |
| Alternative Aufrufpfade | `$C09726`, `$C0974C` | Zwei direkte JSR in **alternativen** Schleifenzweigen, nicht zwei Aufrufe nacheinander |
| Updatezähler | `$C0D090` | WORD-Zähler für die Parität der Streuung |

Die X-Koordinate ist ein direktes WORD. Es gibt in dieser Routine **keinen
Fixpunktanteil, keine Beschleunigung und keinen Bewegungsteiler**. Das erhaltene
HPOS-LSB belegt: eine X-Einheit ist ein Amiga-Lowres-Pixel, kein Halbpixel.
Der Original-Player besteht aus angehängten Hardware-Sprites, nicht einem anderen
Maßstab eines BOB. Rechts hat im Original Vorrang, wenn beide Bits aktiv sind;
die Portierung behält die bisherige Verarbeitung links, dann rechts bei.

**Nicht bewiesen: tatsächliche Aufrufe pro PAL-Frame bzw. Pixel pro Sekunde.**
Die Rasterabfrage `$C09454` liest nur ein Byte von VHPOSR und akzeptiert damit PAL-Zeile0
und256. Die Schleife springt bei `$C09934` zurück. Unmittelbar vorher wird bei
`$C0944E` die A4-relative Bibliotheksfunktion über DATA+$5A aufgerufen. Der gespeicherte
Stub springt nach `$C119E8`; dort wird mit LVO−222 aufgerufen (graphics LoadView,
kein WaitTOF mit LVO−270). Daraus lässt sich keine gesicherte 50-Hz-Sperre ableiten.
Der vorliegende USS ist ein Menü-Snapshot; ein aktiver Gameplay-/Rastertrace fehlt.
WinUAE/FS-UAE ist in dieser Umgebung nicht verfügbar. Für einen endgültigen Nachweis
sind über mehrere PAL-Frames Eintritte in `$C0D728` mit Frame/Raster und X zu protokollieren,
beide Gameplay-Zweige getrennt. Statische Opcodezählung ersetzt diese Messung nicht.

Deshalb gilt ausdrücklich ein **Testparameter**:
`PLAYER_X_STEP=2` in `src/engine/stage7b5b.asm`, einstellbar1..224.
Die MEGA65-Engine ruft die Bewegung einmal je eigenem 50-Hz-Spielupdate auf:
2 Pixel/Frame =100 Pixel/s bei50Hz. Dies übernimmt den belegten Originalschritt,
**nicht eine vermeintlich bewiesene Originalgeschwindigkeit**. Vorher1 Pixel/Frame.
Y184, Start-X112, Grenzen0..224 bleiben passend zum240-Pixel-Playfield erhalten;
die abweichenden Originalwerte X120/226 werden nicht blind übertragen.
Schüsse, Kollisionen und Respawn verwenden weiterhin denselben Player-Record;
auch während der dreisekündigen Unverwundbarkeit bleibt Bewegung erlaubt.

## Projektil: native Rechenreihenfolge und Portierungskoordinaten

Original-Spawn `$C0D612–$C0D6D5`, Update `$C0D5C8–$C0D611`.
Die früheren PR62-Belege bleiben unverändert und sind die technische Grundlage.
Original-`Level+$6C` liefert DY1/2/3; VYSH.DAT enthält diese Werte bereits vollständig.
Keine neue Datei und keine Änderung der Original-Levelparameter.

1. Erst einen freien der sechs Slots suchen. Bei vollem Pool verfällt das Ereignis;
   **keine** Zufallszahl verbrauchen und kein späterer Versuch.
2. Originaler Schuss-Linksrand `(enemyX+7,enemyY−7)`.
3. Ziel-X = Player-X ± random(20), bei ungeradem Updatezähler plus,
   bei geradem minus. Ziel und Geschwindigkeit danach nicht mehr ändern.
4. `deltaY=playerY−shotY`, `deltaX=targetX−shotX`.
5. Falls `deltaY<=0` oder `abs(deltaX)>=deltaY`: `step=DY<<16`.
   Sonst `step=floor(abs(deltaX)*65536/deltaY)*DY`.
   **Erst dividieren/abrunden, dann multiplizieren**, wie DIVU/MULU des Originals.
6. Pro Update zuerst Y+=DY. Bei Y>=200 deaktivieren und X nicht mehr ändern.
   Sonst `sum=fraction+step`, `fraction=sum&65535`,
   `X+=sign(deltaX)*(sum>>16)`. Kein X-bedingtes Löschen und keine Schützenbindung.

Die Portierung verwendet die bereits projizierten sichtbaren Gegnerkoordinaten
(ENTRY Original-Y−16, Formation/ATTACK mit bestehendem Level-Y-Shift).
Daher entsteht der Schuss bei **sichtbarem Gegner-Y−7** und zielt auf den sichtbaren
Player-Y184. Ein Mischen aus rohem Amiga-Y und projiziertem Player-Y wäre falsch.
Der Engine-Projektilrecord enthält den **Mittelpunkt**, das Original den linken Rand.
Deshalb wird in X sowohl Ursprung als auch Ziel um1 verschoben:
Engine-Mitte enemyX+8, Ziel PlayerX±Streuung+1. Dadurch bleibt deltaX exakt gleich.
Der bestätigte Sprite-Publisher mit seinem bisherigen nativen Pixelphasenversatz
bleibt unverändert. Die Grafiken bleiben bytegleich:3×7, Enemy rote Spitze unten,
Player rote Spitze oben gemäß ausdrücklicher Benutzerentscheidung; Trefferboxen
weiterhin Player1×4, Enemy3×4. Keine Vergrößerung der Trefferbox aufgrund der Grafik.

Die bisherige `fireevents.origin_ok`-Zulassung bleibt **bytegleich**, einschließlich
ihrer alten Sichtbarkeits-/Mündungsgrenzen. Eventzeitpunkte und zulässige Schützen
ändern sich damit nicht; nur Ursprung und Bewegung eines zugelassenen Schusses.
Die neue Streuung nutzt einen eigenen16-Bit-Galois-LFSR, Start `$7B5B`, eine Fortschaltung
pro tatsächlichem Spawn, danach Modulo20. Wertebereich und Paritätsregel stimmen;
**die Zufallsfolge ist nicht identisch** mit `(seed+VHPOSR)&$FFFF` des Amiga.
Schussplanung und Angriffsauswahl behalten ihre eigenen unveränderten RNG-Zustände.
Die Projektilwerte gelten je Engine-Update; die offene native Updatefrequenz
betrifft auch den Vergleich ihrer realen Geschwindigkeit in Pixel/s.

## Speicher, Clipping und Budget

Keine Erweiterung der DAT-/ChipRAM-Allokation. Insbesondere bleibt VYSH in physischem
RAM `$B000–$B45B`; `$60000–$FFFFF` wird weiterhin nicht als RAM behandelt.
Neue signed-WORD-Highbytes für X/Y/Ziel und Richtungsbytes liegen bei `$1F9A–$1FB9`,
eigener RNG und Rechenscratch bei `$1FBA–$1FC4`. Initialisierung bei jedem Levelstart,
F1 und R. `$1FC5–$1FCC` hält je Slot das Bewegungsformat, damit bereits fliegende
Schüsse auch beim Umschalten des historischen T-Demos ihren Pfad behalten.
Das T-Demo bleibt separat bei seiner bisherigen8.8-Berechnung. Die vorhandenen Enemy-8.8-Felder werden als16.16-Werte verwendet:
`p_yfrac` niedriges und `p_xfrac` hohes Akkumulatorbyte;
`p_vyfrac` niedriges und `p_vxfrac` hohes Geschwindigkeitsbruchbyte;
`p_vx` ganzzahliger Betrag, separates Richtungsbyte. Player-Slots0/1 behalten
ihre bisherige Bewegung. Slots2..7 bleiben Gegnern vorbehalten.

Zusatzcode liegt ausschließlich in zuvor freien Lücken unter `$A000`:
`$2F50`, `$3558`, `$3768`, `$4FB2`, `$76B5`, `$788A`, `$85FC`, `$9CEE`. Der freigewordene Bereich `$7954`
unter dem ersetzten Schussstart enthält den unveränderten historischen T-Updatepfad.
Jede Lücke hat eine Assembly-Obergrenze; die erzeugte `memory-map.txt` nennt die
exakten Endadressen. Keine neuen DMA-Listen, keine neuen Sprites, keine IRQs,
keine KERNAL-Aufrufe im Bewegungsupdate. Es bleiben zwei Player- und sechs
Gegnersprites; der Titel-/Loader-/RRB-Pfad bleibt erhalten.

Ein seitlich weggeflogenes Projektil bleibt gemäß Original bis Y200 aktiv und
belegt weiterhin seinen Poolplatz. Signed-WORD-Koordinaten verhindern Lowbyte-
Wraparound. Vor Sprite-Publishing und Gegnerprojektil-Kollisionen werden
X-Mitte1..238 und Y0..199 geprüft; außerhalb bleiben Sprite und Hitbox verborgen.
Das ist bewusst ganzes Sprite-Culling an oberer/seitlicher Grenze, kein neues
subpixelgenaues Sprite-Maskieren. Negative Y können beim Spawn vorkommen; der
Schuss wird erst ab Y0 publiziert. Der bestehende sichtbare Rand-/Bottom-Clip bleibt.
Ein unsichtbarer seitlicher Schuss darf nicht durch Lowbyte-Wrap im HUD auftauchen
oder den Player treffen. Untere Lebensdauer endet nun originalgetreu bei200 statt197.

## Reproduktion

```sh
PYTHONPATH=tools/analysis:/path/to/capstone-5.0.7 \
  python tools/analysis/analyze_stage7b5b_motion.py
python tools/build_stage7b5b.py --kickass /path/to/KickAss.jar
PYTHONPATH=tests:tools:/path/to/test-deps \
  python -m unittest test_stage7b5b -v
python tools/package_stage7b5b.py
```

KickAssembler5.25 wird per SHA-256 geprüft. Die unveränderten Baselines werden
gegen ihre Git-Commits geprüft; alle sechs DAT-Dateien werden byteweise mit
Stage7b5a verglichen. Diskettenprüfung liest Dateiketten/Directory/Dateigrößen
und vergleicht alle sieben Dateien. Start in XEMU: D81 einlegen,
`LOAD"STAGE7B5B",8`, `RUN`; Joystick **Port2**, F1 startet das Spiel.

## Automatische Prüfungen und XEMU-Abnahme

**14 Hosttests bestanden**, Laufzeit202,420s; Protokoll `releases/stage_7b5b/test-results.txt`. Der Host führt tatsächliche
assemblierte45GS02-Instruktionen mit begrenzten CPU/DMA/VIC-/KERNAL-Modellen aus.
Das ist keine vollständige XEMU- oder Hardwareemulation und kein Nachweis des
Rasterzeitbudgets. CPU-Aufwand wird zusätzlich als ausgeführte Hostmodell-
Instruktionen dokumentiert; DMA-/VIC-Bus-Arbitration ist dabei nicht gemessen.

Unter XEMU noch zu prüfen: Player-Geschwindigkeit mit Amiga vergleichen, Bewegung
bis beide Ränder, Spawn/Kollision/Respawn und Steuerung während Unverwundbarkeit;
Projektile bei DY1/2/3 in Level1/3/29/54/100, Streuung, volle sechs Slots, Randflug;
Einflug/Angriff/Return, unveränderte Angriffshäufigkeit; Level Clear und Übergang,
100→1, +/- und F1-Levelwahl, Game Over/R, X zu BASIC und erneutes RUN;
Titel während aller sechs Ladevorgänge, Menü, HUD, Explosionen, Paletten/Cycling,
Sterne und Übergang unverändert. **Keine XEMU-Erfolgsaussage und keine Stable-Markierung.**

### Ergebnisprotokoll (14.10.2026)

- Originalbelege:10 vollständig dekodierte Spannen mit172 Instruktionen;
  jede Spanne stimmt nach Relokation mit ADF und beiden RAM-Kopien überein.
- 14 Tests bestanden: Loader/Menu und alle sechs DATs,16.16-Floor-vor-Multiply,
  DY1/2/3, links/rechts/45°/negative und Null-Distanz, Streuung0..19 auf beiden
  Seiten, RNG-Isolation, sechs Slots und Ereignisverlust ohne RNG-Verbrauch bei
  vollem Pool, Weiterflug nach Schützentod, signed Randflug/Y200-Lebensende,
  unveränderte Player-Projektilbewegung, Schuss-/Kollisions-Gate.
- Alle100 Level initialisieren die richtige DY und löschen signed-/Format-Zustand.
  Level1/3/29/54/100 laufen zusätzlich je50 vollständige Host-Spielupdates.
  Original-DY-Verteilung:19 Level mit1,80 mit2, Level100 mit3.
- Player:100 vollständige Hauptschleifenupdates ergeben genau100 Bewegungsaufrufe,
  Start-X0 bei gehaltenem Rechts-Joystick ergibt X100 nach50 und X200 nach100
  Updates. Separate Links-/Rechtsläufe testen Rand-Clamping und ungerade Start-X.
  Explosion aller sieben Frames, Respawn bei X73/Y184 und steuerbarer Blinkphase
  geprüft; Schussursprung bleibt am autoritativen Player-Record.
- LEVEL CLEAR/Loslassen/Neudruck,100→1, R mit Score-/Lebenreset und Highscore-Erhalt,
  Menü-F1-Levelwahl und Ereignisreset, X/BASIC-Registerrestore und erneutes RUN
  bestehen im Hostmodell. Der isolierte T-Pfad behält8.8 auch nach T-Umschalten.
- Schussereigniscode `$A600–$AF07`, Angriffsauswahl und -takt, Loader,
  Projektil-/Explosionsgrafiken und Stern-/Übergangskern sind bytegleich.
- Zwei isolierte Builds liefern für **sämtliche Builder-Ausgaben** identische
  SHA-256-Listen; PRG45057Bytes, vollständiges D81819200Bytes, sieben Dateien,
  alle Dateiketten/Inhalte geprüft. Keine Stable-Datei verändert.
- Beispielkosten im CPU-Modell:ein fractional Spawn427 Instruktionen,
  sechs aktive normale Projektile pro Update264 Instruktionen. Kein neuer IRQ,
  Spritekanal oder DMA-Transfer. Das sind Instruktionszahlen ohne Bus-/DMA-Wartezeit,
  **keine gemessene XEMU-Rasterauslastung**. Die Division ist auf16 Schritte,
  die Multiplikation auf DY<=3 begrenzt, der Pool auf sechs Slots.

Die native effektive Player-Geschwindigkeit und das echte Rasterzeitbudget bleiben
bewusst offen; XEMU-Abnahme und Vergleich des Testparameters mit Amiga sind erforderlich.
