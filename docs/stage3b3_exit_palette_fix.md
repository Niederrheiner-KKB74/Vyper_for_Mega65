# Stage 3b-3 – BASIC-ROM-Palette beim Exit erhalten

Der Benutzer bestätigt die neue Spieler-Pixie-Darstellung. Nach `X` erschien
jedoch ein grauer Bildschirm mit sichtbaren wechselnden Elementen; BASIC nahm
Eingaben an und `RUN` startete das Programm erneut. Ein Syntaxfehler brachte
laut Benutzer die normale Anzeige zurück. Die korrigierte Fassung wurde am 10.10.2026 vom Benutzer als stabil bestätigt
(`stage3b3-stable`). Die Abnahme stammt vom Benutzer; ein eigener Emulatorlauf
wird nicht behauptet.

## Nachgewiesene Ursache

Die erste Fassung schrieb die Spielerfarben in Bank 3, Einträge 0..15.
Diese Einträge sind in XEMU zugleich die Farben der C65-ROM-Palette. Der Exit
restaurierte `$D030/$D070` korrekt, aber die dahinterliegenden Paletteneinträge
waren bereits überschrieben. Registerrestaurierung allein repariert diesen
Datenverlust nicht. Die erste Palettenprüfung schützte nur Bank 0 und bildete
die ROM-Palettenbeziehung nicht ab; deshalb konnte sie den Fehler nicht erkennen.

Nachweis im XEMU-Quellcode, Commit `40dfef0d1d5f56be2469492715c12bdb32c75b67`:

- `vic4_write_palette_reg_red/green/blue`: Schreibzugriffe auf Bank 3, Einträge
  0..15, aktualisieren gleichzeitig die emulierte ROM-Palette.
- `check_if_rom_palette`: bei ROMPAL aktiv (`$D030` Bit 2 gelöscht) verweist
  die Auswahl Bank 0 auf diese emulierte ROM-Palette. Deren erste 16 Einträge
  stammen aus Bank 3; die übrigen aus Bank 0.

[Quellcode](https://github.com/lgblgblgb/xemu/blob/40dfef0d1d5f56be2469492715c12bdb32c75b67/targets/mega65/vic4_palette.c).
Die Host-Regression bildet nun diese tatsächliche Beziehung ab, statt von vier
vollständig unabhängigen BASIC-Paletten auszugehen.

## Minimale Korrektur

Der Spieler verwendet jetzt Bank **2**, die bislang die Palette der im Spiel
**deaktivierten Hardware-Sprites** enthielt. Gegner und Orbit benutzen weiter
Bank 1. Bank 3 wird nicht mehr verändert. Das vorhandene GOTOX-Prinzip bleibt
identisch: Spieler `$60` → alternative Palette, andere Pixies `$00` → primäre.

`$D070` bei Spielerinitialisierung: **`$DB` → `$9A`**. Damit wechseln ausschließlich
MAPEDPAL und ABTPALSEL von 3 auf 2. BTPALSEL=1 und SPRPALSEL=2 bleiben gleich.
Grafikbytes, RGB-Werte, RRB-Wrapper, Loader, Parser, DMA, Steuerung, Bewegungsdaten
und Exit-Routine bleiben bytegleich. Kein Bildschirm-Clear, kein absichtlich
erzeugter Syntaxfehler und keine kosmetische Reparatur nach dem Exit.

Vergleich gegen Commit `eeca71203219a79bccedb0b78fc177cca6e325e1`:
**genau ein geändertes PRG-Byte bei `$3704`**. Keine neuen Speicherbereiche;
Stage 3b-2 und `stage3b2-stable` bleiben unverändert.

| Artefakt | Vorher SHA-256 | Korrigiert SHA-256 |
| --- | --- | --- |
| PRG | `99f0c9c405aa19fcf61df13b5286845d6e6dece4f022e55873af39d76b2c6ca7` | `4cdb98d30cda81fc2f812fef28e1b7786387050de6c56899ebd5222508cec81d` |
| D81 | `0cdaa7ff98b2985ac0900ddaccb055500da3e54b977813b7db1283a9e6cbc2c6` | `4eb766c5a8ec87e9579b2dcd2af87a0ff6c6bc5c4862740d87985db74ec4b3d3` |

## Prüfung und XEMU-Abnahme

43 Regressionstests bestanden, darunter acht für Stage 3b-3. Der neue Test startet
mit BASIC-Palette Bank 0 und ROMPAL aktiv, führt vollständigen Engine-Start,
Bewegung, `X` und erneuten Start aus. Die gesamte effektive BASIC-Palette und Bank 3
bleiben erhalten. Wird nur das alte Auswahlbyte `$DB` zurückgesetzt, reproduziert
der Test die veränderte ROM-Palette. Die bestehenden Tests für freigegebene
Spielerfarben, Palette-Unabhängigkeit, Bewegung, Clearing, Orbit-/Gegneranimation,
DMA und Cursorbereich bleiben aktiv. Assembly und D81-Prüfung bestanden;
Wiederholungsbuild byteidentisch. Dies ersetzt keine pixelgenaue XEMU-Prüfung.

Bitte XEMU **frisch booten**, bevor das neue D81 getestet wird: Die vorige Fassung
kann die aktuelle ROM-Palette bereits überschrieben haben. Danach
`LOAD"STAGE3B3",8` / `RUN`, Spielerfarben und Bewegung prüfen, mehrmals nach
unterschiedlicher Laufzeit mit `X` beenden. BASIC muss sofort normal erscheinen,
mit normalem Cursor, ohne Syntaxfehler als Reparaturschritt. Anschließend erneut
laden/starten. Dateien bleiben unter `releases/stage_3b3/` im Branch `stage3b-3`.
