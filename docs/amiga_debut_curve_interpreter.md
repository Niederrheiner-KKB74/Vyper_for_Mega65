# Vyper (Amiga): rekonstruierter Einflug-Kurveninterpreter – Referenz für Stage 4b

**Status:** Rekonstruktion aus der früheren gemeinsamen Analyse der originalen Amiga-Dateien `Debut`, `Level`, `Forme`, `Attack` sowie WinUAE-ChipRAM-Dumps (8.–9. Oktober 2026). Die Originaldateien, der dekompilierte Interpreter und die Speicherabbilder liegen **nicht** in dieser Dokumentation. Die folgenden Aussagen sind frühere Analyseergebnisse, **keine neu durchgeführte Binärverifikation**. Codex soll sie gegen die tatsächlich vorhandenen Dateien prüfen und Abweichungen protokollieren. Insbesondere die Original-Amiga-`Level`-Offsets nicht mit Offsets der MEGA65-`VYLV.DAT` verwechseln.

## 1. Bewegungsbyte: identische Dekodierung für Debut und Attack

Die frühere Analyse identifizierte pro Kurvenbyte `b` folgende bitweise Delta-Kodierung:

| Bit(s) | Bedeutung |
|---|---|
| 7 | Vorzeichen X (gesetzt = negatives Delta) |
| 6–4 | Betrag X, 0..7 |
| 3 | Vorzeichen Y (gesetzt = negatives Delta) |
| 2–0 | Betrag Y, 0..7 |

```python
def decode_delta(b):
    dx = (b >> 4) & 0x07
    dy = b & 0x07
    if b & 0x80: dx = -dx
    if b & 0x08: dy = -dy
    return dx, dy

def expand_curve(packed, start_x, start_y):
    x, y = start_x, start_y
    result = []
    for b in packed:
        dx, dy = decode_delta(b)
        x += dx
        y += dy
        result.append((x, y))
    return result
```

**Wichtig:** Prüfen, ob die Originalroutine den Startpunkt separat ablegt, bevor der erste Delta-Schritt geschrieben wird. Dies beeinflusst `n` vs. `n+1` beim Kurvenzeiger; nicht ohne Abgleich festlegen. Die obige Routine illustriert die Delta-Expansion, nicht die vollständige Amiga-Speicherbelegung.

## 2. Original-Amiga-Datei Debut

- Die frühere Analyse indexierte **248 Einflugkurven**, deren gepackte Nutzdaten die **46.422 Bytes** von `Debut` ausfüllen.
- **Level 1:** zwei Kurven bei `Debut`-Offsets **0** und **158**, mit Längen **158** und **165** Bytes.
- Startpositionen der beiden Einfluggruppen: **links (20,0)** und **rechts (220,0)** in den damals untersuchten logischen Koordinaten.
- Kurven werden in eine Folge von 16-bit-X- und 16-bit-Y-Werten expandiert: **4 Bytes pro Punkt**. In der WinUAE-Analyse wurde der laufende Punktzeiger durch `P = curve_buffer_start + 4*n` erklärt.
- In einem früheren Abgleich passten **20 von 20** untersuchten Laufzeiger-/Positionspaaren zu dieser Struktur.

Die Angabe der Kurvenoffsets bezieht sich auf die **originale Datei `Debut`**, nicht automatisch auf einen absoluten Offset in `VYLV.DAT`.

## 3. Original-Amiga-Datei Level: beobachtete Felder

Folgende Felder wurden in der früheren Analyse für den **originalen Amiga-Level-Datensatz** identifiziert (Offsets relativ zum dortigen Level-Datensatz):

| Offset | Frühere Interpretation |
|---|---|
| `+$00..+$0F` | Einflug-/Debut-Kurvenoffsets |
| `+$10..+$17` | Einflug-Kurvenlängen |
| `+$20..+$2F` | Gruppen-Startkoordinaten X/Y |
| `+$30` | Anzahl aktiver Einfluggruppen |
| `+$32..+$39` | Gegnerzahlen je Gruppe |
| `+$42` | zeitlicher Abstand der Gegnerstarts |

Für Level 1 wurden **zwei parallele Einfluggruppen** mit insgesamt **22 Gegnern (11 + 11)** und **16 Ticks Startversatz** zwischen aufeinanderfolgenden Gegnern festgestellt. Die Zeitbasis wurde als **50 Hz** angesetzt: 16 Ticks entsprechen 320 ms. Der konkrete Zusammenhang zwischen `+$42`, Gruppenzählern und Auslösung muss im Code noch einmal überprüft werden, insbesondere ob der Versatz pro Gruppe oder global wirkt.

**Nicht verwechseln:** Die MEGA65-Datei `VYLV.DAT` besitzt nach der späteren Konvertierung ein anderes, kompaktes Datensatzformat: 8-Byte-Levelheader, Einfluggruppen, 6-Byte-Gegnertabellen und Angriffskurven. Für Level 1 war der Datensatzbeginn bei **Dateioffset `$0328`**, Datensatzlänge **849 Bytes**, die 22 Gegner-Einträge beginnen bei **Datensatzoffset `$015B`**. Pro Gegner: X-Word bei +0, Y-Word bei +2, Grafiktyp bei +4, Angriffsindex bei +5. **Nicht** die Amiga-`Level`-Offsets direkt als `VYLV`-Offsets verwenden.

## 4. Laufzeit-/Zustandsablauf der Amiga-Engine

Aus den früheren Speicherabbildern und Zustandsuntersuchungen:

1. **Einflug (State 1):** Der Gegner erhält eine der vorab expandierten X/Y-Kurven, liest nacheinander Koordinatenpaare und bewegt sich entlang der Punkte. Ein Kurvenzeiger schreitet je Punkt um vier Bytes fort. Der untersuchte Code dekrementierte den Zähler bei **`$6A`** und wartete auf die zeitliche Freigabe über **`$6C`** (Adressen/Offsets aus dem damaligen Laufzeitkontext, **nicht** als globale feste MEGA65-Adressen übernehmen).
2. **Ende des Einflugs:** Übergang in **State 2**.
3. **Rückkehr zur Formation (State 2):** Ein **eigenständiger Bewegungszustand**, nicht einfach ein Sprung/Teleport zum Ziel. In der späteren Attack-Analyse wurde beobachtet: Rückkehr mit **±1 pro Update** zur jeweiligen Zielposition. Ob diese Regel für X und Y beim Ende des Debut-Einflugs identisch ist, muss am Original oder mit der Referenzposition verifiziert werden. **Keine erfundene Sofortpositionierung**.
4. **Formation:** Erst nach Erreichen des zugeordneten Formationsplatzes den Gegner als `FORMATION` markieren.

In der Attack-Analyse gab es zusätzlich einen **negativen Y-Endmarker**, der State 3 in State 2 überführte und Y auf 0 setzte. **Das ist ein Befund für Attack, kein nachgewiesener identischer Debut-Endmarker.** Für Stage 4b die Ende-Bedingung aus der **bekannten Debut-Kurvenlänge** ableiten, sofern Originaldaten/Code das bestätigen; den Attack-Endmarker nicht blind übertragen.

## 5. Referenz für Formationszuordnung

- Level 1 hat **22 Gegner**, alle mit `graphic_type = 14` im VYLV-Record.
- Die **visuell bestätigte** Übersetzung lautet **VYLV 14 → VYGR-Typ 15 (1-basiert)** mit **6 Animationsframes**.
- Die Formation-X/Y-Werte stehen in den 22 sechs-Byte-Gegnereinträgen in `VYLV.DAT`; **aus der Datei lesen**, keine Formation aus einem Screenshot schätzen.
- Pro Gegner die stabile Zuordnung `ID → Einfluggruppe → Kurvenstart → aktueller Schritt → Ziel-X/Y → Status` bewahren.
- `DEAD`-Gegner dürfen nach einem Abschuss während ENTRY **nicht** beim Formationsübergang wieder auftauchen.

## 6. Was Codex konkret tun soll

1. Bestehende VYLV-Konvertierung/Parser prüfen und die beiden Level-1-Kurvenbytes **verlustfrei** aus `VYLV.DAT` auslesen. Falls die dortige Repräsentation bereits absolute Positionen enthält, **nicht erneut** die Delta-Dekodierung darauf anwenden.
2. Nibble-Decoder gemäß Abschnitt 1 gegen die tatsächlichen Level-1-Bytes testen; erste und letzte 10 XY-Punkte je Kurve dokumentieren. Startpunkt und Byte-/Punktindexierung verifizieren.
3. Einflugstarts (20,0) / (220,0), 11+11 Gegner und 16-Tick-Abstände gegen die tatsächlichen VYLV-Felder und vorhandene Konvertierungslogik abgleichen. Abweichungen nicht stillschweigend überschreiben.
4. Gruppen parallel verwalten; pro Gegner eigenen zeitlichen Start und eigenen Kurvencursor, aber gemeinsame unveränderliche Kurvendaten zulassen.
5. State 1 → State 2 → FORMATION nachbilden, wobei State 2 kontinuierlich auf die originalen Formation-X/Y-Ziele zusteuert. ±1-Regel gegen vorhandene Referenz prüfen.
6. Bewegung mit Stage-4a-Offscreen-Clipping im Y-Bereich 0..199 darstellen; negative Koordinaten signed halten.
7. `docs/stage4b_level1_entry.md` um **tatsächlich verifizierte** Offsets, Bytebeispiele, Decoder-Tests, Gruppen- und Formations-Tabelle ergänzen.
8. Original-ADF, WinUAE-Savestates oder `Debut`/`Level` nur dann als erneut geprüft deklarieren, wenn diese Dateien tatsächlich zugänglich sind. Bei fehlender Originalreferenz die oben dokumentierte historische Rekonstruktion als solche kennzeichnen und die vorhandene `VYLV.DAT` als primäre maschinenlesbare Quelle verwenden.

## 7. Offene, ausdrücklich zu verifizierende Punkte

- Ist die ursprüngliche Kurven-Zeitbasis exakt ein expandierter Punkt pro 50-Hz-Tick oder sind zusätzliche Pausen/Teiler aktiv?
- Enthält der expandierte Kurvenpuffer den Startpunkt als ersten Eintrag?
- Gilt die beobachtete State-2-Rückkehrgeschwindigkeit von ±1 pro Tick für beide Achsen und auch für Debut?
- Wie werden die zwei Gruppen zeitlich gegeneinander gestartet und die 16-Tick-Abstände auf einzelne Gegner angewendet?
- Gibt es einen Debut-spezifischen Endmarker oder genügt die Länge?

Diese Punkte sind **keine Einladung zu erfundenen Originaldaten**. Implementiere belegte Teile; prüfe die übrigen gegen die Daten und benenne Abweichungen klar.
