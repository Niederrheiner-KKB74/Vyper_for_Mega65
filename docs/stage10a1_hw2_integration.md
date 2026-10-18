# Stage10a1-HW2: Integration zur Prüfung

## Referenzen

Zielbasis: main `08e0272319ead24f2f189b9391aec56712d54569` (PR88).
Übernommen werden drei unveränderte Commits von stage10a1-hw:

- `2f56b24529c9d5c3863c0c506fddf06c0a3dd9e6`: H320/GOTOX und Audioinitialisierung.
- `5c956b126743285000c515f3c535307c8a4d9f00`: RRB-Doppelpufferung und HW2-Image.
- `0b1c083f46dc41e7c6b8fb743b3f39b5a9af09cf`: AGENTS-Regel19 und dokumentierte Abnahme.

Die Release-README dokumentiert Benutzerbestätigung am17.10.2026 auf Core0.97
aaf4542, ROM920413, PAL sowie in XEMU. Bei der Integrationsprüfung wurde kein
neuer Hardware-/XEMU-Lauf durchgeführt. Eine vollständige100-Level-Abnahme
ist durch die übernommene Bestätigung nicht dokumentiert.

## Änderungen gegenüber main

| Bereich | Bisher | HW2 |
|---|---|---|
| Spielgeometrie | H640, CHRXSCL60, verdoppelte GOTOX | H320, CHRXSCL120, logische X; HUD240 |
| Lebensfelder | X490/524/558/592, Abschluss632 | X245/262/279/296, Abschluss316 |
| Meldungen | GAME OVER168, GET READY204/208 | 84 bzw.102/104 |
| Audio CURRENT | Bank vor Low/High | Low/High vor Bank; C übernimmt die Adresse |
| D711-Prüfung | Vergleich mit80 | nur AUDEN/Bit7 |
| RRB-Renderer | zehn NOPs | D051=0 und fünf NOPs; NORRDEL0 |

Die Änderungen bleiben längengleich. Speicherbereiche, Audio-ABI und Original-
PCM werden nicht neu angeordnet. Regel19 verlangt Hardwareabnahme für neue
Grafik-/Soundänderungen. Historische Releases bleiben unverändert.

## Regulärer Quellbuild

Voraussetzungen: Python3/Pillow, Java und offizieller KickAssembler5.25.
Download: https://theweb.dk/KickAssembler/
Vom Builder geprüfte JAR-SHA256:
`9592a39336e73a1db8b4a7749256d62d29b113b1c7f0f6c86ea43870ebd9ae1f`.

```sh
python tools/build_stage10a1_hw2.py --kickass /path/to/KickAss.jar --output build/stage10a1-hw2
```

Der neue Einstieg verwendet den regulären Stage10a1-Quellbuild einschließlich
Konverter und Assembler; keine Binärpatches. Anschließend packt er dessen Dateien
in HW2-Reihenfolge und mit HW2-Diskettennamen. Der alte Builder erzeugt zusätzlich
VYPER_STAGE10A1.d81 mit anderem Namen und anderer Dateireihenfolge.
Dateiketten und BAM werden geprüft. Alle vier HW2-Referenzartefakte müssen
bytegleich sein; Ziele unter releases/ werden abgelehnt. Der historische
Patchgenerator und alle bestätigten Releases bleiben unverändert.

Am18.10.2026 regulär aus Quellen reproduziert, jeweils identisch zum HW2-Release:

| Datei | SHA256 |
|---|---|
| STAGE10A1.PRG | `39801954a71d74914772d712ae1eeba6dabc8306ed90767f3dbaf2eaef81df63` |
| AUDIO_CORE.PRG | `4b298b26fd80c6285ac37727a8114fbf25919291dfd54a8add200ba0ee4a282e` |
| VYSO.DAT | `775e901da9c4f6a30a50f4596b43bc35c691f02f6a71f63587c3558d9c37a90f` |
| VYPER_STAGE10A1_HW2.d81 | `53deee9b018bf3e1af4ba59f96ca76c9348658444a95b324aecb734741db5e25` |

Der Quellbuilder prüft zusätzlich die vorhandenen Stable-Refs und historischen
Dateien. Es ist kein neues Release notwendig, da die bestätigten Bytes bereits
vorhanden sind. Der aktuelle Bericht und die Symbol-/Speicherkarten liegen im
separaten Buildziel.

## Bestehende Hosttests gegen den neuen Build

Die Stage10a1-Fixtures unterstützen STAGE10A1_ARTIFACTS; ohne Variable bleibt
ihr bisheriges Releaseziel erhalten. Kopien ersetzen temporäre Symlinks für
Windows ohne Symlink-Berechtigung. Bei einem HW2-Bericht wird der Audiocode
gegen HW2 geprüft; unveränderte Original-DATs weiterhin gegen Stage9b1.

```sh
export STAGE10A1_ARTIFACTS="$PWD/build/stage10a1-hw2"
PYTHONPATH=tools:tests python -m unittest discover -s tests -p 'test_stage10a1*.py' -v
```

PowerShell: `$env:STAGE10A1_ARTIFACTS=(Resolve-Path build/stage10a1-hw2).Path`.
PYTHONPATH verwendet unter Windows `;`. Testabhängigkeit: py65 1.2.0.
Die eingeschränkten CPU-/VIC-/PCM-/DOS-Modelle ersetzen keine Hardwareprüfung.

## Mergegrenze

Integrationsvorschlag; main bleibt bis ausdrücklicher Benutzerfreigabe unverändert.
Vor Merge Ziel-/Head-SHA erneut prüfen. Diagnose-PRs90/92/94/97/98 werden nicht
automatisch übernommen. AGENTS-Regel18 beschreibt den damaligen Stage10a-Stand;
Regel19 und dieser Bericht dokumentieren die spätere HW2-Bestätigung.
