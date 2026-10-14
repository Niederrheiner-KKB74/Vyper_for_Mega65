# Stage 9b1 – zyklische Original-ATTACK-Kurven (Issue #79)

Entwicklungsbranch `stage9b1`, **nicht Stable**, kein Merge vor XEMU-Abnahme.
Unveränderte Basis: Stage9a Stable, Main-Merge
`9bbe02ed9d284575c14c23954659a781d6889ee9`, getesteter Programmstand
`7f50547337c4aa7256f908547d627dae7da433e0`.

## Ursache und Originalnachweis

Stage9a setzte nach dem letzten gepackten Deltabyte `e_phase=5` und bewegte den
Gegner anschließend bei festem X um zwei Y-Pixel pro Update. Die gepackte Länge
ist jedoch nur die Länge eines wiederholbaren Musters, nicht des ganzen Angriffs.

Verbindliche Grundlage: [PR #78](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/pull/78),
Analysecommit `04b1feb2337156c9cdc8feccea8b3d59cf624e28`. Die acht Analyse-/Evidenzdateien
wurden gezielt übernommen; der Analysebranch wurde nicht gemergt.
Siehe [Originalanalyse](amiga_attack_curve_end_analysis.md),
[Portvergleich](amiga_vs_stage9a_attack_end.md) und
[Disassemblierung](amiga_attack_end_evidence/68000-excerpts.txt).

Nachgewiesene Amiga-Adressen (relokierte CODE-Basis `$C08760`):

- `$C0AFAC…$C0B1AA`: Expansion in individuelle XY-Puffer. Beim Erreichen der
  gepackten Länge wird der Byteindex zurückgesetzt; der vorige XY-Punkt bleibt
  Grundlage des nächsten Deltas.
- `$C0B180/$C0B186`: Schleife bis signed Y≥216. `$C0B1A4` ersetzt das Y des letzten
  Punkts durch −1. Kein angehängter Punkt und keine Kurvenverkettung.
- `$C0D232`: einmaliger Startanker und Lesepointer; `$C0D4B2…` liest die expandierten
  Punkte linear. Negatives Y beendet ATTACK. Sound/Schussplanung werden nicht
  durch den gepackten Byte-Wrap erneut aufgerufen.

## Änderung im Port

Nur `stage9b1_attack.asm` ändert die Spielroutine. Die übrigen vollständigen
Stage9a-Quellen wurden als neue `stage9b1*.asm` kopiert und ihre Importnamen
angepasst. Der Loader-Fehlertext heißt bei gleicher Länge `STAGE9B1 LOAD ERROR`.

1. Kurvenindex und Cursor werden vor dem Lesen gegen Descriptorzahl/Länge geprüft.
2. Das aktuelle gepackte Byte wird unverändert als zwei signed-magnitude Nibbles
   dekodiert und auf die vorhandenen signed-16-Bit-Koordinaten addiert.
3. `fireevents.attack_tick` läuft einmal pro tatsächlich berechnetem Punkt.
4. Bei Port-Y≥200 wird der Gegner unsichtbar und Phase5 gesetzt, unabhängig davon,
   ob die gepackte Kurve bereits einmal durchlaufen wurde.
5. Ansonsten wird bei `cursor==length` ausschließlich der Cursor auf0 gesetzt.
   Anker, Koordinaten, Kurvenzuordnung, Animation und Schussplanung bleiben bestehen.
6. Nach dem unsichtbaren Bottom-Frame führt die vorhandene Routine zu Y=−16/RETURN;
   die bestehende Rückkehr steuert den individuell driftenden Formationsplatz an.

`audio8.attack` und `fireevents.attack_plan` bleiben ausschließlich in `a_start`.
Verbrauchte Y-Schwellen bleiben0, auch über mehrere Wiederholungen. Volle sechs
Gegnerschuss-Slots verursachen weiterhin Ereignisverlust statt Wiederholung.
Auswahlintervall30, maximal drei Angreifer, Projektilbewegung, Player-Bewegung,
Explosionen, Paletten, Audio, Menü, automatischer Übergang und Bonusleben bleiben
unverändert. Die Daten aller sieben DAT-Dateien einschließlich Audiocore sind
byteidentisch zur Stable-Basis.

## Bewusste Geometrie und offene Originalunterschiede

Der Port endet bei **Y≥200**, das Amiga erzeugt bis **Y≥216** und ersetzt den
terminalen Punkt. Der Port spielt keine native absolute Y-Liste ab, sondern
akkumuliert ab seiner pro Level verschobenen Formation (oberste Pixelzeile Y=0).
Deshalb wäre eine pauschale Übernahme der nativen216-Grenze falsch. In Level4
beträgt die Formationsverschiebung26 Pixel; `216−26=190` ist ebenfalls nicht
unsere gewählte200-Grenze. Zahl der Kurvenpunkte und Schuss-/Rückkehrzeitpunkte
können deshalb gegenüber dem Amiga abweichen. Der vorhandene unsichtbare
Bottom-/Top-Wechsel wird bewusst beibehalten.

ENTRY-B2-Y−16, Formationsplätze und RETURN-Timing sind unverändert. Die native
horizontale X-Begrenzung wird hier nicht zusätzlich eingeführt: Der Port behält
seine signed-Koordinaten und seinen bereits bestätigten Offscreen-Clipper.

Die vorhandene Gameplay-ATTACK-Sperre in Level25/50/99/100 bleibt bestehen.
Deren Ein-Byte-Decoder wird nur isoliert in Hosttests ausgeführt; dadurch wird
keine dieser Stages für Angriffe freigeschaltet. Keine Originaldatenänderung.

## Speicher und Build

Keine neuen RAM-Bereiche oder DMA-Puffer. Weiterhin pro Gegner Cursor `$1E9A`,
signed XY `$1E00/$1E16/$1E2C/$1E42`, Kurvenindex `$6F80`, Anker `$6F96/$6FAC`,
Bottom-Latch `$6FC2`; Descriptorpointer/-längen `$6FEC…$6FF8`.

Die Hauptbewegung bleibt in `$9F10…$9FE5` unter der ROM-Overlay-Grenze `$A000`.
Die Cursor-/Bottom-Abschlussroutine nutzt den frei gewordenen Ersatzflugbereich
`$36B0…$36F5`; Top-RETURN beginnt jetzt bei `$36D2`. Keine neuen Audio-/Loader-
Abbildungen, unveränderte Audio-ABI. Die Boundsprüfungen des Assemblers bleiben aktiv.
Vollständige [Assembler-Speicherkarte](../releases/stage_9b1/memory-map.txt).

```sh
python tools/build_stage9b1.py --kickass /pfad/zu/KickAss.jar
PYTHONPATH=tests:tools:/pfad/zu/py65 python -m unittest test_stage9b1 -v
```

KickAssembler5.25 mit vom Builder geprüfter SHA256; Python3.12 und OpenJDK21.
Hosttests benötigen py65==1.2.0. Der Build benötigt keine Audio-Neuextraktion;
der gemeinsame Konverter prüft die vorhandenen Originaldaten. Die übernommenen
Analysewerkzeuge sind separat nutzbar (Capstone5.0.7, siehe Originalanalyse).
Build-Ausgabe `releases/stage_9b1/`: vollständige Quellen/Includes/Symbole,
`STAGE9B1.PRG`, `VYPER_STAGE9B1.d81`, sieben SEQ-Dateien und SHA256-Manifest.
Das D81 enthält PRG plus VYTI/VYMN/VYLV/VYGR/VYCL/VYSH/VYSO.DAT.

## Tests und XEMU-Abnahme

Alle2194 Gegnerrecords terminieren im unabhängigen Referenzmodell innerhalb
von300 Punkten. [Vollständige Tabelle](stage9b1_attack_trajectories.csv), reproduzierbar
mit `python tools/analyze_stage9b1_trajectories.py`. Diese Tabelle ist eine
Deltaberechnung, kein gemessener Emulatorlauf; die Sonderlevel bleiben gesperrt.

**29 Hosttests bestanden (723,150 Sekunden)**. Zwei unabhängige Builds sind
in allen70 Release-Dateien byteidentisch. Das vollständige Protokoll steht in
[stage9b1_test_results.txt](stage9b1_test_results.txt).
Unter dem modellierten130-Frame-Stresslauf: maximal322 DMA-Jobs/Frame,
maximal802049 modellierte6502-Zyklen inklusive Warten, keine Audio-Unterläufe.
Der170-Frame-Übergang bleibt unterbrechungsfrei; Peak1941108 enthält die
Initialisierung des nächsten Levels. Dies sind Modellwerte, keine45GS02-Messung.
Die Tests führen die assemblierten Routinen in einem eingeschränkten CPU-/DMA-
Modell aus. Sie sind kein XEMU-Lauf und kein Nachweis realer Raster-/Audiozeiten.

Besonders aussagekräftiger Level4-Nachweis: Kurve43 Bytes, Nettodelta(+2,+38).
Slot0 beginnt bei(40,27). Nach Punkt43:(42,65), Cursor0; Punkt44:(44,67),
Cursor1. Stage9a hätte Punkt44 dagegen bei(42,67) dargestellt. Damit entfällt die
senkrechte Ersatzbewegung, ohne die akkumulierte Position zurückzusetzen.

Unter XEMU (50Hz, Joystick Port2) noch durch den Benutzer zu prüfen:

- Menü Level004: hohe/tiefe, linke/rechte Gegner über mehrere43-Byte-Durchläufe
  beobachten; kein Positionssprung, kein fester senkrechter Ersatzflug. Unterer
  Austritt einmalig, anschließender Wiedereintritt oben und Rückkehr zur driftenden
  Formation. Gegner unmittelbar vor/nach Wiederholung abschießen.
- Level001 sowie047/056: gespiegelte und verschieden lange Deskriptoren,
  Clipping links/rechts, bis zu drei unabhängige Angreifer, keine RRB-Artefakte.
- Pro Angriff kein erneut beginnender Angriffssound und keine durch Wiederholung
  neu geplanten Schüsse. Sechs Gegnerprojektile bleiben globale Obergrenze.
- Titel/Laden, Menü/F1/F2/F3, Levelnavigation, Player/Joystick, Treffer/Respawn,
  Paletten/Cycling/Sterne, automatischer Levelwechsel mit Sounds24/22 und
  Bonusleben nach drei echten Abschlüssen, GAME OVER/R, X→BASIC und erneutes RUN.

**Keine XEMU-Abnahme behauptet. Kein Stable-Tag, kein Merge vor Freigabe.**
