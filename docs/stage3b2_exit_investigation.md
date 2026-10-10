# Stage 3b-2: BASIC-Exit – Untersuchung vom 10.10.2026

Der Benutzer bestätigt Laden und Verifizieren der Originaldaten, richtige
Gegnergrafiken und den Enginebetrieb unter XEMU. Nach `X` bleibt eine ungefähr
acht Pixel breite rote horizontale Linie an der Cursorposition. BASIC funktioniert.
Die Testumgebung verwendet laut Benutzer ROM **V920395** und **80×25**.
Der Fehler wurde rückblickend auch in Stage 3b-1 beobachtet. Stage 3b-2 ist deshalb
**nicht freigegeben**; kein Stable-Tag wird gesetzt.

## Nachgewiesene Befunde

- `exit_to_basic` ist im archivierten Stage-2ja-Quellcode sowie in Stage 3b-1 und
  Stage 3b-2 identisch. SHA-256 des Quellabschnitts bis `// Runtime state`:
  `af2b1415961c62b1754696d9d95808f9e06f50aa890380a1d01bfb058d4713cf`.
- Der Exit deaktiviert Hardware-Sprites, restauriert die gesicherten 2 KB
  Color-RAM und die erweiterten VIC-Register für Modus, Zeilenbreite, Screen-,
  Color-, Zeichensatz- und Spritepointer, Palette-Auswahl, Zeilenzahl und HOTREG.
  HOTREG wird zuletzt restauriert. Border und Hintergrund werden restauriert.
- Die Legacy-Register `$D011/$D016/$D018/$DD00` werden gesichert, aber bewusst
  nicht zurückgeschrieben. Das gehört bereits zur ursprünglichen Exit-Strategie;
  ein Zusammenhang mit dem aktuellen Fehler ist nicht nachgewiesen.
- Es gibt keine explizite Sicherung des BASIC-Screen-RAM oder der internen
  KERNAL-Cursorvariablen. Palette-Inhalte werden ebenfalls nicht gesichert;
  die Engine programmiert Palette 1 und 2.
- Stage 3b-1 ergänzt vor der unveränderten Engine KERNAL-Datei-I/O, Statusausgaben
  und eine Wartezeit von 60 Frames. Stage 3b-2 ergänzt Parser und Grafik-DMA.
  Die neue Grafikkopie schreibt nach `$9840–$98BF`, mit Guards innerhalb
  `$9800–$98FF`; die DMA-Rücklesepuffer liegen bei `$6800/$6900`.
- Ein belegungsbezogener Konflikt ist aufgefallen: Die Engine schreibt
  Objektrecords nach `$1000–$12FF` und Diagnostik nach `$1300–$131F`. Die aktuelle
  offizielle Speicherübersicht ordnet `$0002–$15FF` den KERNAL-Daten zu und nennt
  erst `$1600–$1EFF` als freien Bereich. Diese Engine-Adressen sind bereits in
  Stage 2ja vorhanden. **Dieser Konflikt allein beweist die Ursache der roten
  Linie nicht.** Die tatsächlich betroffenen Variablen des verwendeten ROMs
  müssen identifiziert werden.
- Neuere ROMs können in BASIC-80×50-Modus Bank 4, Region 0 reservieren. Das
  überschneidet sich mit dem vorgeschriebenen Ladeziel `$40000`. Der bestätigte
  Modus 80×25 schließt diese 80×50-Reservierung als Erklärung des Tests aus.

## Quellen zur ROM-Abhängigkeit

Die zusätzlichen Quellen dienen nur der Diagnose; keine externen Spielassets
oder ROM-Binärdateien wurden ins Projekt übernommen.

- [Offizieller User Guide, Speicherübersicht](https://github.com/MEGA65/mega65-user-guide/blob/cefce48d72e5c98d732c0589461d62b205b5165f/memory.tex):
  KERNAL-Bereich und freier RAM.
- [ROM-Changelog](https://github.com/MEGA65/mega65-rom-public/blob/83c14797980b895eddde82df71f87084cf036929/CHANGELOG.md):
  80×50-Speicherreservierung, neue CURSOR-KERNAL-Schnittstelle ab 920415,
  Änderungen an der Cursor-Darstellung.
- [ROM-Issue 175](https://github.com/MEGA65/mega65-rom-public/issues/175):
  dokumentiert Cursorartefakte bei aktivem Cursor und Textausgaben. Es ist kein
  Nachweis, dass derselbe Fehler hier vorliegt. Laut User Guide ist der Cursor
  bei normalem `SYS` grundsätzlich deaktiviert.

## Noch erforderliche Diagnose

ROM V920395 und 80×25 sind bestätigt. Noch offen ist, ob die Linie nach dem
ersten Tastendruck verschwindet. Für einen Nachweis sind Cursorzustand,
tatsächlich verwendete Screen-/Zeichensatzadressen und
KERNAL-Arbeitsbereiche vor/nach dem Lauf gezielt zu vergleichen. In dieser
Cloud-Umgebung fehlen XEMU und das verwendete ROM; die vorhandenen KERNAL-/DMA-
Testmodelle können die Cursoranzeige nicht reproduzieren. Die öffentlichen
ROM-Quellen enthalten nur Fehlerberichte und Changelog, keinen ROM-Quellcode.
Für die konkrete ROM-Analyse wird die im Test verwendete ROM-Datei benötigt.

Bis zum Nachweis der Ursache bleiben ASM, PRG und D81 unverändert. Ein
Cursor-Reset, Bildschirm-Clear oder Übermalen würde den gewünschten Nachweis
nicht liefern. Es wurde deshalb **noch keine Exit-Korrektur** eingebaut.

## Bisherige Verifikation und nächster Releasevergleich

Alle 18 vorhandenen Stage-3b-2-Hosttests bestanden erneut. Sie prüfen Originaldaten,
variable Recordgrenzen, Zuordnung Index 14 → Typ 12, Grafik-DMA mit Rückvergleich,
Guards, Fehlerpfade, definierte Engine-Patches und D81-Dateien. Sie prüfen keinen
echten BASIC-IRQ oder Cursor.

Referenz für den späteren Vergleich ist Commit
`778b7d41c26086dc143312453ce033ea9e8d8130`. Nach einer belegten Korrektur sind
Codeänderungen und Artefakt-Hashes dagegen zu dokumentieren, PRG und D81 neu zu
bauen und der XEMU-Test einschließlich `X`, normalem Cursor und erneutem
Laden/Starten durchzuführen. Stage 3b-1 und `stage3b1-stable` bleiben unangetastet.
