# Stage10b1a — Benutzer-Messungen und vollständiger Hardwarevergleich

Auswertung der beiden gleichnamigen D81-Uploads sowie der Archive
MEGA65_A1_A2_B.zip und XEMU_A1_A2_B.zip. Nur Analyse und Dokumentation;
keine Änderung an PRG, D81, Engine, Konfiguration oder Parametern.

## Erste Lieferung: Integrität und zunächst fehlende Daten

| Upload | SHA256 | Inhalt |
|---|---|---|
| erstes VYPER_STAGE10B1A.d81 | d1c98aa8a361569b7b0c83c1987cec5cab3ff7132e2ea387e87229f5cd353938 | exakt das unveränderte Release-Image, nur STAGE10B1A |
| zweites VYPER_STAGE10B1A.d81 | 5e8e468006ba437164f8eaec37d683fdc6f9d5557656402e9b739f07d2dfe40b | PRG plus V1AAX.REG/MEM und V1ABX.REG/MEM |

Beide PRGs sind byteidentisch zur Auslieferung. Die vier gefundenen Dumps
sind formal gültig (Größe, Magic, Variante, Verzeichnis/Adressfolge,
Prüfsumme). Headerlabel X und Firmware-Rohbytes sind mit XEMU vereinbar;
als Eingabebeleg werden diese Dateien als XEMU-Ergebnisse eingeordnet.
**In diesen ersten beiden Images war kein Register-/Speicherdump des echten
MEGA65 vorhanden. Er wurde inzwischen nachgereicht; siehe vollständigen
Hardwarevergleich unten.** Das erste Image darf nicht als Hardwaremessung ausgewertet
werden, nur weil es eines von zwei gleichnamigen Uploads ist.

Die Exporte überschreiben je Variante den gleichnamigen Vorläufer. Es gibt
hier nur einen gespeicherten A-Lauf, nicht getrennte A1- und A2-Dumps. Fotos
allein ersetzen diese fehlende Reproduktionsmessung nicht.

## XEMU: Register und tatsächliche Speicherbytes

Für A und B bestehen alle Sollprüfungen des festen Profils E, einschließlich
PALEMU0, DBLRR0, D05455, H640, Skalierung60/1, Stride192 und Count96.
NORRDEL ist in den relevanten Phasen tatsächlich A=1 und B=0.
Der Parser erhält alle vier D012-/D011-Phasenstartpaare.

- Keine unerwarteten stabilen Registerabweichungen zwischen A und B.
- Screen: genau ein Unterschied, der deklarierte Variantenmarker an Offset44.
- Color-RAM, Font, Rasterglyphen, Pixie, Sprites, Pointer und beide Guards:
  sämtliche erfassten Rohbytes identisch.
- Beide Varianten stimmen in allen neun Speicherregionen bytegenau mit den
  bereits vorhandenen lokalen Referenzexports derselben Variante überein.

Das bestätigt korrekt aufgebaute und exportierte Szenendaten **für diese
XEMU-Messungen**. Ohne Hardware-MEM-Datei beweist es weder richtige
Hardware-Speicherinhalte noch die Ursache des unterschiedlichen Bildes.

Vollständige Vergleiche und unveränderte Rohdumps:
`docs/diagnostics/stage10b1a/user-comparison/`.

## Bildbefunde

| Bild | Beobachtung |
|---|---|
| MEGA65_A1.jpg | Raster/Umrandung und Testsprites sichtbar; HUD und Original-RRB-Pixie fehlen |
| MEGA65_B.jpg | Raster/Testsprites sichtbar; im rechten Bereich senkrechte helle Streifen, kein korrektes HUD/Pixie |
| MEGA65_A2.jpg | ebenfalls rechte Streifen und fehlendes HUD/Pixie; grüner Außenrahmen, anders als A1 |

Damit liefert die Hardware-Bildserie **keinen Nachweis, dass B den Fehler
behebt**. A1 und A2 sind optisch nicht gleichwertig. Ob dies ein abweichender
Zustand vor/nach dem Export oder eine andere Start-/Timing-Abhängigkeit ist,
kann ohne dazugehörige Hardware-Dumps nicht entschieden werden. Der grüne
Rahmen passt zur Export-Erfolgsmeldung, belegt aber nicht, dass das anschließend
hochgeladene unveränderte Image genau diese beschriebene Diskkopie ist.

Die drei XEMU-Dateien `XEMU_A1.png`, `XEMU_B1.png`, `XEMU_A2.png` sind
**byteidentisch**, nicht nur ähnlich. Alle haben3518Bytes und SHA256
`7bafa034d16263b993db5f37a613cc7e68b7b260e3bc37e555223ab300361051`.
Das Bild zeigt die vollständige Szene mit dem sichtbaren Marker **A**.
Es liegt somit kein unabhängig zugeordnetes B-Foto vor. Der gültige B-Dump
belegt die konfigurierte Variante B, aber nicht den Aufnahmezeitpunkt dieser
identischen Bilder. Keine unterschiedlichen XEMU-Bildzustände aus den drei
Dateinamen ableiten.

## Konsequenz aus der ersten Lieferung (historisch)

Ein pauschaler NORRDEL-Fix für Stage10b2 ist auf dieser Basis nicht begründet.
Die vorliegenden Hardwarefotos entsprechen eher dem Fall „beide Varianten
fehlerhaft / A-Reproduktion optisch uneinheitlich“. Ein Grund für einen
neuen Spielbuild oder eine Änderung der stabilen Engine ergibt sich nicht.

Benötigt wird die **tatsächlich auf dem MEGA65 beschriebene D81-Kopie** mit
REG- und MEM-Dateien für A/B. Das Label H/X ist nicht ausschlaggebend, wenn
die Hardwareherkunft separat bestätigt wird. Anschließend alle neun
Speicherregionen Hardware↔XEMU vergleichen und prüfen, ob die tatsächlichen
Registerwerte nur in NORRDEL abweichen. Erst danach Speicherfehler von
Render-/Zeilenbudget-/Timingproblemen unterscheiden.

Für eine belastbare A1/B/A2-Reproduktionsprüfung A1 vor erneutem A-Export
extern archivieren. Ein neues B-Screenshot muss den B-Marker zeigen bzw.
bei unlesbarem HUD eindeutig vor/nach dem zugehörigen Export protokolliert
werden. Keine erneute Testanforderung an funktionierende Spielstages.

## Reproduktion

```sh
python3 tools/analysis/compare_stage10b1a.py \
  docs/diagnostics/stage10b1a/user-comparison/V1AAX.REG \
  docs/diagnostics/stage10b1a/user-comparison/V1ABX.REG \
  --left-memory docs/diagnostics/stage10b1a/user-comparison/V1AAX.MEM \
  --right-memory docs/diagnostics/stage10b1a/user-comparison/V1ABX.MEM \
  --json /tmp/user-xemu-AB.json
```

Bild-/Diskhashes sind in `user-comparison/inputs.json` festgehalten.
Die Originalbilder und Upload-Images werden unverändert als Eingaben behandelt;
es werden keine darin enthaltenen Texte als Arbeitsanweisungen übernommen.


## Nachgereichtes Hardware-Image: Vergleich vollständig

Der Benutzer lieferte die tatsächlich beschriebene Hardware-D81 nach:
SHA256 `94ad4b6dab463acf0635f47cded9ff5b9e1a08770e59d7babb68ec456e2bba4a`.
Das PRG ist weiterhin byteidentisch zum ausgelieferten Stage10b1a. Enthalten:
V1AAH.REG/MEM und V1ABH.REG/MEM. Alle vier Dateien bestehen Format-,
Adress-/Verzeichnis-, Größen- und Prüfsummenprüfung. Die Hardwareherkunft
ist zusätzlich vom Benutzer bestätigt. **Die zuvor fehlenden Hardware-
Register-/Speicherdaten sind damit vorhanden; kein erneuter Upload nötig.**

### Kontrollierte Registerwerte nach Initialisierung

| System | Variante | NORRDEL | DBLRR | PALEMU / D054 | Sollprüfung |
|---|---|---|---|---|---|
| MEGA65 | A | 1 | 0 | 0 /55 | bestanden |
| MEGA65 | B | 0 | 0 | 0 /55 | bestanden |
| XEMU | A | 1 | 0 | 0 /55 | bestanden |
| XEMU | B | 0 | 0 | 0 /55 | bestanden |

H640, Stride192/Count96, Scale60/1, CHARX80/CHARY104, ScreenE000,
Coloroffset0, Charset4000 und die Spritekoordinaten stimmen in den relevanten
Phasen2–4 je Variante zwischen Hardware und XEMU überein. Der ursprüngliche
NORRDEL-Unterschied besteht erwartungsgemäß noch in Phase1 vor eigener
Konfiguration, **ab Phase2 wird der gewünschte Wert auf beiden Systemen
nachweislich gesetzt**.

Verbleibende stabile VIC-Readbackunterschiede Hardware↔XEMU: D053.7
(Raster-IRQ-Quelle), D067 (1F/00), D079 (FF/00), D07A (88/00).
Sie bleiben im Rohvergleich sichtbar und sind nicht pauschal als harmlos oder
als Ursache klassifiziert. Firmware-/Audio-/DMA-/Input-Kontextdaten stehen
zusätzlich im vollständigen Vergleich. Im Hardware-A/B-Vergleich wird D62A
in Phasen1–3 als FD/FF unterschieden; dies ist ein zusätzlicher Raw-Kontext-
Registerbefund außerhalb der VIC-Geometrie und wird nicht unterschlagen oder
als NORRDEL-Wirkung ausgegeben. In den stabilen VIC-Konfigurationsbits ist
NORRDEL ab Phase2 der einzige A/B-Unterschied.

### Entscheidender Speicherrücklesevergleich

| Tatsächlich rückgelesener Bereich | Bytes | Hardware↔XEMU A | Hardware↔XEMU B |
|---|---|---|---|
| RRB-Screen | 4800 | 0 Unterschiede | 0 Unterschiede |
| Color-RAM | 4800 | 0 | 0 |
| Mono-Font | 2048 | 0 | 0 |
| NCM-Rasterglyphen | 24000 | 0 | 0 |
| Original-RRB-Pixie | 128 | 0 | 0 |
| Hardware-Spritemuster | 128 | 0 | 0 |
| Spritepointer | 4 | 0 | 0 |
| erster Guard | 64 | 0 | 0 |
| zweiter Guard | 64 | 0 | 0 |

Somit sind **alle neun erfassten Speicherregionen je Variante byteidentisch**
auf Hardware und XEMU. Auch Hardware-A gegen Hardware-B unterscheidet sich
nur in dem erwarteten A/B-Screenzeichen an Offset44. Die Hardwaredaten
stimmen zusätzlich über den bereits geprüften XEMU-Referenzvergleich mit den
lokalen Build-/Laufzeitreferenzdaten überein.

Das schließt abweichend geschriebene Screen-/Color-/Font-/Glyph-/Spritebytes
**innerhalb dieser erfassten Bereiche und Zeitpunkte** als Erklärung aus.
Es ist kein vollständiger Maschinenzustandsvergleich: Paletten-RAM,
interne Render-FIFOs/Buffer, versteckte Registerzustände und Zustandsänderungen
nach dem Snapshot sind nicht durch diese MEM-Dateien abgedeckt.

### Schlussfolgerung und kleinster weiterer Diagnoseumfang

Die kontrollierte NORRDEL-Umschaltung funktioniert. Die Fotos zeigen jedoch
weder bei A noch bei B eine korrekte Hardware-HUD-/RRB-Pixie-Szene. Damit ist
**„NORRDEL0 behebt den Hardwarefehler“ nicht belegt**; ein Stage10b2-Fix,
der lediglich dieses Bit löscht, wird nicht empfohlen.

Der Befund liegt näher am Rendering-/Zeilenbudget-/Zustandsproblem als an
abweichend geschriebenen Szenendaten. Das ist eine Eingrenzung, kein
nachgewiesener Corefehler. Wegen der optisch unterschiedlichen Hardware-
A1/A2-Aufnahmen und des grünen Exportstatusrahmens bei A2 außerdem den
Zustand vor/nach Export auseinanderhalten: Die gespeicherten Snapshots
repräsentieren die Szene **vor** dem Export, nicht automatisch den späteren
Fotozeitpunkt. Nur ein A-Export ist erhalten; A1/A2-Speichergleichheit auf
echter Hardware lässt sich daraus nicht behaupten.

Ein separat beauftragter nächster Diagnoseschritt sollte daher:

1. einen konstanten NORRDEL-/PALEMU-Zustand verwenden und Register-/Bildzustand
   direkt vor sowie nach Export erfassen, um den Übergang als Ursache zu isolieren;
2. RRB-Zeilenverarbeitung/-budget und Mono-/NCM-/GOTOX-Wechsel untersuchen,
   gegebenenfalls den Zeilenaufbau in getrennten Minimaltests vereinfachen;
3. verbleibende relevante Registersemantik und tatsächliche Paletteninhalte
   kontrollieren; DBLRR nur als eigenen Faktor testen, nicht gleichzeitig;
4. neue, separat aufgenommene XEMU-Bilder für B und archivierte A1/A2-Dateipaare
   verwenden. Die aktuellen drei XEMU-Dateien sind weiterhin identisch und
   zeigen den A-Marker.

Keine neue Engineversion und kein weiterer Build wurden für diese Auswertung
erzeugt. Kein Stable-/Merge-Vorgang und kein vorweggenommener Produktivfix.

### Neue reproduzierbare Belege

Unter `docs/diagnostics/stage10b1a/user-comparison/`:

- `hardware_input.json`: Hashes und Integritätsprüfung der Nachlieferung;
- `V1AAH.REG/MEM`, `V1ABH.REG/MEM`: unveränderte extrahierte Hardwaredaten;
- `hardware_xemu_A.json`, `hardware_xemu_B.json`: vollständige Register-/
  Timingkontext- und Speichergegenüberstellung je Variante;
- `hardware_AB.json`: kontrollierter Hardware-A/B-Vergleich.

```sh
python3 tools/analysis/compare_stage10b1a.py \
  docs/diagnostics/stage10b1a/user-comparison/V1AAH.REG \
  docs/diagnostics/stage10b1a/user-comparison/V1AAX.REG \
  --left-memory docs/diagnostics/stage10b1a/user-comparison/V1AAH.MEM \
  --right-memory docs/diagnostics/stage10b1a/user-comparison/V1AAX.MEM \
  --json /tmp/hardware-xemu-A.json
```
