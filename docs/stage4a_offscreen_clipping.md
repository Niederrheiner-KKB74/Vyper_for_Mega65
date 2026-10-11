# Stage 4a – Offscreen-Einflug und Clipping

Status: Entwicklungsstand, **nicht Stable**. Grundlage ist der unveränderte,
annotierte Tag `stage3b5c-stable`, Commit
`1e0d1a7537d9b55d105442d8736d07cf5778272a`. Auftrag: [Issue #10](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/issues/10).
Stage 4a enthält keine originalen Einflug-/Angriffskurven und keinen Levelwechsel.

## Ist-Analyse vor der Integration

Die Quellen `src/engine/stage3b5c.asm`, `_hud.asm`, `_game.asm`, `_shots.asm`
bleiben erhalten. Ihre entsprechenden Stage-4a-Kopien behalten sämtliche alten
Symboladressen. Der Build vergleicht das neue PRG byteweise mit dem stabilen PRG
(SHA256 `2de5edcc91b8d4a24afb7ec427b89ca0b17cbe4841b5cb5d9fe2c0a6f5f62d04`).
Er erlaubt sechs JSR-Zieländerungen, zehn gezielt geprüfte Zeilenbereich-Patches
für die freigegebenen Randzeilen und drei zuvor vollständig
nullbelegte Codebereiche sowie die private Erweiterung um 256 Grafikbytes.

Quellstellen der stabilen Engine (Symbolnamen sind in Stage 4a gleich):

| Bereich | Quelle / Befund |
| --- | --- |
| Hauptschleife | `stage3b5c.asm:main_loop`, Rasterzeile 250 abwarten; Bewegung/Animation/Render im Hauptprogramm, kein neuer IRQ |
| RRB-Listen | `v012a_screen_lo/hi`, 25 Zeilen × 128 Bytes, dynamische Liste ab Byte 84 |
| Zeilen löschen | `s2ia_clear_row`, 36 Screenbytes + bewährte Color-DMA; alte Einträge verschwinden vor jeder Ausgabe |
| Pixie zerlegen | `v014_submit_pixie`, Y/8 und Y mod 8; zwei NCM-Zeichen plus transparenter Folgeguard bei Subzeilenversatz |
| Zulässige Zeilen | `v014_append`, ausschließlich Zeilen 2–22; maximal acht Pixies pro Zeile |
| X kodieren | `stage3b5c_hud.asm:hud_write_x`, logisches Byte X verdoppeln und Carry als GOTOX-Bit 8 verwenden |
| RRB ausgeben | `v014_write_slot`, GOTOX + NCM-Glyph; Color-Attribute `$90,$00` / `$08,$00` |
| Renderzustände | `stage3b5c_game.asm:c_render`, Player + 22 Pfadgegner + Orbit, Explosionen/Unsichtbarkeit; Abschlussmarker |
| Animation | `s3b2.animate`, geprüfte DMA-Framekopie nach `$9840`; Typ 15 hat sechs Frames |
| Paletten | `s3b3.player_write_slot`, Player selektiert alternative Palette; normale Gegner-/Crop-Glyphen bleiben auf Gegnerpalette |

Die tatsächliche stabile Engine hat **24 RRB-Objekte insgesamt: 23 Gegner und einen
Player**, entgegen der Formulierung „24 Gegner + Player“ im Issue. Stage 4a erhöht
oder reduziert diese Baselinezahl außerhalb des isolierten Tests nicht.

### Drei verschiedene Grenzen

- Hintergrund/Textfläche: 320×200 logische Pixel, H640 mit `CHARXSCALE=60`;
  logisches X wird zu zwei nativen horizontalen Pixeln.
- Bisheriger aktiver Pixie-Bereich: **`[0,240) × [16,184)`**, also X 0–239,
  Y 16–183. Die Y-Grenzen folgen direkt aus den vorhandenen Zeilen 2–22.
  Y 0–15 und 184–199 gehören zum schwarzen Rand der Bildschirmfläche;
  Die Erweiterung vom 11.10.2026 nutzt dagegen **alle Zeilen 0–24**, also
  **`[0,240) × [0,200)`**. Die rechte Grenze liegt weiterhin bei nativ X=480;
  dahinter beginnt das HUD mit 160 nativen Pixeln Breite.
- VIC-IV-Hardwareborder: äußere Bildgrenze. Die HUD-Trennlinie ist **keine**
  Hardware-Clipping-Grenze. Spritekoordinaten verwenden zusätzlich den aus
  `$D04C–$D04F` gelesenen nativen Ursprung; RRB-Koordinaten nicht.

Die Originalroutine nimmt **Bytekoordinaten**, keine signed Positionen entgegen.
X=-1 als Byte $FF würde nach Verdopplung bei logisch 255 / nativ 510 und damit im
HUD erscheinen. Y=-1 wird zu $FF, Zeile 31, und verworfen; bei größerem positivem Y
kann durch Abschneiden auf ein Byte eine falsche sichtbare Zeile entstehen. Die
Zeilenprüfung verhindert manche ungültigen Schreibzugriffe, stellt aber kein
pixelgenaues Clipping oder signed Offscreen-Modell bereit. An der rechten Kante
würde ein vollständiger Glyph über X=240 hinwegzeichnen. An den Y-Kanten entfernt
die alte Zeilenprüfung nur ganze 8-Pixel-Zeilen.

### VIC-IV-Referenz und Grenzen der Aussage

**Im Repository ist keine Chipset-Referenz/PDF vorhanden.** Deshalb werden keine
zusätzlichen Registerfähigkeiten aus einer vermeintlich vorhandenen Referenz
behauptet. Die tatsächlichen Enginequellen werden ergänzend mit der lokal
verfügbaren XEMU-Implementierung verglichen, Commit
`40dfef0d1d5f56be2469492715c12bdb32c75b67`:

- [GOTOX und Subzeilenoffset](https://github.com/lgblgblgb/xemu/blob/40dfef0d1d5f56be2469492715c12bdb32c75b67/targets/mega65/vic4.c#L1535):
  10-Bit-X, besondere Interpretation großer X-Werte, kein Clip an der HUD-Grenze.
  Der bisherige Byte-X-Pfad kann daraus keine sichere negative Position bilden.
- [NCM-Nibbles und Transparenz](https://github.com/lgblgblgb/xemu/blob/40dfef0d1d5f56be2469492715c12bdb32c75b67/targets/mega65/vic4.c#L1356):
  gerader Pixel im unteren Nibble, ungerader im oberen; Null ist bei den
  vorhandenen GOTOX-Attributen transparent.
- [Glyph-/Zeilenadressierung](https://github.com/lgblgblgb/xemu/blob/40dfef0d1d5f56be2469492715c12bdb32c75b67/targets/mega65/vic4.c#L1588):
  `glyph*64 + (Zeilenpixel + Subzeilenoffset)*8`, daher Leading-/Trailing-Guards.

Diese Implementierungsreferenz und die CPU-/Fetch-Tests ersetzen keine XEMU-
Sichtprüfung oder normative Hardwarebeschreibung. Stage 4a verwendet **keine
neuen VIC-Register oder unbestätigten Hardware-Clippingfunktionen**.

## Lösung und mathematisches Modell

`src/engine/stage4a_offscreen.asm` kapselt die Erweiterung. X/Y sind unabhängige
signed 16-Bit-Wörter. Für 16×16 gelten die exklusiven Schnitte:

```
left=max(x,0)     right=min(x+16,240)
top=max(y,0)      bottom=min(y+16,200)
```

Ein leerer Schnitt erzeugt **keinen Pixie-RRB-Eintrag**. Die Listen werden trotzdem
vorher gelöscht und abgeschlossen. Die logische Bewegung läuft weiter.
Vollständig sichtbare Pixies nutzen die ursprünglichen Glyphen `$261–$263` ohne
Grafikkopie. Teilweise sichtbare Pixies erhalten einen privaten transparenten
16×16-Puffer: nur der sichtbare Ausschnitt wird aus der Originalgrafik `$9840`
kopiert und bei `(left,top)` verankert. Alle anderen Zielpixel werden Null.
Der Crop berücksichtigt ungerade Nibble-Offsets und alle vier Kanten/Ecken.
Die ursprüngliche Position bleibt unverändert; nur die Renderposition wird begrenzt.

`r_clip_axis` berechnet die Entscheidung ohne ein überlaufendes signed `x+16`:
Position relativ zum Minimum, negative Differenzen -15 bis -1 separat behandeln,
alle anderen negativen/zu großen Werte verwerfen. Die Tests umfassen auch
INT16_MIN/INT16_MAX und Werte jenseits eines Bytebereichs. Keine Adresse wird aus
einer negativen Position erzeugt. CPU-Code liest keine Cropdaten unter BASIC-ROM;
er schreibt ausschließlich `$CA40–$CABF`, die der VIC als physisches RAM liest.

**Pixelgenaues Clipping ist damit im Software-/RRB-Fetch-Modell nachgewiesen.**
Es erfordert keinen Architekturwechsel: dieselben 25 bereits reservierten Zeilenlisten, Glyphformate,
Paletten, DMA-Listen, GOTOX-Routinen und Abschlussmarker bleiben bestehen.
Es ist kein Übermalen außerhalb des Spielfelds. Die verworfenen Pixel fehlen
bereits im transparenten Glyph. Guards verhindern den Subzeilen-Fetch in fremde
Grafiken. Originaldaten, gemeinsame Framepuffer, Player und Explosionen bleiben
unverändert.

## Isolierter Modus und Bedienung

D81 `releases/stage_4a/VYPER_STAGE4A.d81` einlegen, dann:

```basic
LOAD "STAGE4A",8
RUN
```

Standard ist das unveränderte Gameplay. **F** aktiviert/deaktiviert den Test,
ausschließlich bei aktivem Player (nicht während Explosion, Respawn oder GAME OVER).
Im Test wird genau ein Original-Typ-15-Gegner gezeigt; übrige Objekte, Projektile,
Kollisionen, Treffer, Punkte und Lebensverwaltung sind eingefroren. Hardware-
Sprites sind ausgeblendet, ihre Kanalzustände werden erhalten. Beim Verlassen
läuft der ursprüngliche Framekoordinator weiter und baut die normalen Listen neu.
Die sechs Originalframes laufen auch während des Clippings mit ursprünglichem
Animationstakt. Space / + / - behalten ihre bisherige Animationsfunktion.

| Taste | Verhalten im Test |
| --- | --- |
| F | zurück zum normalen Gameplay |
| N | nächster Fall, Start vollständig außerhalb |
| P | Bewegung pausieren/fortsetzen; Animation läuft weiter |
| X | ursprünglicher sauberer BASIC-Exit |
| T / E | im Test ohne Aktion, damit die eingefrorenen Gameplay-Testzustände erhalten bleiben |
| R | keine Aktion im Test; außerhalb bleibt GAME-OVER-Neustart unverändert |
| Joystick / Feuer | nur außerhalb des Tests aktiv, dort unverändert |

Die fünf Fälle laufen automatisch endlos, mit **einem logischen Pixel pro
50-Hz-Frame**. Start und Ende bleiben mindestens einen Frame vollständig unsichtbar.

| Fall | Start | Ende | Bewegung |
| --- | --- | --- | --- |
| oben | (112,-16) | (112,200) | Y +1 |
| unten | (112,200) | (112,-16) | Y -1 |
| links | (-16,92) | (240,92) | X +1 |
| rechts / neben HUD | (240,92) | (-16,92) | X -1 |
| diagonal oben links | (-16,-16) | (240,240) | X +1, Y +1 |

Beim diagonalen Fall ist der Pixie nach dem unteren Austritt weiter logisch
beweglich bis Y=240; zusätzliche CPU-Tests prüfen auch Y=256 gegen
Wraparound auf Zeile 0.
Kein Debugtext wird während der Darstellung oder in IRQs ausgegeben.

## Speicher und Diagnose

| Bereich | Stage-4a-Verwendung |
| --- | --- |
| `$1D00–$1D3F` | vorher freier Arbeitsbereich; bei Programmstart genullt |
| `$4E30–$4EFE` | Modus-/Keyboard-/RRB-Hook |
| `$8660–$874A` | isolierte Bewegung und Framehooks |
| `$8E20–$8F7D` | signed Clipping und transparenter NCM-Crop |
| `$CA00–$CAFF` | privater Guarded-Glyph; `$CA00–$CA3F` Blank, `$CA40–$CABF` Crop, `$CAC0–$CAFF` Blank |

Die vollständige Belegung einschließlich sämtlicher geerbter Bereiche steht in `releases/stage_4a/memory-map.txt`. PRG-Ende `$CAFF`,
256 Bytes größer als Stable. Keine belegte Baselinefläche wird umgewidmet.
Keine neuen Zero-Page-Adressen, Hardware-Sprite-Kanäle oder DMA-Listen.
Loaderpuffer `$6800/$6900`, Levelkopie, Datenspeicher `$40000/$54000`,
Color-Backup `$6B00` / `$9000`, `$1000–$15FF` KERNAL-Arbeitsbereich und
`$20000–$3FFFF` ROM-Bereich bleiben getrennt/unberührt.

| Adresse | Diagnose (Byte, soweit nicht anders angegeben) |
| --- | --- |
| `$1D00 / 01 / 02 / 03` | Test aktiv / Pause / Fall 0–4 / Starthalteframe |
| `$1D04–05 / 06–07` | X / Y, WORD LE signed |
| `$1D08 / 09` | sichtbare linke / obere Renderposition |
| `$1D0A / 0B` | Quell-X / Quell-Y des Schnitts |
| `$1D0C / 0D` | sichtbare Breite / Höhe; bei leerem Schnitt kann nur eine davon Null sein |
| `$1D0E` | 0 unsichtbar, 1 originaler Glyph, 2 Crop |
| `$1D10–$1D1E` | interner Clip-/Crop-/Keyboard-Arbeitsbereich |

Das sichtbare Rechteck lautet `(draw_x,draw_y,draw_x+width,draw_y+height)` bei
Entscheidung !=0. Bei Entscheidung 0 existiert kein sichtbares Rechteck.
RRB-Zeile `draw_y>>3`, Subzeilenoffset `draw_y&7`, erster Listenoffset
`$5000 + Zeile*128 + 84`; `v014_row_count` und `v014_overflow_count` sind weiterhin
an den Symboladressen des stabilen Renderers verfügbar. Maximal ein Pixie pro
Testzeile gegenüber acht verfügbaren Slots. Abschlussmarker passen weiterhin
in die 36 dynamischen Bytes je Zeile; keine Prefix-/HUD-Zellenschreibzugriffe.

## Performance und Empfehlung für Stage 4b

Kein zusätzlicher IRQ, keine Disk-I/O pro Frame, kein Crop bei vollständig
sichtbaren/unsichtbaren Pixies. Ein Teil-Crop schreibt genau 128 Bytes und
verarbeitet 256 Pixel; nur ein privater Ausschnitt pro Testframe. Messung der
realen assemblierten Routinen im py65-NMOS-Instruktionsmodell:

| Position | Clip-Zyklen | Crop-Zyklen |
| --- | ---: | ---: |
| (-16,92), unsichtbar | 283 | 0 |
| (112,92), vollständig | 328 | 0 |
| (-1,92), 15×16 sichtbar | 322 | 30959 |
| (-15,-15), 1×1 sichtbar | 323 | 15018 |
| (239,199), 1×1 sichtbar | 319 | 15013 |

Das sind **keine gemessenen 45GS02-/XEMU-Framezeiten**. DMA-Stalls, echter VIC-Fetch
und Maschinen-/Emulatortakt sind darin nicht bewertet; die stabile 50-Hz-Ausgabe
muss in XEMU unter dem bisherigen schnellen CPU-Modus geprüft werden. Der
Crop ist bewusst einfach; größere Mehrgegner-Last ist nicht Bestandteil dieses
Nachweises. Für Stage 4b: dasselbe signed Positions-/Schnittmodell übernehmen,
pro gleichzeitig teilgeclipptem Gegner einen eigenen Guarded-Crop reservieren
oder einen nachgewiesen ausreichend großen Pool nutzen. Keinen gemeinsamen
Crop während des VIC-Fetch für mehrere Pixies überschreiben. Bei Bedarf später
byteweise Kopie mit Nibble-Shifts und Frame-/Schnitt-Caching optimieren; zuvor
Worst-Case-Last mit mehreren Randgegnern auf XEMU/Hardware messen.
Alternative größere Lösungen wären Rowmask-/Tilezerlegung oder Rasterclip;
sie sind hier nicht erforderlich und nicht implementiert.

## Reproduzierbarer Build und automatische Prüfung

Voraussetzungen wie bei Stable: Python 3, Java, offizieller KickAssembler 5.25
mit dem vom Builder geprüften SHA256. py65 1.2.0 wird nur für CPU-Tests benötigt.
Der Builder nutzt ausschließlich Originalassets aus dem Repository/Originalarchiv,
prüft DAT-/Player-/Explosionsdaten und erstellt die vollständige Disk ohne c1541.

```sh
python3 tools/build_stage4a.py --kickass /pfad/zu/KickAss.jar
PYTHONPATH=tests python3 -m unittest test_stage4a -v
# Optional tatsächliche bereitgestellte ROM-Blinkroutine mitprüfen:
MEGA65_ROM=/pfad/zu/MEGA65.ROM PYTHONPATH=tests python3 -m unittest test_stage4a -v
# Zweitbuild in anderes Verzeichnis, SHA256SUMS und Dateien vergleichen:
python3 tools/build_stage4a.py --kickass /pfad/zu/KickAss.jar --output /tmp/stage4a-rebuild
```

Aktualisiert und ausgeführt am 11.10.2026 im Cloud-Host:

- KickAssembler 5.25 erfolgreich; PRG **43.777 Bytes**, Load $2001 bis $CAFF.
- **21/21 Tests bestanden**: bestehende Suite 20/20 in 101,112 Sekunden plus
  zusätzlicher Normalrenderer-Randzeilentest 1/1 in 4,382 Sekunden. Optionaler ROM-Test mit dem
  bereitgestellten V920395 tatsächlich aktiviert. Das ROM wird nicht verteilt.
- 1.849 signed Rechteckschnitte inkl. INT16-Extremen, 780 Vergleiche tatsächlich
  gefetchter RRB-Pixel (130 Kanten-/Eckenpositionen × sechs Originalframes),
  Crop-Nibble-Reihenfolge/Transparenz/Guards, HUD-/System-/Grafikschutz.
  Normalrenderer zusätzlich bei Y=0, 15, 184 und 199 direkt geprüft.
- 2.600 Bewegungsupdates umfassen mindestens zwei vollständige Fünffallzyklen;
  Start/Ende, Kontinuität, unsichtbare Bewegung und Extremkoordinaten geprüft.
- F/N/P, eingefrorene Spielzustände einschließlich ignorierter T/E-Tasten,
  sechs weiterlaufende Animationsframes, Test verlassen, X und zweiter RUN.
- Geerbte 14 Gameplayprüfungen: Loader, korrekte Originalgrafiken/Bewegung,
  Softwarekollisionen, unabhängige sieben Originalexplosionsframes, Punkte,
  Highscore, Leben, steuerbarer 150-Tick-Respawn, GAME OVER/R und Fehler-Exit.
- Sechs Hooks, zehn eng begrenzte Zeilenbereich-Patches und drei freie Codebereiche; alle alten Symbole erhalten.
  Die sechs stabilen Quellen und sämtliche stabilen Releases bleiben unverändert.
- **Alle 14 Release-Dateien byteidentisch** beim unabhängigen Zweitbuild.
- D81 **819.200 Bytes**, PRG/SEQ-Dateitypen, BAM, Dateiketten, Originaldateigrößen,
  Signaturen und SHA256 geprüft.

Finale SHA256:

```
PRG 3da4cf49117ad07ac630dfad10ec30407ff62bc6e5051eac3c974bd8c5d002e2
D81 a608d67994b26100295f38f4ee9821e90ddde6e8763daee35ec293d51954df54
```

Tests sind CPU-/DMA-/RRB-Fetch-Modelle, **kein XEMU-Lauf**.

## XEMU-Abnahme – noch ausstehend

ROM V920395, BASIC 80×25 wie bei Stable. Mindestens zwei komplette Testschleifen:

1. Laden/Originaldatenprüfung erfolgreich, außerhalb F dieselben Grafiken,
   Bewegung, Joystick, zwei Player-/vier Gegnerschüsse und Kollisionen.
2. F: ein Typ-15-Gegner; bei allen vier Richtungen erst einzelne sichtbare Pixel,
   dann gesamter Pixie, danach entsprechend abgeschnitten und unsichtbar.
3. Rechter Rand: keinerlei Pixel/Schriftverschiebung im HUD. Oberer/unterer Rand:
   pixelgenaue Ausgabe bis Y=0 beziehungsweise Y=199,
   kein Zeichnen außerhalb Y=0–199, keine Spuren/Wraparound.
4. N bis Diagonale: Ecke korrekt, Animation durchgehend sechs Frames,
   Endposition vollständig unsichtbar, mehrere Durchläufe ohne Störungen.
5. P pausiert Bewegung; Animation bleibt erkennbar. F zurück: Gameplay,
   Projektile, Score/Leben und Player unverändert funktionsfähig.
6. X aus einem partiell sichtbaren Testfall: normaler BASIC-Screen und Cursor;
   erneut RUN bzw. laden/starten funktioniert. Mehrfach wiederholen.
7. Außerhalb F letztes Leben verlieren: sieben Originalexplosionsframes, GAME
   OVER, andere Tasten ohne Aktion, R Neustart mit erhaltenem Highscore, X Exit.

XEMU-/Hardwareerfolg sowie stabiles 50-Hz-Timing sind **noch nicht bestätigt**.
Stage 4a erhält keinen Stable-Tag vor ausdrücklicher Benutzerfreigabe.

## Erweiterung vom 11.10.2026: volle Bildschirmhöhe

Der Benutzer hat die bisherige Stage-4a-Clippingdarstellung unter XEMU als
fehlerfrei bestätigt und anschließend die Freigabe für Y=0–15 und Y=184–199
beauftragt. Die neue Version nutzt sämtliche 25 bereits vorhandenen RRB-Zeilen.
Initialisierung, Löschen und Abschlussmarker umfassen nun 0–24; `v014_append`
verwirft nur Zeilen >=25. Die entfallene Untergrenzenprüfung wird durch vier
NOPs ersetzt, sodass sämtliche nachfolgenden Symboladressen unverändert bleiben.
Die Test-Schnittgrenzen und vertikalen Start-/Endpositionen folgen dem neuen
Bereich; X-Grenze 240, Geschwindigkeit, Animation und Tasten bleiben gleich.
Player-Bewegungsgrenzen, Flugbahnen, Projektil-/Kollisionslogik, HUD und alle
Register-/Speicherparameter werden nicht verändert. Insbesondere wächst das
PRG nicht weiter. Die zusätzliche Zeilenarbeit im Renderer ist in XEMU erneut
auf Timing und sauberen Exit zu prüfen.

Die vorherige Benutzerabnahme gilt für den älteren eingeschränkten Bereich;
die **erweiterte** Version benötigt eine neue XEMU-Abnahme und bleibt nicht Stable.
