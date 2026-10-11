# Analyse der Angriffskurven-Deskriptoren in VYLV.DAT

**Stand:** 11.10.2026. **Quelle:** vom Benutzer hochgeladene `VYLV.DAT`, 81.793 Bytes, SHA-256 `c99bc1262a10babc84f0ae7eb6ff019faccdeb0382711f99ffe6c23023d7d283`. Alle hier genannten Ergebnisse sind aus **dieser konvertierten MEGA65-Datei** extrahiert, nicht durch Disassemblierung des Original-Amiga-Codes bewiesen.

## Ergebnis

Das **Byte +5 jedes 6-Byte-Gegnerrrecords** (nach den WORD-LE-Formationskoordinaten X/Y und dem Grafiktyp-Byte +4) ist ein gültiger **nullbasierter Index in die Angriffskurvenliste des Levels**.

Für **alle 2.194 Gegnereinträge aller 100 Levels** gilt: `0 <= attack_index < attack_curve_count`. Es gibt 1–4 Kurven je Level und die Indizes 0–3. Dies ist ein sehr starkes strukturelles Indiz für eine **feste Kurvenzuordnung pro Gegner**, getrennt von der **zufälligen Auswahl des angreifenden Gegners**. Eine unabhängige Bestätigung der Original-Amiga-Routine steht noch aus.

**Empfehlung für die MEGA65-Engine:** Bei zufälliger Wahl eines FORMATION-Gegners die zu diesem Gegner gehörige `attack_index`-Kurve starten, **nicht** unabhängig eine zufällige Kurve ziehen. Die ursprüngliche Kurvenwahl des Amiga ist weiterhin als „noch nicht aus Originalcode bestätigt“ zu dokumentieren.

## Recordstruktur (Little Endian)

- 8-Byte-Levelheader: `level:word`, `group_count:byte`, `enemy_count:byte`, `entry_interval:word`, `attack_count:word`.
- Danach `group_count` Einfluggruppen: je `enemy_count:word`, `start_x:word`, `start_y:word`, `curve_length:word`, anschließend genau `curve_length` komprimierte Bytes.
- Danach `enemy_count` Gegnerrecords von je **6 Bytes**: `formation_x:word`, `formation_y:word`, `graphic_type:byte`, **`attack_index:byte`**.
- Danach `attack_count` Angriffskurven: je `length:word` und `length` komprimierte Bytes.
- Der Level-Offset-/Längentisch beginnt bei Datei-Offset 8; je Level 8 Bytes (Start: uint32 LE, Länge: uint32 LE). Level 1 beginnt bei `$0328`, Länge `$0351` (849 Bytes).
- Der Parser hat alle 100 Datensätze bis exakt zu ihrem jeweils deklarierten Ende gelesen.

## Gesamtstatistik

| Merkmal | Wert |
|---|---:|
| Level | 100 |
| Gegnerrecords | 2.194 |
| Level mit 1 / 2 / 3 / 4 Angriffskurven | 24 / 61 / 10 / 5 |
| Vorkommen Index 0 / 1 / 2 / 3 | 1.318 / 737 / 110 / 29 |
| Gegnerindizes außerhalb der Kurvenliste | **0** |
| Level, die nicht jede gespeicherte Kurve referenzieren | **25, 50** |

Die Levels **25 und 50** enthalten je zwei Angriffskurven von jeweils nur einem Byte `01`, aber alle 22 Gegner referenzieren ausschließlich Index 0. Auch Level **99** und **100** enthalten ungewöhnliche Ein-Byte-Angriffskurven. Diese Sonderfälle nicht ohne Originalprüfung als reguläre lange Flugkurven interpretieren; sie können besondere Levelmechaniken oder Platzhalter repräsentieren.

## Level 1 – zwei exakt gespiegelte Angriffskurven

- 22 Gegner, zwei Einfluggruppen (11+11), Einflugintervall 16.
- Angriffskurve 0: **183 Bytes**, 11 Gegner; Angriffskurve 1: **183 Bytes**, 11 Gegner.
- Die Kurven sind **für jeden Schritt exakt horizontal gespiegelt**: `dx_0 = -dx_1`, `dy_0 = dy_1` (Dekoder siehe `docs/amiga_debut_curve_interpreter.md` im Branch `stage4b-entry-analysis`).
- Gegner mit `attack_index=0` haben Formations-X 30..103, Gegner mit Index 1 Formations-X 122..195. Gleiche Formations-Y-Folge in beiden Hälften.
- Summierte Delta-Bewegung Kurve 0: (+80,+168); Kurve 1: (−80,+168). Dies sind **relative Summen der komprimierten Kurve**, keine absoluten Endpositionen.
- Erster Gegnerrecord: `62 00 2B 00 0E 00` = X98, Y43, Grafikindex14, Angriffsindex0.
- Der erste Gegner der zweiten Hälfte: X127, Y43, Grafikindex14, Angriffsindex1.

## Level 2 – drei Kurven für linke, rechte und mittlere Formation

- 22 Gegner, 3 Angriffskurven mit **163 / 163 / 217 Bytes**.
- Index 0: **7 Gegner**, Formations-X 43..83 (linker Teil).
- Index 1: **7 Gegner**, Formations-X 143..183 (rechter Teil).
- Index 2: **8 Gegner**, Formations-X 93..133 (Mitte).
- Alle 22 Gegner haben `graphic_type=0`, **aber drei unterschiedliche Angriffsindizes**. Die Zuordnung ist damit eindeutig **nicht allein aus dem Grafiktyp** ableitbar.

## Level 5 – zwei Kurven unterschiedlicher Länge

- 22 Gegner, Kurvenlängen **171 / 119 Bytes**.
- Index 0: 11 Gegner, Formations-X 25..103.
- Index 1: 11 Gegner, Formations-X 122..200.
- Gleicher Grafiktyp `4` in beiden Gruppen, aber unterschiedliche Attack-Indizes.

## Vier-Kurven-Beispiele

- Level 47: Kurvenlängen 62/38/38/62, referenziert von 5/6/6/5 Gegnern.
- Level 52: Kurvenlängen 126/126/84/84, referenziert von 5/5/6/6 Gegnern.
- Level 56: Kurvenlängen 157/157/27/27, referenziert von 5/5/6/6 Gegnern.
- Level 97: 126/126/84/84, 5/5/6/6.
- Level 99: 1/1/1/1, 6/5/5/6 (Sonderfall).

## Wichtig für Stage 4b-3 / folgende Stage

1. Die vorhandenen `attack_index`-Bytes der Gegner **beim Levelstart** in deren Laufzeitobjekte übernehmen.
2. Zufällig **den Angreifer** auswählen; Kurvenindex **aus dessen Objekt** beziehen, nicht erneut zufällig wählen.
3. Für Level 1 weiterhin zwei gespiegelte Kurven; für spätere Level alle 1–4 Varianten aus `VYLV.DAT` laden und Grenzen validieren.
4. `attack_index` darf `attack_count-1` nicht überschreiten; im Parser abweisen statt blind in Speicher zu lesen.
5. Unabhängig vom Grafiktyp speichern: derselbe Gegnertyp kann in einem Level unterschiedliche Attack-Kurven besitzen.
6. Die *ursprüngliche Amiga-Auswahlroutine* muss noch unabhängig aus Originalcode/Savestates verifiziert werden. Es ist möglich, dass der Konverter die Indizes schon aus einer früheren Interpretation abgeleitet hat; dieser Bericht beweist die **VYLV-Semantik**, nicht automatisch das Verhalten des Originalprogramms.
7. **Stage 4b-2 Stable unverändert lassen.** Die laufende Stage 4b-3 nicht ohne explizite Rücksprache durch Änderungen an Angriffsauswahl/Spielmechanik erweitern; die Erkenntnisse für die nächste dedizierte Stage übernehmen.

## Reproduzierbarkeit

Die Struktur lässt sich mit `tools/analyze_attack_descriptors.py` im Branch `analysis-attack-descriptors` prüfen. Das Skript benötigt nur `assets/VYLV.DAT` oder einen explizit übergebenen Dateipfad und die Python-Standardbibliothek.
