# Projektstand – 2026-10-10

## Bestätigt durch XEMU-Test des Benutzers

**Stage 2ja:** stabile Spielengine mit 24 animierten RRB-Pixies, Joysticksteuerung und funktionierendem RRB-Clearing. Als unveränderte Referenz erhalten.

**Stage 3a-1:** Das Lesen des `VYLV.DAT`-Headers funktioniert nach Ergänzung von `SETBNK` mit A=0, X=0 vor `SETNAM`. Ergebnis: Header VYLV, Version 1, 100 Level, READST $00.

**Stage 3a-2:** `VYLV.DAT` vollständig nach `$40000`, `VYGR.DAT` vollständig nach `$54000` geladen. DMA-Rücklesevergleiche erfolgreich. Level-1-Record per DMA nach `$7000` kopiert; Signatur geprüft. Programm kehrt zu BASIC zurück.

## Wichtige Fehlerursachen

- Ohne `SETBNK` war `READST $42` schon beim ersten `CHRIN` zu sehen.
- Der erste Stage-3a-2-Versuch schrieb in `$20000` (ROM) und meldete DMA-Vergleichsfehler $04.
- Mit `$40000` / `$54000` wurde der vollständige Test erfolgreich.

## Noch offen

- Import abgeschlossen: bereitgestellte Loader-Quellen, Binär-Assets, Build-Skripte und Releases sind in der vorbereiteten Struktur enthalten; Stage 2ja bleibt als unverändertes Archiv erhalten.
- Build-Skripte verwenden derzeit `/mnt/data`; für die Cloud-Entwicklung ist eine gesonderte Einrichtung erforderlich.
- Stage 3b-1: Loader-Integration implementiert, assembliert und automatisch geprüft; XEMU-Abnahme offen.
- Spätere Stages: Levelstruktur, Gegnerzuordnung und Grafikframes in die Engine integrieren; Stage 3b-1 verwendet die geladenen Daten noch nicht für Gegnersteuerung.
- Keine unbestätigten Änderungen an Stage 2ja.


## Stage 3b-1 – Entwicklungsstand (kein bestätigter XEMU-Erfolg)

Neue Quelle `src/engine/stage3b1.asm`, Artefakte `releases/stage_3b1/` und
reproduzierbarer Builder `tools/build_stage3b1.py`. Die Engine stammt ausschließlich
aus dem vorhandenen Stage-2ja-Archiv. Ihr Maschinenprogramm, Grafikdaten und
Tabellen bleiben bytegenau erhalten; nur der BASIC-SYS-Einstieg und ein vorher
ungenutzter Loader-Bereich unterscheiden sich. Stage 2ja und Stage 3a-2 unverändert.

Vor dem RRB-Start werden beide Originaldateien per SETBNK/SEQ und der bisherigen
F018A-DMA-Konfiguration geladen. Pufferkonflikte sind durch `$6800/$6900` und
Level-Kopie `$7600` vermieden. DMA-Rückvergleich, Level-Signatur und die aus den
Originaldaten abgeleiteten Bytesummen werden geprüft. Erfolgsmeldung vor der
Engine-Initialisierung; kein Text im RRB-Spielbetrieb. Keine DAT-gesteuerten Gegner.

Bestätigt: Assembly mit KickAssembler 5.25, bytegenaue Reproduktion der Baseline,
identische Artefakte aus zwei Builds, Originaldaten-SHA-256, D81-Dateiketten und
BAM sowie 12 bestandene Host-Tests des assemblierten Loaders mit KERNAL-/DMA-Modellen.
**Nicht bestätigt:** reale Geräteabläufe, RRB-Darstellung, Animation, Joystick und
X-Exit von Stage 3b-1 unter XEMU. Das Akzeptanzkriterium bleibt bis zum Vergleich
offen. Anleitung und Checkliste: [stage3b1.md](stage3b1.md).
