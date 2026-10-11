# Stage 3b-4a – Diagnose von Hintergrund, Pixie-Spuren und Schrift

Der Benutzer-XEMU-Test der ersten Fassung (`41b6afe`) zeigt BASIC-Inhalte und blauen
Hintergrund während des Spiels, kumulative Pixie-Spuren und rechteckige/verschmolzene
HUD-Buchstaben. Player-Grafik und Bewegungssteuerung sind weiterhin grundsätzlich
funktional. Stage 3b-3 ist stabil und bleibt unverändert.

## Nachgewiesene Ursachen

In Stage 3b-3 beginnt jede Zeile mit deckenden leeren NCM-Glyphen. Für den ersten
HUD-Build wurden sie durch ausschließlich rechts positionierte HUD-Einträge ersetzt.
Die beweglichen Pixies verwenden GOTOX mit Attribut `$90` (transparent), damit schwarze
Glyphenpixel andere Pixies nicht verdecken. Ohne vorherige Hintergrundfüllung werden
vom Renderer übersprungene Bereiche und transparente Nullpixel nicht neu gezeichnet.
Das persistente XEMU-Ausgabebild behält BASIC- oder Pixie-Pixel des vorherigen Rasters.
Screen-/Color-Slots zu löschen ist allein keine Raster-Hintergrundfüllung.

Beleg in XEMU `targets/mega65/vic4.c`: `vic4_render_char_raster()` repositioniert
`current_pixel` bei GOTOX, ohne den übersprungenen Bereich zu füllen. Vertical-Flip
im GOTOX (`$80`, insgesamt `$90`) schaltet `enable_bg_paint` aus. Der NCM-Renderer
zeichnet Nullpixel bei ausgeschalteter Hintergrundfüllung nicht. Die stabile Engine
lieferte deshalb zuerst die deckenden Leer-Glyphen.

Die HUD-Font-Routine der ersten Fassung fasste acht Originalspalten paarweise per OR
auf vier zusammen. Beim H wurden so Lücke und Querbalkendetails zerstört; zusätzlich
wurden die Glyphen auf vier Spalten getrimmt. Das ist ein tatsächlicher Verlust von
Schriftinformation. Eine Farbänderung oder bloßes Löschen des BASIC-Screens kann
keinen dieser beiden Renderer-/Fontfehler beheben.

Der erste Host-Rastertest legte jede Zeile neu schwarz an. Damit waren sowohl
übersprungene Bereiche als auch transparente Pixel implizit bereits gefüllt. Dieser
Test konnte den Fehler nicht entdecken und wurde entsprechend korrigiert.

## Korrektur

- BASIC-Screen vor dem unveränderten SEQ-Loader durch KERNAL-CHROUT `$93` leeren.
  Hintergrund auf Schwarz setzen, ursprüngliche BASIC-Farbe sichern und bei normalem
  Exit sowie Ladefehler restaurieren.
- Zeilen von 40 auf 64 SEAM-Einträge / von 80 auf 128 Bytes erweitern. Zuerst GOTOX 0
  plus 20 deckende schwarze NCM-Glyphen über volle 640 native Pixel, danach der
  permanente HUD-Prefix, danach unverändert acht bewegliche Slots plus Endmarker.
- Schriftbitmap unverändert aus dem tatsächlichen BASIC-Charset kopieren. Kein OR,
  kein Trimmen der Schrift. Rahmen dürfen schmale eigene Monozeichen verwenden.
  FORMATION und 100 stehen wegen der vollständigen Schrift jetzt in zwei Zeilen.
- 24 historische feste Screen-Stores und den alten Capture-Aufruf deaktivieren.
  Diese ungenutzten statischen Pixie-Slots lagen nach der Zeilenvergrößerung teils
  im HUD. Framezähler und die aktive Pixie-Animation bleiben erhalten.
- Spritepointer nach `$5C80` verlegen, damit sie nicht im erweiterten Screen liegen.
  Physische Color-RAM-Zugriffe für 3200 Byte mit gesichertem B/Z/Flags und IRQ-Maske;
  keine KERNAL-Zero-Page verwenden. Dynamisches Color-Clearing per F018A-COPY.
- Alle 3200 berührten Color-RAM-Bytes vor dem ersten Engine-Schreiben sichern;
  zusätzliche 1152 Byte im leeren PRG-Bereich `$6B00–$6F7F`. Beim Exit alles
  restaurieren, ebenso zusätzliches `$D05A`, ursprünglicher Hintergrund und alle
  bisher restaurierten VIC-/Charset-/Palette-/Screen-Register.

Dies behebt die Ursache in der RRB-Pipeline. Es wird kein Cursorartefakt übermalt
und kein BASIC-Syntaxfehler als Reparaturschritt erzeugt. Joystick, Gegnerpfade,
Originalglyphen, Originaldateien und SEQ-Loader bleiben erhalten.

## Automatische Prüfung und deren Grenze

**54 Tests bestanden:** 43 stabile Regressionstests plus elf HUD-/Exit-Tests.
Der neue Test beginnt mit einem blau gefüllten Ausgabebild, übernimmt danach
vorherige Frame-Pixel und vergleicht zwölf bewegte Frames mit einer frisch
gezeichneten Referenz. Entfernt man die deckende Füllung wieder, bleiben die
blauen Pixel reproduzierbar stehen. CIA1 und physischer Color RAM werden separat
modelliert: Joystick-Register `$DC00` bei ausgeschaltetem CRAM2K ist kein Schreibzugriff
auf Color-RAM-Offset `$400`.

Zusätzlich: alle acht Original-Lebenssymbole samt 1-Pixel-Abständen und Clamping;
56 Frames gegen 3b-3 mit identischen Objekt-, Phasen-, Framezähler- und Grafikdaten;
komplette Schriftbitmaps; Zahlen bis zum 32-Bit-Maximalwert; keine unnötigen HUD-
Schreibzugriffe; P/S und Player 2 inaktiv; Font-DMA-Aliase; B/Z/A/X/Y/Flags und
Zero-Page-Erhaltung; normale und fehlerbedingte BASIC-Rückkehr; zweimaliger Neustart
mit unveränderten VIC-Registern, 3200 Color-RAM-Bytes (auch ungleichmäßig initialisiert),
ROM-Palette und KERNAL-/Cursor-RAM. Die echte V920395-Cursorroutine wird ebenfalls
im vorhandenen CPU-Adapter ausgeführt.

KickAssembler 5.25, Originaldaten-/D81-Dateiketten-/BAM-Prüfung bestanden;
Wiederholungsbuild byteidentisch. Hostmodelle sind kein eigener vollständiger XEMU-Lauf.
Bitte die korrigierte D81 unter XEMU mit ROM V920395 erneut prüfen: schwarzer, leerer
Start; alle Pixies ohne Bewegungsspuren; lesbare HIGH-SCORE-/Score-/Level-Schrift;
Leben, Joystick, Animation und Performance; mehrfach X mit normalem BASIC/Cursor;
anschließend erneutes LOAD/RUN. Keine stabile Freigabe vor Benutzerbestätigung.

## Artefaktvergleich

Gegenüber der vom Benutzer getesteten ersten Stage 3b-4a (`41b6afe`):
**4097 geänderte PRG-Bytes**. Gegenüber stabiler Stage 3b-3: **3287 Bytes**,
auf exakt deklarierte Hooks/Zeiger/NOPs und freie neue Bereiche begrenzt. PRG weiterhin
43.521 Byte, D81 weiterhin 819.200 Byte. Alle älteren Release-Dateien bytegleich.

| Artefakt | Erste Stage 3b-4a SHA-256 | Korrigierte Fassung SHA-256 |
| --- | --- | --- |
| `STAGE3B4A.PRG` | `eb4eb72afa0819c861c6f07c2ae62aa827e0700e684aeb6e845643c0a4b04929` | `53a42e6994dcb73157ec9be78f33daba0cafad0bb66bcf72874e8bb85634b9e7` |
| `VYPER_STAGE3B4A.d81` | `601c66ae99743b35afbab1a08d86fb5e78687db631aa0a0ed5efc336e85d5afc` | `465cd7db4b4e21c6c18ea0ab0b2ddf152d61f89b07b75b04bcccd5fa4c98d0ea` |

[Technik/Build und XEMU-Checkliste](stage3b4a.md).

## Anschließende bestätigte Basis und Schriftanpassung

Der oben verglichene Build `9b2e767` wurde anschließend vom Benutzer als voll funktional
bestätigt. Der Artefaktvergleich dokumentiert diese Fehlerkorrektur historisch; die
aktuellen Release-Prüfsummen stehen in `releases/stage_3b4a/SHA256SUMS.txt`.
Auf Wunsch folgen kürzere gerahmte Texte und eigens erstellte dünne 5×7-Glyphen.
Details und aktuelle Speichergrenzen: [Stage 3b-4a](stage3b4a.md). Die neue Schrift
wird ausschließlich in der privaten Fontkopie ersetzt; BASIC/WOM bleiben erhalten.
