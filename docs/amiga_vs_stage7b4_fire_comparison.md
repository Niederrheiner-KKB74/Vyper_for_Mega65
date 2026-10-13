# Original-Amiga vs Stage7b4 — Schusslogik, Issue #61

Analysebasis: Stage7b4 Commit `bd63682fa37df2853338b499f1210ec9dd2f56dc`.
Alle dortigen Enginequellen, Assets, DATs, Releases und Buildskripte wurden
nur gelesen. **Keine Umsetzung, kein Build, kein Merge/Stable.**
Originalnachweise: [Hauptbericht](amiga_enemy_fire_analysis.md),
[Instruktionsbytes/Adressen](amiga_enemy_fire_evidence/68000-excerpts.txt),
[100-Level-Tabelle](../assets/amiga_enemy_fire_level_parameters.csv).

## Warum die Begrenzung allein nicht genügt

Die beiden Versionen begrenzen **verschiedene Größen**:

- Original: pro Gegner-Flugphase neu geplante **Ereignisse**. Ein nicht mehr
  aktives Projektil erzeugt keinen neuen Countdown oder Schwellenwert.
- Stage7b4: maximal zwei gerade **aktive Projektile je Schütze**. Sobald eines
  verschwindet, wird derselbe Gegner wieder in die Schützenliste aufgenommen
  und kann nach dem globalen Cooldown erneut ausgewählt werden.

Ein langer ENTRY-/ATTACK-Flug kann damit in Stage7b4 viele nacheinander
abgefeuerte Schüsse erzeugen, obwohl zu keinem Zeitpunkt mehr als zwei
besitzereigene Schüsse fliegen. Das Original plant in seinem Standardpfad
höchstens zwei neue Ereignisse pro Flugphase. Dieser Mechanismusunterschied
ist aus dem Code bewiesen; er erklärt die Möglichkeit deutlich höherer
Schusszahlen, ohne eine gemessene Originalrate vorzutäuschen.

Zusätzlich verbraucht ein fehlgeschlagener Originalversuch bei sechs belegten
Slots sein Ereignis. Stage7b4 hat kein solches endliches Ereignis und würfelt
bei freiem Cooldown weiter. Die künstliche individuelle Aktivenzahl ersetzt
also nicht die ursprüngliche Schussentscheidung.

## Konkrete Gegenüberstellung

Alle Originaladressen beziehen sich auf die untersuchte USS-Allokation;
Dump-/CODE-/Dateioffsets im verlinkten Auszug. Abweichungen sind statisch belegt,
ihre Auswirkungen auf Spielschwierigkeit ohne Amiga-Messlauf qualitativ.

| Aspekt | Originalregel / Nachweis | Stage7b4-Istzustand / Quelle | Abweichung und mögliche Wirkung |
|---|---|---|---|
| ENTRY-Auswahl | Laufender Gegnerzähler, jeder N-te nach Level+$70; C0AE8E–AF84 | Jeder sichtbare ENTRY-Gegner mit erlaubtem Ursprung/Quota; `selection.fire_eligible` | Original-Ausdünnung fehlt, besonders bei N=2/3/4 |
| ENTRY-Auslösung | Individuelle +7A/+7C-Countdowns; einmalig bei Dekrement auf0; C0D446–D46A | Globaler Cooldown, Zufallsbedingung und zufälliger geeigneter Schütze | Freigewordene Slots erlauben viele weitere Schüsse derselben Phase |
| ENTRY-Punktwahl | Initial t1=L+random(N−L), in74 Levels L>0, Planung prüft Kurven-Y<=148; mode2 t2=(t1+15)%N; C0AEA2–AF62 | Sichtbarkeit plus signed muzzleX in0..237 und muzzleY in16..183 | Aktuelle Bildschirmprüfung ist kein rekonstruierter Schusszeitpunkt |
| WAIT_ENTRY | +6C-Startwartezeit verhindert Bewegung/Countdown; C0D3EE–D3F8 | WAIT_ENTRY-State5 nicht zugelassen; `selection.fire_eligible` | Zweck stimmt überein, Statewerte und Organisation sind verschieden |
| ATTACK-Auslösung | Y-Schwellen einmalig, clear **vor** Spawn; C0D4EC–D514 | Weiterlaufende Zufallsauswahl bei jedem freiem Cooldown | Schussmengen nicht auf vorbereitete Ereignisse begrenzt |
| Anzahl neuer Ereignisse | Level+$6E:1 oder2; mode1 ATTACK löscht zweiten Wert; C0A758, D252–D272 | Keine Begrenzung pro ENTRY/ATTACK; nur aktive Besitzerquota | Aktive2 ist nicht Ereignisse2; der historische Original-Nachweis fehlte bisher |
| Globale Gegnerprojektile | Sechs Records, BEQ6; C0D614, D5CC | Sechs Slots2–7; freie Slot-Suche `attack.a_fire` | Globale Grenze stimmt numerisch überein und ist nun original belegt |
| Besitzerlimit | Kein Ownerfeld im22-Byte-Projektilrecord, keine Besitzersuche; C0D612–D6D4 | `p_source_enemy` und Scan2..7 mit maximal2; `selection.owner_room` | Zusätzliche MEGA65-Regel, keine nachgewiesene originale Aktivenzahlbegrenzung |
| Fehlgeschlagener Spawn | Ereignis bereits konsumiert; voller Pool: Rückkehr vor RNG; C0D452/D4FC und D614 | Kein Ereignis zu konsumieren; ohne neuen Cooldown weiter würfeln | Neu verfügbare Slots ermöglichen zeitnah neue Versuche |
| Zufallsquelle | `(seed+VHPOSR)&FFFF`, modulo Divisor; C0D764, C0EDF8 | 16-Bit-Galois-LFSR mit Feedback B4; `shots.p_random_step`, Seed C3A5 bei Attackinit | Weder Quelle noch Aufrufzeitpunkte/Ranges sind identisch; keine Amiga-1/2-Pro-Frame-Schusschance |
| Cooldown | Keine allgemeine sechs-Update-Schusspause im Spawn/Entscheidungspfad | `a_SHOT_COOLDOWN=6`, `a_SHOT_RANDOM_MASK=1`, Initialcooldown25 | Testparameter, keine Originalrekonstruktion |
| Y-Geschwindigkeit | Level+$6C =1/2/3; C0B216 setzt DY, C0D5D6 verwendet es | `attack.a_fire_start` schreibt DY=1 unabhängig vom Level | Originale Levelsteigerung fehlt; Lebensdauer/gleichzeitige Dichte ändern sich |
| Ziel beim Spawn | Player-X plus/minus random(20), nach Updateparität; C0D67C–D69E | Gespeicherte aktuelle Player-X+8, ohne Streuung | Stage zielt präziser; quantitatives Ausweichen gesondert messen |
| X-Schritt | 16.16; bei abs(dx)>=dy begrenzt auf DY; C0D6B2–D6CE | 8.8-Verhältnisberechnung in `p_fraction`, eigenes X-Vorzeichen | Originale Steigungsbegrenzung und Genauigkeit nicht identisch |
| Schussursprung | enemyX+7, enemyY−7; C0D668–D678 | `entry.e_xlo+8`, `entry.e_ylo+16` | Rohwerte unterscheiden sich; Original-/Engine-/B2-Anzeigekoordinaten zuerst abgleichen, Zahlen nicht blind übertragen |
| Deaktivierung | Nachgewiesene Standardprojektilroutine prüft Y>=200, nicht X; C0D5C8–D610 | Auch X<1 oder X>=239 deaktiviert sofort; `shots.p_update` | Frühere X-Freigabe kann weitere Schussversuche früher zulassen |
| Rückkehr/Tod des Schützen | Projektile unabhängig vom Actor, ohne Ownerbezug weiterbewegt | Owner bleibt erhalten; Bewegung unabhängig vom Actor | Fortbestehen stimmt; Stage hat zusätzlich weiterhin Ownerquota |
| RETURN/FORMATION-Schüsse | State2 ohne Spawn-Aufruf; C0D46E–D4AA | Nicht in der Schützenliste | Wesentliche Statusregel stimmt überein |
| Physische Darstellung | Enemyshots Hardware SPR2–7; Player Hardware SPR0/1 attached; zwei Player-Schüsse BOBs | Player RRB-Pixie; alle2+6 Schüsse Hardware-Sprites | Technische Architektur verschieden; keine Änderung dafür vorgeschlagen |

Quellstellen Stage7b4:

- [attack.asm](../src/engine/stage7b4_attack.asm): Zeilen8–12 Parameter;
  `a_postframe` ab158, `a_fire` ab458, `a_fire_start` ab493;
  Ownerzuordnung545, DY=1 bei547, Cooldown551.
- [selection.asm](../src/engine/stage7b4_selection.asm): `fire_eligible` ab74,
  `owner_room` ab114; Aktivenzählung anhand ursprünglicher Slot-ID.
- [shots.asm](../src/engine/stage7b4_shots.asm): `p_init` ab82, LFSR221,
  Standardprojektilbewegung316; T-Testpfad230 ist nicht normaler Spielpfad.
- [game.asm](../src/engine/stage7b4_game.asm): `c_tick` ab674, Zufallsschritt697,
  Gegner-Fire698; Standardaufruf pro bestehendem Spielframe.

## Angriffsauswahl ist ein separates Problem

Original C0D174–D27A: Angriffstimer wird auf ungeraden Engineupdates und ohne
Player-Schutzgate dekrementiert. Ein zufälliger Startslot wird gewählt, danach
scannt das Programm zyklisch über alle ursprünglichen Slots bis zu einem
wirklich an seinem Formationsziel angekommenen Gegner. Tote Slots führen
nicht allein zum Verlust eines einzelnen zufälligen Auswahlversuchs.
Pro Batch werden1–4 geeignete Gegner mit derselben Kurven-ID gesucht. Die
Startentscheidung enthält keine globale Maximal-drei-Prüfung. Bei fehlenden
Kandidaten wird der Original-Angriffstimer trotzdem neu gesetzt.

Stage7b4 `a_postframe`: Liste tatsächlich verfügbarer FORMATION-Gegner,
maximal3 ATTACK, ein Start pro festem30-Frame-Intervall. Kein geeigneter
Gegner oder abgelehnter Auswahlrang: Timer bleibt fällig, erneuter Versuch
im nächsten Frame. Das ist eine belegte abweichende Schedulingregel.
Originaltimer für normalen Tabellenindex0:30+random(80) **ungerade Updates**;
Umrechnung in Sekunden nur nach Prüfung der Original-Updatezeitbasis.
Die Original-Batches und die globalen Aktivenzahlen nicht gleichsetzen.

Diese Befunde erklären zusätzliche Unterschiede im Angriffsablauf, sind
aber **keine Freigabe zum Verändern** der bisherigen Attack-Kurven, Timer,
Auswahl oder Drei-Gegner-Grenze. Sie dürfen nicht als Schuss-Cooldown behandelt
werden. Eine separate Entscheidung des Benutzers ist erforderlich.

## Priorisierte Empfehlungen — noch nicht implementiert

1. **Ereignisse statt wiederholtem Schusswürfeln:** Für ENTRY und ATTACK
   Originalplanung und einmaligen Verbrauch übernehmen. Auch bei vollem
   globalem Pool das Ereignis verbrauchen. Keine bloße weitere Erhöhung des
   MEGA65-Cooldowns als angeblich originale Lösung.
2. **Nachgewiesene Levelparameter verfügbar machen:** Geschwindigkeit,
   Ereignis-Modus und ENTRY-N aus der CSV verlustfrei als Laufzeitparameter
   übernehmen, erst nach Freigabe des dafür nötigen Datenformats. Das aktuelle
   VYLV-Recordformat führt diese drei Originalfelder nicht als eigene Felder.
   In diesem Auftrag wurde keine DAT-Datei erweitert.
3. **Originalkoordinaten vor Renderingprojektion verwenden:** ENTRY-Zeitpunkte
   anhand ursprünglicher Kurvenpunkte, ATTACK-Schwellen im Original-Y-System
   planen; B2-Y−16 und Formationsverschiebung dürfen Schwellen nicht heimlich
   neu definieren. Den nachgewiesenen t1/t1−1-Versatz bewusst entscheiden.
4. **Zusätzliche Ownerquota als Designentscheidung kennzeichnen:** Maximal2
   aktive je Schütze ist kein Originalnachweis. Beibehalten/Entfernen erst
   nach Vergleichstest und ausdrücklicher Entscheidung; derzeit unverändert.
5. **Danach Streuung, Geschwindigkeiten und Steigungsbegrenzung prüfen:**
   Level-DY und Original-Zielstreuung beeinflussen Ausweichbarkeit. Ein
   portabler RNG kann dieselben Wertebereiche verwenden, reproduziert aber
   nicht automatisch den Amiga-Beam-RNG. Kein ungeprüftes Gleichheitsversprechen.
6. **Angriffstimer/Batchwahl getrennt behandeln:** Original-Updatezeitbasis und
   Sonderlevel-Ranges zunächst messen, anschließend eine eigene Freigabe
   zu Schedulingänderungen einholen. Der Auftrag verändert sie nicht.

## Bekannte offene Punkte und Messgrenzen

- Exakte Anzahl der Engineupdates pro PAL-Frame: Byte-Rasterwait erkennt0/256;
  CPU/Blitterlast und Frameskips müssen in WinUAE protokolliert werden.
- Möglicher alter ENTRY-counter2 beim ausgewählten Mode1-Slot: kein explizites
  Clear im Planungszweig; frischer Nullzustand allein beantwortet Slotreuse nicht.
- Vollständige Player-Tod-/Hardwarekollisions- und Sonderreset-Pfade sowie
  unveränderte ursprüngliche Timer-Ranges an jedem Sonderlevelstart.
- Tatsächliche Schüsse/Minute im Original, räumliche Schussdichte und maximale
  überlappende Schüsse eines ursprünglichen Schützen: nicht gemessen.

Vorhandene Stage7b4-Hostmessung (aus dem unveränderten Release, hier **nicht**
neu ausgeführt): bei einem erhaltenen Level-1-Gegner46 Schüsse und12 Angriffe
in3000 simulierten50-Hz-Ticks. Das sind keine Amiga-Messwerte. Der neue
Originalcode-Nachweis erlaubt daher keine ehrliche prozentuale Aussage
„Stage ist X-mal schwerer“. Er erlaubt bereits die belastbare Aussage,
welche zusätzlichen Schussereignisse die aktuelle Software erzeugen darf.

Die Benutzerprüfung soll zunächst die ursprüngliche Ereignislogik, die
100-Level-Feldzuordnung und die offenen Messpunkte bewerten. Eine mögliche
Stage7b5 ist **nicht** Teil dieses Analysebranches.
