# Vyper Amiga – Analyse möglicher Wiederholungen von Angriffskurven

**Datum:** 11.10.2026. **Unabhängige Untersuchung; kein Eingriff in B2, Stage 5c Stable oder Stage 5d-1.**

## Tatsächlich untersuchte Originaldaten
- Vom Benutzer erneut hochgeladenes Original-ADF `VYPER(1).ADF`, darin **`Wave/Level`** als Amiga-OFS-Datei (Headerblock 979), exakt **11.400 Bytes = 100 × 114-Byte-Levelrecords**. Felder als **Big-Endian-WORDs** gelesen.
- `VYLV.DAT` (81.793 Bytes) zum Vergleich mit den Längen der aus dem Original übernommenen `Attack`-Kurven; VYLV enthält die unbekannten Original-Level-WORDs nicht.
- **Noch nicht durchgeführt:** Nachweis der konkreten 68000-Interpreterroutine im ausführbaren Amiga-Code, die das betreffende Feld liest und die Kurve zurücksetzt. Die Deutung als Wiederholungszähler ist daher eine **starke Hypothese, kein bestätigter Originalalgorithmus**.

## Wichtigster Kandidat: WORD bei Original-Leveloffset `+$70` (dezimal 112)

Das letzte WORD jedes 114-Byte-Levelrecords nimmt ausschließlich Werte **1, 2, 3, 4** an:

| Wert | Anzahl Level |
|---:|---:|
| 1 | 78 |
| 2 | 19 |
| 3 | 1 |
| 4 | 2 |

**Alle Levels mit Wert >1:**

- Wert 2: **32, 36, 41, 44, 45, 47, 49, 52, 54, 56, 58, 59, 66, 69, 73, 79, 82, 97, 98**
- Wert 3: **46**
- Wert 4: **30, 51**

Der Kandidat ist auffällig, weil:
1. Level 1–20 ausschließlich Wert 1 besitzen, was zur Beobachtung der einfachen frühen Angriffe passen könnte.
2. Mehrere Level mit **kurzen Angriffskurven** haben höhere Werte: Level 30 (24/24 Bytes, Wert 4), Level 46 (20/20 Bytes, Wert 3), Level 51 (41/41 Bytes, Wert 4), Level 32 (54 Bytes, Wert 2).
3. Nicht jede kurze Kurve hat einen höheren Wert: Level 25/50/99/100 haben Sonderkurven von nur einem Byte und Wert 1. Ebenso hat Level 45 (205/161/72 Bytes) Wert 2. Eine einfache „auf feste Dauer auffüllen“-Regel ist daher **nicht** belegt.
4. Das Feld wurde beim bisherigen VYLV-Konverter nicht als eigener Parameter in den neuen Levelrecord aufgenommen; selbst wenn die Wiederholungssemantik bestätigt wird, müsste eine **zusätzliche versionierte Datenerweiterung** erfolgen, statt blind einen freien Byteplatz zu überschreiben.

## Weitere Kandidaten / Abgrenzung

- `+$6C`: Werte **1 (19 Level), 2 (80 Level), 3 (1 Level)**; der Wechsel liegt fast durchgehend bei Level 21, mit Ausreißern. Könnte Schwierigkeit oder ein weiterer Ablaufparameter sein.
- `+$6E`: Werte **1 (34 Level), 2 (66 Level)**, stark levelabhängig, Bedeutung offen.
- `+$18/+1A`: häufig 0/30/60, zusätzlich 1/10/20; könnten Zeitparameter sein, aber keine belegte Wiederholungssteuerung.
- `+$3E/+40`: meist 0/1, einmal 2; ebenfalls offen.
- `+$66`: bereits **Anzahl gespeicherter Angriffskurven** (1–4), daher **nicht** mit Wiederholungszahl verwechseln.
- `+$4C`: bestätigter starker Kandidat für Levelpalette (0–19), **kein Wiederholungszähler**.

## Offene technische Frage

Selbst wenn `+$70` eine Wiederholungszahl ist, muss die **Art** der Wiederholung geklärt werden:
- Kurvenzeiger nach Ende auf denselben Anfang zurücksetzen?
- Wiederholung der Delta-Bewegung relativ zum zuletzt erreichten Punkt oder erneute Basisposition?
- Erneutes Durchlaufen nach Offscreen-Reentry?
- Wechsel zu einer anderen Kurve?
- Zählt der Wert die **Gesamtzahl** der Durchläufe oder zusätzliche Wiederholungen?

Der bislang rekonstruierte ATTACK-Endmarker/RETURN-Übergang reicht **nicht** aus, um dies zu beantworten.

## Empfohlene Verifikation ohne Gameplay-Umbau

1. In WinUAE gezielt **Level 30, 46 und 51** mit dem Original vergleichen (dort `+$70=4/3/4` und kurze Kurven), dazu Level 29/31 als Kontrollfälle mit Wert 1.
2. Optional gezielte 68000-Codeanalyse: Suche, wo `Level + $70` in die Laufzeitstruktur kopiert und am Kurvenende dekrementiert/verglichen wird. Nicht die gesamte Engine neu disassemblieren.
3. **Nur wenn bestätigt** einen separaten Testbuild mit explizitem Repeat-Parameter erzeugen. Keine Änderung an den Stable-Ständen oder der laufenden B2-Variante.
