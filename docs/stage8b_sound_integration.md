# Stage8b – Original-Amiga-Sound im vollständigen Spiel

Issue #73; **Entwicklungsstand, kein Stable und kein Merge ohne Benutzerabnahme**.
Ausgangsbasis: aktuelles `main`, Commit
`f7350d6` (Merge von Stage7b5b / PR #66). Technische Audioreferenz ist der vom
Benutzer bestätigte Stage8a2-Stand `ee66f6d44fe4b6488dd3db25c7b91deaa77878d5`,
einschließlich der Korrektur des sporadischen ERROR5 am Sampleende.
Die Originalanalyse stammt aus `d135b754beec10d608ac4bf6b91a2357247b62f3` / PR #68.
Die geschlossenen Analyse-/Audio-PRs wurden **nicht** über die Spielengine gemergt.

Alle bestehenden Dateien von `main` unter `src`, `assets`, `tools`, `releases` und
die im bisherigen Builder geschützten Stable-Referenzen werden vor dem Build gegen
Git geprüft. Neue Enginequellen heißen `src/engine/stage8b*.asm`; alte Stages
bleiben bytegleich. Die vorhandenen sechs DAT-Dateien sind ebenfalls bytegleich.

## Korrektur nach XEMU-Abbruch unmittelbar nach dem Titel

Der Erstbuild `50edf577` ist durch die Benutzerabnahme **als fehlerhaft erkannt**:
Titelteile beschädigt, anschließend PC/linear PC0000 unter ROM V920413.
Die damaligen Hostprüfungen waren kein Nachweis der IRQ-Sicherheit zwischen
KERNAL-Traps; diese konkrete Prüflücke wird durch die folgende Regression abgedeckt.

Nachgewiesener Fehler im Trampolin `audio8.rom_call`:

```asm
; ALT nach JSR $FFFF (KERNAL läuft mit IRQs):
php                 ; sichert normalerweise I=0
sei
; ... Rückgaberegister sichern, MAP A000->E000, Register restaurieren ...
plp                 ; I=0 wird bei bereits bankbarem Loader wieder freigegeben!
sei                 ; erst die nächste Instruktion sperrt wieder
rts
```

Die sichtbare native SYS-Abbildung E000→3E000 wird für die Loader-Abbildung
aufgegeben. Ein IRQ nach dem PLP läuft somit nicht mehr im vorgesehenen
KERNAL-Kontext. SEI danach macht die bereits eröffnete Unterbrechungsmöglichkeit
nicht sicher. Die genauen Folgeschritte bis zum vom Benutzer beobachteten PC0000
wurden hier nicht in XEMU nachverfolgt; der unsichere Zustand selbst ist anhand
des assemblierten Codes reproduziert. ROM V920413 hat unterschiedliche Vektoren
in Bank2/Bank3 (IRQ FF48/FA23); diese Kontexte sind nicht austauschbar.

Korrektur: **SEI vor PHP**, solange noch der normale KERNAL-Kontext aktiv ist.
SEI erhält Carry und die übrigen Ergebnisflags. Der Rückgabestatus enthält jetzt
I=1; das spätere PLP kann im bankbaren Loader keine IRQs mehr freigeben. Der
äußere Gate stellt den vorherigen IRQ-Zustand erst nach Wiederherstellung des
nativen SYS-Kontexts her. Kein neues Grafik-, Timing- oder Gameplayverhalten.

Im PRG ändern sich ausschließlich zwei Bytes:
`$66C6:08→78`, `$66C7:78→08` (PHP/SEI→SEI/PHP). Länge und alle Adressen bleiben
gleich. VYSO und sämtliche sieben DAT-Dateien bleiben bytegleich.
Die neue CPU-Testinvariante prüft **nach jeder ausgeführten Instruktion**, dass
bei MAP für Loader/Audiocode IRQs maskiert bleiben. Der alte Build reproduziert
`IRQ enabled ... PC66D9, mask20`; der neue besteht dieselbe gezielte Prüfung.
Zusätzlich werden Kaltstart, alle Dateiladevorgänge und die bisherigen Audio-/
Spiel-/Exit-Tests mit dieser strengeren Invariante erneut ausgeführt.
**Erneute XEMU-Abnahme erforderlich; keine Stable-Freigabe daraus ableiten.**

## Ausführen und Abnahme

D81 in XEMU einlegen, übliche PAL-Konfiguration mit MEGA65-ROM und Joystick
**Port2** verwenden:

```basic
LOAD "STAGE8B",8
RUN
```

Das originale Titelbild bleibt beim Laden sichtbar. Zusätzlich zu den bisherigen
Dateien wird `VYSO.DAT` geladen und geprüft. Danach erscheint unverändert das Menü;
F1 startet das Spiel mit dem dort gewählten Level. Es gibt keine Audio-Testtasten
und kein neues Audiomenü. Alle bisherigen Spiel-/Menütasten bleiben erhalten.

Die neue Datei wird vor `VYMN.DAT` geladen: Reihenfolge
`VYTI, VYSO, VYMN, VYLV, VYGR, VYCL, VYSH`.
Das Audio-Archiv wird direkt ins Attic übertragen, nicht in die bereits für
Level-/Grafikdaten benötigten Bereiche. Erst nach F1, Rückkehr aus dem Menü und
der bestehenden FAST/VFAST-Initialisierung übernimmt der Audiotreiber die Hardware.
Im Titel-/Menüteil gibt es keine erfundenen neuen Soundereignisse.

XEMU-/Hardware-Checkliste:

1. Titel beim Laden vollständig sichtbar, Menü/32 Animationen/Color-Cycling korrekt.
   F1 auch mit anderem Initial-Level, F2/F3-Platzhalter und Joystick Port2 testen.
2. Level1: ENTRY/ATTACK, Gegnerfeuer, Zerstörung, Playerfeuer und Playerverlust hören.
   Im bekannten Fall VYLV14→VYGR15 müssen ENTRY6, ATTACK7, Schuss2, Zerstörung3 gelten.
3. Level3/29/54/100 auf andere typspezifische Sounds und korrekte Grafik/Paletten prüfen.
   Spielerpalette, Explosionen, HUD, Sterne, Clipping und Steuerung unverändert.
4. Zwei gleichzeitige Effekte links/rechts hören; bewegte Gegner/Projektile sollen
   die Stereoposition auch während eines laufenden Klangs ändern.
5. LEVEL CLEAR bestätigen: ID24 bei Sternbeschleunigung, danach ID22 beim Beginn
   der Rechtecke. Kein Aussetzen während farbiger/schwarzer Rechtecke oder Levelaufbau.
6. Lange Spielsituation mit drei Angreifern und sechs Gegnerschüssen testen.
   GAME OVER, R, +/− und100→1 prüfen; Score/Highscore/Leben nach bisherigen Regeln.
7. X während laufender Sounds: kein Restsound, normaler BASIC-Screen/Cursor;
   DIRECTORY und erneutes RUN prüfen. Keine Stable-Freigabe allein aus dem Hostmodell.

## Originalereignisse und Priorität

Grundlage: [Analyse](amiga_sound_engine_analysis.md),
[volle Ereignistabelle](amiga_sound_event_mapping.md),
[38×4-Tabelle](amiga_sound_evidence/enemy_types.csv),
[68000-Auszüge](amiga_sound_evidence/68000-excerpts.txt).
Adressen sind die USS-CODE-Abbildung des Amiga.

| Ereignis | Native Stelle | logische Quelle | Sound / neue Ereignisstelle |
|---|---|---|---|
| ENTRY beginnt tatsächlich | `$C0D41C` | A | Typfeld ENTRY; `entry.e_spawn`, nicht WAIT_ENTRY |
| Formation→ATTACK | `$C0D21E` | A | Typfeld ATTACK; `attack.a_start` |
| Gegnerprojektil tatsächlich aktiviert | `$C0D63C` | B | Typfeld Schuss; `motion.activate` |
| Gegner tatsächlich zerstört | `$C0D332/$C0D3B4` | B | Typfeld Zerstörung; `game.c_enemy_hit` |
| Playerprojektil tatsächlich aktiviert | `$C0D10A` | A |17; `shots.p_player_fire` |
| Player wechselt in Explosion | `$C09498` | A |19; `game.c_player_hit`, nach Unverwundbarkeitsprüfung |
| Levelwechsel beginnt | `$C08F52` | A |24, Mitte; `transitionfx.begin` |
| Beschleunigung→Rechteckphase | `$C09060` | A |22, Mitte; bestehender FSM-Übergang |

Kein Sound bei vollem Projektilpool, fehlgeschlagener Schusszulassung, wartendem
Gegner oder wiederholtem Rendern. Rückkehr zur Formation erzeugt keinen neuen Effekt.
Zusätzliche Menü-, Extra-Leben- oder GAME-OVER-Samples sind nicht nachgewiesen und
wurden nicht erfunden. Der Score-/Kollisions-/Bewegungscode wird nicht ersetzt.

Echter Originaltyp-Record: DATA+`$2BAA`,18 Bytes. Soundfelder bei+10/+12/+14/+16
(Zerstörung/Schuss/ENTRY/ATTACK), **nicht** relativ zum früheren Grafik-Hilfsanfang
DATA+`$2BA2`. `convert_stage8b_audio.py` prüft die vier Felder aller38 Typen gegen
ADF **und beide RAM-Abbilder**. Zur Laufzeit wird der aktuelle VYGR-Frameursprung
eines Actors gegen die38 Originaldeskriptoren aufgelöst. Keine Slotnummer als Typ,
keine Verschiebung des Index14 und keine provisorische Audio-Mappingregel.
Die sechs Gegner-Zerstörungssamples sind1/3/8/9/18/20; Player19 bleibt davon getrennt.

Originale zwei Effektplätze statt einer beliebig großen Warteschlange:

- Gegner-ENTRY/ATTACK/-Zerstörung werden bei Busy abgewiesen.
- Beim Gegnerschuss wird der Positionszeiger auf das neue Projektil **auch bei Busy**
  aktualisiert; die neue ID bleibt dann abgewiesen. Bei vollem Pool entsteht gar
  kein Ereignis. Ein laufender Zerstörungsklang kann daher nativ einem neuen Schuss folgen.
- Player17/19 und Transition24/22 dürfen Quelle A sofort unterbrechen und setzen
  eine neue Pending-ID ohne Busy-Zulassung. Der neue Start erfolgt im Soundtick.
- Mehrere zugelassene Schreiber vor dem nächsten Tick: der letzte gewinnt. Keine
  FIFO und keine erfundene allgemeine Prioritätsliste. Busy wird erst beim Start gesetzt.

Soundtick vor den neuen Gameplayereignissen, einmal pro vorhandenen50-Hz-Frame.
Busywerte3/6/120 stammen aus den Deskriptoren. LEVEL CLEAR, GAME OVER und die
vorhandene Animationspause dekrementieren Busy nicht. Bei der Transition tickt die
logische Pflege während Beschleunigung und der ersten drei Rechteckframes;
danach bleibt Busy bis zum neuen Gameplay eingefroren. Der hochfrequente
Streamingservice läuft unabhängig davon weiter.

Die drei Frames entsprechen der belegten Reihenfolge um die drei WaitTOFs und
COPER-Flaglöschung. Die **exakte native Soundtickfrequenz und analoge Ereignisdauer
sind nicht vollständig bewiesen**; diese Abbildung auf die bestehende50-Hz-Engine
ist dokumentiert, nicht als gemessene Gleichheit ausgegeben. Insbesondere läuft
hier die bestehende Beschleunigung50 Frames:24 wird von22 verdrängt, statt für
Soundzwecke das unveränderte visuelle Timing zu verlängern. ID22 darf ins nächste
Level hinein weiterklingen; Source B und gegnergebundene alte Referenzen werden
beim Levelreset gestoppt. R stoppt beide Quellen und Pending, nicht den Highscore.

## Datei VYSO.DAT, Originalintegrität

160960 Bytes, geschlossenes SEQ. Versionsformat1, Little Endian:

| Dateioffset | Inhalt |
|---|---|
|0..3|`VYSO`|
|4/6|Version WORD1 / Headergröße WORD512|
|8/12|Codeoffset DWORD512 / Codegröße DWORD6144|
|16/20|PCM-Offset DWORD6656 (`$1A00`) / PCM-Größe DWORD154304|
|24/26|20 Samples /16 Bytes pro Metadatensatz, jeweils WORD|
|28|PCM-CRC16/CCITT-FALSE als DWORD, obere16 Bits0|
|32..351|20 Metadatensätze|
|352..511|reserviert0|
|512..6655|bankbarer Audiocode/Tabellen, auf6144 Bytes begrenzt|
|6656..160959|unveränderte, gepackte Signed8-PCM-Bytes|

Je16-Byte-Datensatz: ID BYTE, geladen BYTE1, PCM-relativer Offset DWORD,
Länge WORD, originaler PER WORD, Panningteiler BYTE, Busy BYTE,
Ratenakkumulator WORD (hier alle<65536), Sample-CRC WORD.
Vollständige Originaloffsets, Hashes, PER, Busy, Typfelder und Diagnosesymbole stehen
in `releases/stage_8b/audio-metadata.json`. Der gesamte Datei-CRC ist zusätzlich
im PRG gepinnt; Format-/Metadaten-/Code- und PCM-Änderungen werden dadurch abgewiesen.
Erste32 Headerbytes werden bereits beim ersten Chunk verglichen.

20 geladene Original-IDs:
`1,2,3,5,6,7,8,9,10,11,12,15,16,17,18,19,20,21,22,24`.
4/13/14/23 sind weiterhin unbenutzt. `/Vyper/sonquasar` wird aus der vorhandenen
ADF gelesen, alle20 PCM-Blöcke werden mit CSV-Hash und beiden Original-RAM-Abbildern
verglichen. Es gibt keine WAV-/Unsigned-Konvertierung und keine Ersatzsamples.
Die13 ungenutzten Schlussbytes der Originaldatei werden nicht als Sample interpretiert.

```
PAL_Paula_rate = 3546895 / PER
DMA_increment = round(3546895 * 2^24 / (PER * 40500000))
```

Exakt rationale Rundung wie in8a1/8a2, z.B. ID17: PER356, Increment4127=`$00101F`.
Originaldaten und Perioden bleiben unverändert, einschließlich langer IDs19/22.
Keine unbewiesene Tonhöhenkorrektur oder SID-Neusynthese.

## Geprüfte Speicherkarte und Phasen

Das Spiel benötigt weiterhin DOS-RAM,24 RRB-Pixies, Originaldaten, Sternbitmap,
Titelcache, Menüs und BASIC-Farbsicherungen. Die isolierten8a2-Puffer bei4000/5000
wären hier falsch. Neue Bereiche werden phasenabhängig wiederverwendet:

| Physischer Bereich | Stage8b-Verwendung / Abgrenzung |
|---|---|
| `$10000–$11FFF` | DOS bleibt unverändert |
| `$12000–$126FF` | unveränderter Levelrecord |
| `$12800–$13FFF`, `$14000–$15A7F` | Menüanteile bzw. private Pixies/Player unverändert |
| `$15B00–$162FF` | ursprüngliche Bootstrapsicherung unverändert |
| `$16400–$173FF` | neuer4096-Byte-Ring A, Halbgrenze`$16C00` |
| `$18000–$1DDBF` | unveränderte Stern-/Transitionfläche |
| `$1DE00–$1DEFF` | unveränderte Transitionfarben |
| `$1E000–$1F7FF` | Audiocode/Tabellen,6144 Bytes, nach Menüende |
| `$1F800–$1FFFF` | Color-RAM-Fenster, ausdrücklich nicht benutzt |
| `$40000–$53F80` | VYLV,81793 Bytes |
| `$54000–$5C2B7` | VYGR,33464 Bytes |
| `$5C300–$5C4DB` | VYCL,476 Bytes |
| `$5C500–$5D4FF` | neuer4096-Byte-Ring B, Halbgrenze`$5CD00` |
| `$5F100–$5FB4F` | Titel-Color-Backup unverändert |
| `$08000000–$080252BF` | vorhandene Attic-Sicherungen/Menüasset, mit bisherigen Lücken |
| `$0802B000–$0802B01F`, `$0806B000–$0806B01F` | neue Kapazitäts-/Aliasing-Probewerte |
| `$0802C000–$0802CFFF` | Sicherung des transienten Audioloaders für RUN |
| `$08030000–$080574BF` | vollständiges VYSO-Archiv |
| `$08030200–$080319FF` | darin die Audio-Codekopie |
| `$08031A00–$080574BF` | darin Original-PCM |

Die Audiocode-/Ringbereiche waren zuvor Teile des Titel-/Menüatlas, sind nach dem
Spielstart unbenutzt. Der Menüatlas darf sie während der Menüphase weiterhin
belegen; kein Audiokanal wird dort aktiviert. Nach Wiederherstellung der Engine
wird der Code aus dem gesicherten VYSO-Archiv installiert. Ein erneuter Start
initialisiert die Puffer wieder. Es wird weder RAM ab`$60000` angenommen noch in
ROM`$20000–$3FFFF` geschrieben.

Vor Laden werden unterschiedliche Probewerte bei Attic2B000/6B000 geschrieben und
beide zurückgelesen. Das erkennt insbesondere256-KiB-Aliasing, das sonst getrennt
geprüfte Archive und vorhandene Menüassets gegenseitig überschreiben könnte.
Anschließend: exakte Dateilänge/EOF, kompletter Datei-CRC, jeder256-Byte-Chunk mit
DMA-Rückkopie und Bytevergleich, danach ein zweiter vollständiger Attic-CRC-Durchlauf.
Die aktuelle Referenz/XEMU-Speicherkarte hat8MiB Attic; die tatsächlich genutzten
Adressen werden trotzdem geprüft. Audio-DMA liest ausschließlich die beiden ChipRAM-Ringe.

### Bootstrap, CPU-Abbildung und Wiederanlauf

Die fertige Haupt-PRG endet weiterhin bei`$CFFF`, nicht im I/O-/ROM-Fenster.
Der neue Audioloader ist **anfänglich bei`$5000` abgelegt**, in dem erst beim
Spielstart beschriebenen BASIC-Color-Backup. Vor dessen Wiederverwendung wird er
per DMA in die noch unbenutzte RRB-Screenfläche`$E000` kopiert und im Attic gesichert.
Die Titel-Screenfläche`$F300–$FD4F` bleibt davon getrennt.

Bankgate: CPU`$A000–$BFFF` wird kurzzeitig abgebildet, mit maskierten IRQs und
vollständig erhaltenen A/X/Y/Z/B/Statusregistern. Audiocode: Offset`$14000`, also
physisch`$1E000`; Loader: Offset`$4000`, also physisch`$E000`.
Vor jedem KERNAL-Aufruf wird **die native SYS-Abbildung E000→Bank3** hergestellt,
Z auf den KERNAL-Aufrufwert0 gesetzt und IRQ freigegeben. Danach wieder IRQ sperren
und die Loaderabbildung herstellen. Keine KERNAL-Aufrufe aus der Audioabbildung.
Dieser native SYS-Kontext wurde bereits bei Stage4b dokumentiert; ein bloßes
D030-Umschalten oder pauschales MAP0 wäre hier falsch.

F018A-Listen im bankbaren Code werden mit ihrer **physischen**, nicht der logischen
CPU-Adresse gestartet. Audio-Code-Descriptoren liegen in Bank1, Loader-Descriptoren
physisch beiE000. D701/D702/D704 werden nach Audiocalls restauriert. Triggerregister
D700/D705 werden beim Restore nicht beschrieben, um keinen fremden DMA-Job zu starten.

Bei X werden die Stimmen vor der Videorückstellung gestoppt. Nach dem unveränderten
Titel-/BASIC-Restore werden Mixer/Audioregister und die transiente E000-Loaderkopie
restauriert; ein zweites RUN findet daher Code statt RRB-Screendaten vor. Ein erneutes
LOAD setzt den Phase-Cachemarker zurück. R braucht kein erneutes Diskettenladen.

## Streaming, Stereo und Last

Je Quelle ein eigener4096-Byte-Ring mit zwei2048-Byte-Hälften. Bewährtes8a2-Protokoll:
Ring zunächst nullen; erster Originalblock rechtsbündig, sodass das endgültige
Sampleende immer genau eine Halbgrenze trifft. Nur die freie Hälfte nachfüllen,
DMA-Zeiger HIGH/LOW/HIGH kohärent lesen, Quell-/Zielbereich prüfen. Im letzten Block
LOOP ausschalten und STP als Ende verwenden. Erneute STP-Prüfung nach Pointer-Snapshot
und vor Pointerfehler verhindert den bestätigten8a2-Sampleende-Race.

Kanal0=`$D720` für A, Kanal2=`$D740` für B;1/3 bleiben unbenutzt. Signed8, CTRL`$C2`
beim Ring und`$82` für den letzten Block, niemals UNSIGNED. D711=`$80`, NOMIX0.
Digi-L/Input8 und Digi-R/Input9 sind zwei unabhängig pannbare Monoquellen;
keine zwei auseinanderlaufenden Cursor pro Stereopaar.

| Quelle | Primär L/R | Kopfhörer L/R |
|---|---|---|
| A | Mixer`$10/$30` | `$D0/$F0` |
| B | Mixer`$12/$32` | `$D2/$F2` |

Native Formel (X in logischen Einheiten, signed Offscreenwerte geklemmt):
`right=floor(clamp(X,0,240)/div)`, `left=240/div-right`.
Volume64 entspricht Unity; native Summen60/40/30 bleiben erhalten.
Koeffizientbyte=`round(PaulaVOL*255/64)`, beide Koeffizientbytes identisch;
Dadurch bleibt das bestätigte8a2-Gainmapping unabhängig vom Handbuch-/XEMU-
Endiankonflikt. Maximaler absoluter Quantisierungsfehler<1/510.
Mindestens32 I/O-Lesezyklen Wartezeit zwischen Mixer-Schreiben und Selektorwechsel.

Streamservice läuft während des bestehenden Raster250-Wartens und nach Engine-
DMA-Jobs, unabhängig von Busy-/Gameplaytick, LEVEL CLEAR, GAME OVER und Transition.
Kleine Byte-Lesejobs lösen höchstens einen Bankwechsel pro Rasterzeile/Frame aus;
der bankbare Dienst vermeidet ebenfalls doppelte Pflege derselben Zeile. Das ist
keine50-Hz-Nachfüllung:64µs Rastergranularität gegenüber mindestens180,15ms pro Hälfte
beim schnellsten Originalsample (PER312,11368,25Hz). Zwei Stimmen brauchen maximal
ca.22,74kB/s PCM-Nachschub.

Das vorhandene Raster250-Framefenster bleibt erhalten. Während des Wartens wird
im Bereich192..255 kein zusätzlicher Service begonnen, um die Raster250-Flanke
nicht durch einen Nachfülljob zu verpassen. Während eigentlicher Enginearbeit
können die DMA-Nachlaufaufrufe den Stream weiterhin bedienen.

Ab drei unbeobachteten Framegrenzen wird sicher stummgeschaltet; zusätzlich gilt
200-Frame-Endwatchdog (>längstem Sample). Bei komplett angehaltener CPU über die
Pufferreserve hinaus kann reine Software das Wiederholen alter Ringdaten **vor**
dem Wiederanlauf nicht verhindern. Das ist keine Zusage für beliebige CPU-Halts.
Nullinitialisierung verhindert unbeschriebene Ringausgabe; Fehler werden gelatcht.

## Fehlerpolitik und Diagnosen

Audio-Datei-/Kapazitätsfehler: saubere Rückkehr zu BASIC mit
`STAGE 8B LOAD ERROR $0A FILE VYSO.DAT,S,R`, keine stillschweigend ignorierte Datei.
Kein KERNAL-CHROUT während CHKIN aktiv ist. OPEN/CHKIN/CHRIN/READST/CLRCHN/CLOSE sowie
SETBNK vor SETNAM bleiben korrekt, normales Gerät aus der bestehenden Laufwerkswahl.

Audio-Laufzeitfehler: eigene Stimmen sicher stoppen, Spielgrafik/Steuerung weiterlaufen
lassen. Keine ungefragte BASIC-Rückkehr, kein zusätzliches HUD-Element. Diagnosecode
bei bank0`$1FD3`:1=Datei/CRC/Header,2=fremde aktive DMA,3=Attic-Rücklesen/Aliasing,
4=Registerinitialisierung,5=Index/Pointer/Grenze,6=Serviceintervall,7=Endwatchdog.
Nach einem gelatchten Laufzeitfehler X und RUN für Neuinitialisierung; R ändert die
Spielregeln nicht und löscht nicht heimlich die Audiodiagnose. Die50-Hz-Framewartung
bleibt auch bei abgewiesener Audioübernahme bestehen.

Residenter Audiomailboxbereich`$1FD0–$1FD8`, hinter bisherigen Projektil-/Motionfeldern
bis`$1FCC`. Weitere physische Diagnosen aus `audio-metadata.json`:

- Error: `$1E64A`, Unterlauf-/Servicefehlerzähler: `$1E665`.
- Maximaler Serviceabstand in Framegrenzen: `$1E666`.
- Maximaler Serviceabstand in PAL-Rasterzeilen: WORD LE`$1E667` (×≈64µs).
- Nachfüllungen: WORD LE`$1E662`, vollständige Enden: BYTE`$1E664`.

Zähler sind Diagnosewerte mit ihren jeweiligen Byte-/Word-Überläufen, keine
Gameplaytimer. Alle implementierten13 Register je Audiokanal, D711,256 Mixerbytes
und Selektor werden beim Exit restauriert. CIA/Keyboard, SID, IRQ-Vektoren und
VIC-Paletten werden vom Audiotreiber nicht geändert; die bewährte Spielengine
restauriert ihre bisherigen Video-/Sprite-/Cursorzustände.

## Build und tatsächliche Prüfungen

```sh
python3 tools/build_stage8b.py --kickass /path/to/KickAss.jar
PYTHONPATH=tests:tools:/path/to/py65-1.2.0 python3 -m unittest test_stage8b -v
```

Python3, Java, gepinnter KickAssembler5.25; Extraktion benötigt keine neue
Capstone-Laufzeitabhängigkeit. `convert_stage8b_audio.py` erzeugt Originaldatenpaket
und Metadaten aus der vorhandenen ADF. Buildtool erzeugt vollständige Enginequellen,
bankbaren Audiocode, PRG, sieben DATs, vollständiges819200-Byte-D81, Symbolfiles,
Speicherkarte, Metadaten und SHA-256. Nur `STAGE8B` ist das startbare Hauptprogramm;
`AUDIO_CORE.PRG` ist ein internes bankbares Modul, kein eigenständiges BASIC-Programm.

Der Test führt assemblierte Engine-/Audio-Instruktionen in einem begrenzten
45GS02-/KERNAL-/DMA-/VIC-/Mixer-Modell aus. Bankumschaltung, IRQ-/Registererhalt,
physische DMA-Listen und SYS-Kontext werden geprüft. Ein taktgetriebener PAL-Raster
und PCM-Verbrauch nach Akkumulator ermöglichen Interleavings während Code-/DMA-Last.
DMA-Latenz4 Modellzyklen/Byte ist eine **Testannahme**, kein vermessener Hardwarebus.
6502-Modellzykluszahlen einschließlich Rasterwartezeit sind keine45GS02-Messung.

Das Testprotokoll `stage8b_test_results.txt` enthält die ausgeführten Fälle:
Originalintegrität/38×4,20 Sampleenden/Neustart, zwei Stimmen/Panning/Pending/Busy,
repräsentative Levels, F1/Navigation/GAME OVER/R, originale Bewegungs-/Projektil-/
Kollisionsregressionen, vollständige Transition24→22, Last mit3 Angreifern/6+2
Projektilen, Fehlerpfade, X und erneutes RUN. Ein zweiter sauberer Build prüft
Byte-Reproduzierbarkeit. D81-Dateiketten und alle sieben Dateiinhalte werden geprüft.

**Noch offen:** XEMU-Hörabnahme und reale MEGA65-Messung mit Core-/ROM-Version,
Rastermaximalwert und hörbaren Dropouts. Es wurde hier kein XEMU-/Hardware-Hörtest
behauptet. Amiga-Analogfilter, DAC-/Starttransienten, native COPER-Tickfrequenz und
die ursprüngliche Zwei-IRQ-Abschaltung sind nicht identisch nachgebildet; Hardware-
STP ersetzt letztere. Für Gameplay/RNG wird kein neuer Soundzufall eingeführt.
