# Original vs. Stage9a: ATTACK-Ende und kleinster Korrekturansatz

Issue #77, **nur Analyse**. Stable-Referenz `9bbe02ed` / Stage9a-Programm
`7f505473`. Originalbelege: [Hauptbericht](amiga_attack_curve_end_analysis.md),
[Instruktionsbytes/Adressen](amiga_attack_end_evidence/68000-excerpts.txt).
Hier wird kein Patch ausgeführt und keine spätere Implementierung autorisiert.

## Nachgewiesene Ursache in der Portierung

Die ursprüngliche Annahme „ein gepackter Record = ein kompletter Angriff“ war
unvollständig. Die fehlende Logik sitzt im Amiga **Levelaufbau**, nicht im
State3-Interpreter selbst. Die bisherige endliche VYLV-Datei ist korrekt: Sie
enthält die originalen gepackten **Muster**, die bei der Wiedergabe fortgesetzt
werden müssen. Die DAT-Datei braucht für diesen Befund keine Änderung.

| Punkt | Amiga, bestätigt | Stage9a, tatsächlicher Quellcode |
|---|---|---|
|Kurvenauswahl|gegnergebundener Index; Expansion dieses Musters|`a_index,x`, feste Deskriptorzuordnung|
|Format|gepackte signed-magnitude Deltas → pro Gegner absolute XY-Punktfolge|dieselben Deltas unmittelbar integriert|
|X-Ursprung|relativ0 im Puffer, plus beim Start eingefrorener X-Anker|akkumuliertes aktuelles X; Anker wird ebenfalls gespeichert|
|Y-Ursprung|ab Forme-Y+16 beim Levelaufbau|ab aktuellem, vertikal verschobenem Formations-Y|
|Paketende|nur Byteindex zurück0, Akkumulatoren bleiben|Cursor erreicht `a_length` → `e_phase=5`|
|Fortsetzung|gleiche ΔX/ΔY zyklisch, kein neuer Angriff|`a_exit`: X unverändert, Y+=2|
|Ende|Generator stoppt bei Y≥216; terminales Y wird−1|Y≥200 setzt zunächst nur `a_hidden`; erste Kurve läuft ggf. unsichtbar weiter|
|Rückkehr|beim Marker State2/Y0, dann±1 zu aktuellen Driftzielen|nach Phase5 am unteren Ende Y−16, Phase2/ENTRY, dann bestehende Rückkehr|
|Animation/Feuer/Sound|Wrap plant nichts neu|Startplanung nur in `a_start`; so beibehalten|

Konkrete Stable-Stellen (Links auf unveränderlichen Commit):

- [Cursor-/Längenvergleich und Phase5](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/blob/7f50547337c4aa7256f908547d627dae7da433e0/src/engine/stage9a_attack.asm#L387):
  Zeilen387–396, `INC e_cursor; ... CMP a_length; LDA #5; STA e_phase`.
- [Senkrechter Ersatzflug](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/blob/7f50547337c4aa7256f908547d627dae7da433e0/src/engine/stage9a_attack.asm#L422):
  Zeilen422–438, `ADC #a_EXIT_DY` mit Konstante2, kein X-Update.
- [Bottom-Latch](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/blob/7f50547337c4aa7256f908547d627dae7da433e0/src/engine/stage9a_attack.asm#L402):
  nur Unsichtbarkeit, kein unmittelbarer Abbruch der laufenden Kurve.
- [Start](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/blob/7f50547337c4aa7256f908547d627dae7da433e0/src/engine/stage9a_attack.asm#L229):
  setzt State/Phase, Sound und `fireevents.attack_plan`. **Nicht zum Wrap verwenden.**

Für Level4 enthält der Record43 Bytes. Beim ersten Actor endet der aktuelle
Kurvendurchlauf bei X42/Y65 (Anfang40/27, Drift0). Ab dem nächsten Update wird
X42 beibehalten. Die originale Expansion liefert an der entsprechenden nächsten
Stelle dagegen wieder ΔX=+2/ΔY=+2. Bei native-Y53 läuft das Muster vier ganze
Durchläufe plus13 Punkte, insgesamt185 erzeugte Punkte bis zum Marker.
Das ist **keine Verkettung**, **kein zufälliger neuer Kurvenindex** und **keine
Wiederholung anhand Level+$70**.

## Noch nicht implementierter minimaler Vorschlag

Die bestehende unmittelbare Deltaintegration lässt sich ohne große Amiga-Puffer
beibehalten. Die gleichwertige fortlaufende Akkumulation benötigt nur den bereits
vorhandenen **eigenen Cursor pro Gegner**:

1. Während Phase4 unverändert das nächste Byte der fest zugeordneten Kurve lesen,
   X/Y signed fortschreiben. Kurvenlänge und Dateigrenzen weiterhin prüfen.
2. Bei Erreichen der gepackten Länge Cursor0 setzen und **in Phase4 bleiben**.
   X/Y/Anker/Animationsphase nicht zurücksetzen. Nicht `a_start` aufrufen, keinen
   Deskriptor wechseln, kein neues RNG und keinen Wiederholungszähler einführen.
3. Die ATTACK-Phase am **unteren Austritt** beenden, auch wenn dieser vor dem
   ersten gepackten Ende liegt. Danach nur den vorhandenen unsichtbaren Bottom-
   /Top-RETURN-Pfad verwenden. Der DY2-Zweig darf kein sichtbarer Ersatzflug mehr sein.
4. `fireevents.attack_tick` weiterhin einmal pro tatsächlich ausgespieltem Punkt;
   auf einem terminalen/offscreen-Endpunkt keine neue Schussplanung oder neue
   Schussschwellen erzeugen. Die verbrauchten Werte bleiben0. Bei vollem Pool
   bleibt ein verbrauchtes Ereignis verbraucht, keine Wiederholung am Bytewrap.
5. `audio8.attack`, `fireevents.attack_plan` und der maximal3-Angreifer-Zähler
   werden ausschließlich am echten Start behandelt. Ein wiederholtes Muster
   gehört weiterhin zu **demselben** ATTACK-Zustand desselben Gegners.

Das ist ein Verhaltenvorschlag, kein KickAssembler-Patch. Ein bloßes Ersetzen von
`phase=5` durch `cursor=0` genügt **nicht**: Mit dem bisherigen Bottom-Latch würde
der Gegner nach dem Austritt weiter unbegrenzt Originalbytes konsumieren und
nie den Rückkehrpfad erreichen. Die Austrittsentscheidung gehört dazu.

Es werden keine350-Punkte-Amiga-Puffer benötigt. Alle gepackten Kurven sind höchstens
217 Bytes; der vorhandene Bytecursor reicht, weil er **pro Muster** zurückgesetzt
wird. Ein kumulierter Angriff kann298 oder mehr Updates dauern, ohne dass hierfür
ein kumulierter Bytecursor eingeführt werden muss. Fremde/beschädigte Datensätze
brauchen trotzdem die bestehenden Boundschecks; kein unbewiesener unendlicher Loop.

### Koordinatenentscheidung vor einer Originaltreue-Behauptung

**Empfohlene kleine Portkorrektur:** aktuelle Formationsgeometrie, ursprüngliche
Attack-Deltas und aktuelles Playfield beibehalten, Muster bis zum vollständig
unteren Austritt Y≥200 wiederholen. Danach die bestehende Port-Rückkehr ab−16
beibehalten. Das erfüllt die beobachtete fortgesetzte Flugfigur im MEGA65-
Playfield und verändert weder ENTRY-B2 noch Formation oder RETURN.

**Grenze dieser Empfehlung:** Originalgenerator216 und Port200 sind verschiedene
Koordinatenregeln. Stage9a nutzt `rawY − level.y_shift`; für Level4 ist
`level.y_shift=26`. Die native Schwelle216 würde dann bei Port-Y190 liegen,
nicht200. Ein unbesehenes Übernehmen von216 oder ein pauschales ATTACK-Y−16 wäre
falsch; letzteres gehört insbesondere **nicht** zur bestätigten ENTRY-B2-Korrektur.
Eine exakt originalzeitige Endschwelle würde in diesem Beispiel Port-RETURN
starten, während ein16-Pixel-Pixie noch teilweise im Playfield liegt. Sie wird
hier nicht als gleichwertig empfohlen. Für pixel-/zeitgleiche Originalabbildung
wäre eine gesonderte gemeinsame Koordinaten-/Clippingentscheidung nötig.

Auch das native X-Clamping ist ein belegter weiterer Unterschied, aber keine
Voraussetzung für das Schließen der gefundenen Paketend-Lücke. Die aktuelle
signed Offscreen-/Clippingdarstellung soll im kleinen Fix unverändert bleiben.
Ein späterer exakter Clamp müsste **getrennte Roh-/Ausgabekoordinaten** verwenden:
Der native Puffer rechnet mit unclamped X weiter. Jedes Schritt-X im Port direkt
zu clampen würde dagegen spätere Bewegungen verändern.

## Sonderfälle und weitere Entscheidungen

- Level1/3 haben explizit horizontal gespiegelte Bytefolgen; kein neues Spiegeln
  am Wrap. `entry.e_mirror` in Stage9a kopiert Koordinaten in die Pixie-Arrays;
  der Name bedeutet keine zusätzliche geometrische Links-/Rechts-Spiegelung.
- Actoren aus demselben Kurventyp beginnen an unterschiedlichen Formations-Y;
  daher unterschiedliche Original-Pufferlängen. Keine globale Kurvenlaufzeit.
- Natürliche negative Y-Werte sind im vorhandenen Datenbestand vor dem Marker
  nicht vorhanden. Für spätere Fremddaten nicht mit einem Endmarkerbyte verwechseln.
- Die Ein-Byte-Kurven25/50/99/100 lassen sich nun durch Originalcode erklären.
  Die bestehende Angriffssperre kann in einem **späteren** Auftrag separat bewertet
  werden; sie wird in dieser Analyse nicht aufgehoben.
- Tod wechselt State4 und beendet Bewegung; kein Cursorwrap darf einen zerstörten
  Gegner wieder aktivieren. Rückkehr muss weiter das aktuelle driftende Ziel nutzen.
- Die ursprüngliche Schussplanung und Soundereignisse bleiben unverändert; eine
  verlängerte sichtbare ATTACK-Zeit ist kein Anlass für neue Feuerereignisse.

## Vorgeschlagene Abnahme einer späteren Implementierung

1. Level4 linke/rechte und hohe/tiefe Slots: Figuren über Punkt43 hinaus fortsetzen,
   kein vertikaler Ersatzflug, keine Sprünge an Cursor0, Austritt/RETURN einmalig.
2. Level1/2/3/5/47/56: auch Austritt **vor** dem ersten gepackten Ende, mehrere
   Deskriptoren, signed seitliches Clipping und unabhängige gleichzeitige Angreifer.
3. Schuss-/Sound-Trace pro Actor: genau ein Startsignal/Schussplan pro ATTACK,
   maximal1/2 geplante Schüsse insgesamt, kein Retry bei vollem6er-Pool.
4. Tod kurz vor/nach Musterwrap, letzte Explosion/automatischer Levelwechsel,
   Bonusfortschritt, Wiedereinordnung in bewegte Formation; alles übrige Stage9a.
5. WinUAE-Originaltrace mit Breakpoints aus dem Hauptbericht gegen die Simulation
   prüfen, dann XEMU-Sicht-/Hörabnahme. Bisher keine solche Emulatorprüfung behauptet.

**Offen zur Benutzerprüfung:** Freigabe einer eigenen Implementierungsstufe mit
der kleinen Portkorrektur. Stage9a Stable und ihre Artefakte bleiben unverändert.
