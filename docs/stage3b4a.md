# Stage 3b-4a – HUD rechts neben dem stabilen Spielfeld

Implementiert [Issue #4](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/issues/4)
im Branch `stage3b-4a`, Basis `stage3b3-stable` (`bb557e1995b4ec65730360fe28a38b4b3050001c`).
Stage 3b-3 einschließlich Release und Stable-Tag bleibt unverändert. **XEMU-Abnahme offen;
Stage 3b-4a ist noch nicht stabil.** Die Amiga-HUD-Referenz wurde vom Benutzer im
Gespräch bereitgestellt; sie ist kein bereits im Repository vorhandenes Bildasset.

## Vorprüfung und freigegebene Breite

Die Baseline verwendet H320, CHR16/SEAM, NCM, 25 Zeilen, 40 Einträge/80 Bytes
pro Zeile und Rasterzeile 250 als 50-Hz-Synchronisation. Screen `$5000–$57CF`,
Color-Vorlage `$6000–$67CF`, Color-RAM `$D800–$DFCF`; BASIC-Farbsicherung
`$9000–$97FF`. Der Renderer löscht nur Bytes 42–77 und setzt seinen Endmarker
in diesen acht dynamischen Slots. Bytes 0–41 können dauerhaftes HUD tragen.

Die ursprünglich freien 64 H320-Pixel reichen nicht für vier 16-Pixel-Schiffe
plus Abstände und Rahmen. Der Benutzer hat Variante 2 (angepasste Videoausgabe)
freigegeben und die Spielfeldgrenze X=240 vorgegeben. **H640 mit CHARXSCALE=60**
erhält die bisherige sichtbare Pixie-Breite: NCM-Pixel bleiben horizontal zweifach.
Der Writer verdoppelt die logischen GOTOX-X-Werte einschließlich Carry nach Bit 8;
Y-Offset, Attribute, Glyphen und Objektkoordinaten bleiben erhalten. Das HUD belegt
H640-X=480–639, entsprechend bisherigen X=240–319. Der Endmarker ist jetzt X=640.
Die ursprünglichen Gegner-/Orbit-Tabellen reichen nur bis X=170; mit 16 Pixel
Glyphenbreite bleiben sie innerhalb X=240. Der Builder prüft diese Grenze für
alle 256 Tabellenwerte. Der Joystick-Spieler bleibt bei X=32–224, rechts ebenfalls
224+16=240. Keine Pfadänderung, keine Kompression der Bewegungskoordinaten.

## Layout, Schrift und Palette

| Zeilen (je 8 Pixel hoch) | Inhalt |
| --- | --- |
| 0–2 | HIGH SCORE, sieben Ziffern, Rahmen |
| 3–5 | PLAYER 1 gelb, Score rot, LEVEL blau |
| 6–12 | Lebensfeld, drei Leben als Startwert |
| 14–16 | PLAYER 2, Score/Level ausgeblendet durch Striche, alles gedimmt |
| 17–22 | Inaktives Player-2-Lebensfeld mit roten P/S/X-Hinweisen und `P/S NOT ACTIVE` |
| 23–24 | FORMATION 100 / ATTACK 115, statische Referenz-Testwerte |

Die acht Plätze sind **4 Spalten × 2 Reihen**. In bisherigen Pixelkoordinaten:
X=245,262,279,296; Y=58,75. Jeder Platz ist 16×16; zwischen Schiffen liegt genau
ein Pixel horizontal und vertikal. Der Rahmen links X=240–243 ist vier Pixel breit,
danach ein Pixel Abstand. Rechts X=316–319 ebenfalls vier Pixel Rahmen; nach dem
letzten Schiff bleiben vier Pixel Abstand. Das benötigte Minimum beträgt 77 Pixel;
die verfügbaren 80 lassen drei zusätzliche Pixel am rechten Innenrand zu.
In H640 sind Schiffe/Abstände/Rahmen horizontal verdoppelt. Vertikal bleibt die
Engine-Geometrie unverändert. Anzeige von links nach rechts, dann zweite Reihe.

Die Lebenssymbole verwenden unmittelbar die unveränderten Spieler-Glyphen
`$321/$322/$323` und Palette Bank 2. Statische GOTOX-Tokens im HUD-Prefix positionieren
sie, ohne bewegliche Objektrecords, ohne dynamische Slots und ohne Hardware-Sprites.
Subzeilenoffsets -2/-3 und transparente GOTOX-Tokens ermöglichen den 1-Pixel-Abstand
zwischen den Reihen. In der gemeinsamen RRB-Zeile 9 passen maximal acht Fragmente,
beide Seitenrahmen und Palette-Reset genau in 21 Einträge/42 Bytes. Leere Plätze
sind unsichtbare GOTOX-640-Tokens. Das HUD-Clearing berührt keine dynamischen Bytes.

Text und Rahmen sind gewöhnliche monochrome Bildschirmzeichen. Der tatsächlich
vor Spielstart eingestellte BASIC-Zeichensatz wird per eigener F018A-DMA nach
`$4000–$47FF` kopiert; es werden keine ROM-Bytes ausgeliefert. Die VIC-Aliase
`$1000/$1800/$9000/$9800` werden zum entsprechenden Character-WOM-Bereich
`$0FF7E000/$0FF7E800` aufgelöst. Andere Quelladressen werden direkt übernommen.
Für die schmale Schrift werden jeweils zwei Originalspalten per OR zusammengefasst,
dann auf vier Spalten getrimmt. Eine Zelle belegt damit acht native H640-Pixel.
Vier einfache Rahmenzeichen ersetzen ungenutzte Zeichen 128–131 in der lokalen Kopie.

Nur ungenutzte Bank-2-Indizes 10–15 erhalten Weiß/Grau/Gelb/Rot/Blau/gedimmtes Grau.
Index 0 wird für den schwarzen Hintergrund auf Schwarz gesetzt; er ist in den
Spieler- und Lebens-NCM-Glyphen transparent. Sichtbare Originalfarben 1–8 bleiben
bytegleich. Gegnerpalette Bank 1 und BASIC-ROM-Palette Bank 3 bleiben unverändert.
Alle HUD-GOTOX-Tokens wählen Bank 2, der letzte Token vor den beweglichen Slots
setzt die primäre Palette zurück. Auch die nicht vom Renderer besuchten Zeilen
0/1/23/24 erhalten bei Initialisierung ausschließlich unsichtbare Endmarker im
Suffix, damit kein altes H320-Blank das HUD nachträglich überzeichnen kann.

## Daten und Schnittstellen

Mutable Daten liegen ausschließlich im bisher unbenutzten reservierten Arbeits-RAM.

| Adresse | Name / Format |
| --- | --- |
| `$1A00` | `hud.high_score`, unsigned 32 Bit LE |
| `$1A04` | `hud.player1_score`, unsigned 32 Bit LE |
| `$1A08` | `hud.player1_level`, unsigned 16 Bit LE |
| `$1A0A` | `hud.player1_lives`, unsigned 16 Bit LE |
| `$1A0C` | `hud.player2_score`, unsigned 32 Bit LE |
| `$1A10` | `hud.player2_level`, unsigned 16 Bit LE |
| `$1A12` | `hud.player2_lives`, unsigned 16 Bit LE |
| `$1A14` | `hud.player2_active`, BYTE, in dieser Stage stets 0 |
| `$1A15` | `hud.formation_points`, unsigned 16 Bit LE |
| `$1A17` | `hud.attack_points`, unsigned 16 Bit LE |
| `$1A20–$1A38` | Anzeige-Schattenwerte |
| `$1A40–$1A50` | Dezimal-/Zeichen-Arbeitspuffer, gesicherte X-Skalierung |

`hud.hud_init` ruft die unveränderte Spielerinitialisierung auf, setzt Modus und
Schrift, zeichnet statische Elemente und initialisiert die Anzeigen. Anfangswerte:
Scores 0, Player-1-Level 1/Leben 3, Player 2 inaktiv mit Werten 0, Punkte 100/115.
`hud.hud_draw_static` ist nur für Initialisierung vorgesehen; es initialisiert
auch das RRB-Suffix vor dem ersten Render-Frame.

`hud.hud_update_score`, `hud.hud_update_level`, `hud.hud_update_lives` und
`hud.hud_update_points` vergleichen die jeweiligen P1-/Highscore-/Punktefelder
mit Schattenwerten und schreiben nur bei Änderungen. Aufrufe zerstören A/X/Y/Flags;
RAM-Werte vor dem Aufruf vollständig setzen. CRAM2K wird nach Lebensaktualisierung
wieder ausgeschaltet. `hud.hud_render` ruft zuerst den bestehenden Renderer auf,
danach die Updates. Player-2-Felder und HUD-Bereiche sind vorbereitet; Aktivierung,
Player-2-Updates und Lebenrendering erfordern eine spätere Stage. Kein Tastencode
setzt `player2_active`. P/S ändern nichts, X nutzt den bisherigen Exit.

Scores bleiben 32 Bit (bis 4.294.967.295). Die Anzeige zeigt die letzten sieben
Dezimalziffern; sie begrenzt den gespeicherten Wert nicht. Level/Punkte zeigen die
letzten drei Ziffern. Leben werden intern bis 65.535 gehalten, aber auf maximal
acht Symbole begrenzt. Keine Punktevergabe, Persistenz oder Interpretation von
weiteren VYLV-Feldern. Die Punkte bleiben Testwerte, bis jemand die HUD-Daten ändert.

## Begrenzte Integration und Exit

Neue Code-/Datenbereiche: `$3800–$3C27`, `$5810–$5C60`, `$7A00–$7FE1`.
Diese waren in der stabilen PRG-Datei komplett leer. Bestehende Routinen/Labels
bleiben an denselben Adressen. Der Builder gestattet nur vier Hooks (`$2230`,
`$22B7`, `$BDDE`, `$2D14`) und zwei Endmarker-Operanden. Insgesamt 3047 geänderte PRG-Bytes. Alle anderen Baseline-Bytes
außerhalb der neuen Bereiche müssen identisch sein. Loader, SETBNK, Originaldaten,
Parser, Grafik-DMA, Bewegung, Joystick und Animation bleiben bytegleich.

Der Exit-Hook sperrt IRQs, stellt das zusätzlich geänderte `$D05A` wieder her und
schaltet Sprites ab; anschließend läuft die bisher bestätigte Restaurierung weiter.
Sie stellt auch `$D031` (H640), Charset-Pointer, Screen-/Color-Zeiger, Palette,
HOTREG und den vollständigen 2-KB-BASIC-Color-RAM-Inhalt wieder her. KERNAL-/Cursor-
RAM `$1000–$15FF` wird nicht verändert. Ein Neustart baut Font/HUD/Palette erneut auf.
Die unveränderte Ladeerfolgsmeldung heißt weiterhin Stage 3b-2; Disk/PRG heißen 3b-4a.

## Reproduzierbarer Build und Prüfungen

```sh
python3 tools/build_stage3b4a.py --kickass /pfad/KickAss.jar
MEGA65_ROM=/pfad/MEGA65.ROM python3 -m unittest discover -s tests -p 'test_stage3b*.py' -v
```

Python und Java wie zuvor; KickAssembler 5.25 mit gepinnter SHA-256. Für Tests die
bestehende `tests/requirements-stage3b1.txt` installieren. Der Builder generiert
`stage3b4a_templates.asm` deterministisch, prüft Originaldaten und erlaubte Patches,
assembliert und erzeugt D81 mit geprüften Dateiketten/BAM. Ausgabe enthält drei
vollständige ASM-Dateien, PRG, D81, Symbole, Speicherkarte, Buildbericht und Prüfsummen.

Automatisiert: **51 Tests bestanden**, acht neue HUD-Tests plus 43 bisherige
Regressionstests. Nach der abschließenden Rahmenanpassung alle acht HUD-Tests
erneut bestanden; zwei Builds erzeugen byteidentische Ausgabedateien. Geprüft werden
vollständiger Preload; korrekte Labels/Zahlen; Font-DMA aus VIC-Alias und direkt
adressiertem Charset; 32-Bit-Scores einschließlich Maximalwert; keine Screen-Schreib-
zugriffe bei unveränderten Werten; Originalpixel aller acht Lebensplätze einschließlich
Abstände und gemeinsamen Zeilen; 0/3/4/5/8/9/256/65535 Leben; 56 Frames mit identischen
Objekt-/Pfad-/Glyphenzuständen gegen 3b-3; verdoppelte GOTOX-Werte; permanenter HUD-Prefix;
inaktives P/S/Player 2; Exit/Neustart einschließlich Font-X-Skalierung, BASIC-Farben,
ROM-Palette und unverändertem Cursor-RAM; Grafik-DMA-Fehler nutzt denselben Exit.
Mit dem bereitgestellten V920395-ROM wird außerdem dessen echte Cursorroutine ausgeführt.

Im CPU-Modell kostet das unveränderte HUD samt X-Umrechnung im Mittel etwa 2395
zusätzliche CPU-Zyklen pro Frame; Dezimalberechnung/Lebensaufbau nur bei Änderungen.
Raster-Wartecode und Slotkapazität bleiben erhalten. Dies ist keine Messung realer
Bildrate und kein vollständiger Emulatorlauf. Schriftlesbarkeit, reale VIC-Ausgabe,
Rastertiming und Joystick sind durch den Benutzer unter XEMU abzunehmen.

## XEMU-Abnahme

Frisch booten mit ROM V920395, D81 in Laufwerk 8, `LOAD"STAGE3B4A",8`, dann `RUN`.
Laden/Verifizieren beider DAT-Dateien prüfen. Alle 24 Pixies, Farben, Animation,
Joystick, SPACE und +/- gegen 3b-3 vergleichen. HUD rechts: 0000000 / 0000000 /
LEVEL 001, drei Originalschiffe; vier Plätze pro Reihe, Rahmen und Abstände prüfen.
Player 2 gedimmt/inaktiv, P/S als nicht aktiv bezeichnet, X EXIT; unten 100/115.
Auch nach längerer Bewegung keine HUD-Übermalung oder Farbkonflikte. Mehrfach X:
normaler BASIC-Bildschirm/Cursor ohne rote Linie; erneutes LOAD/RUN muss funktionieren.
Erst nach ausdrücklicher Benutzerbestätigung als stabil markieren.
