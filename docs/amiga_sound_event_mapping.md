# Originale Soundereignisse und38-Typen-Zuordnung

Issue67, **Analyse**, keine Spielintegration. Evidenzgrade wie im
[Hauptbericht](amiga_sound_engine_analysis.md). Alle folgenden IDs/Pointerpfade
sind **statisch bestätigt**, akustische Abnahme und aktive Gameplay-Traces sind offen.
Maschinenlesbar: [156 Ereigniszeilen](amiga_sound_evidence/events.csv),
[38 Typrecords](amiga_sound_evidence/enemy_types.csv),
[24 Samplebeschreibungen](amiga_sound_evidence/samples.csv).

## Ereignisse, Ursprung und gegenseitige Verdrängung

Die folgenden Adressen beziehen sich auf die gespeicherte USS-CODE-Abbildung.
Dump-/Dateioffsets und Instruktionsbytes stehen vollständig im verlinkten Disassembly.

| Ereignis | ID-Quelle | Stelle der ID-Zuweisung | Paula-Paar | Panning-X |
|---|---|---|---|---|
| Gegner beginnt ATTACK |Actor+`$90`|`$C0D21E`|0/1|Pointer auf Enemy-X (Actor+`$10`)|
| Gegner feuert |Actor+`$8C`|`$C0D63C`|2/3|Pointer auf den **Projektilrecord-X**, nicht den Schützen|
| Gegner wird getroffen/zerstört |Actor+`$8A`|`$C0D332` und `$C0D3B4` (zwei Playerschüsse)|2/3|Pointer auf Enemy-X|
| Player feuert |17|`$C0D10A`|0/1|Pointer auf den gestarteten Player-Schuss-BOB-X|
| Player wird zerstört |19|`$C09498`|0/1|Pointer auf Player-Hardware-Sprite-X|
| Levelübergang früh |24|`$C08F52`|0/1|Stack-WORD120, also Mitte|
| Levelübergang vor Rechteckphase |22|`$C09060`|0/1|dasselbe Stack-WORD120|
| Zusätzlich: Gegner beginnt ENTRY |Actor+`$8E`|`$C0D41C`|0/1|Pointer auf Enemy-X|

Gegnerereignisse sind durch den jeweiligen Busy-Countdown gesperrt. Mehrere
zugelassene Ereignisse innerhalb eines Updates können denselben Pending-Slot
überschreiben. Es gibt keine FIFO. Player/Übergang überschreiben ohne Busyprüfung.
Beim Gegnerschuss wird trotz Busy der Panningpointer neu gesetzt; bei komplett
vollem6er-Projektilpool entsteht dagegen überhaupt kein Soundereignis.
Dies ist im Hauptbericht samt Codeadressen beschrieben.

Die Stereo-Lautstärke ist nicht als konstanter Wert zu speichern:
`left=240/div-floor(clamp(X,0,240)/div)`, `right=floor(clamp(X,0,240)/div)`.
Paar0/1 ist L/R, Paar2/3 R/L. Teiler, PER und Busywert hängen von der Sample-ID ab,
nicht zusätzlich von einer versteckten pro-Typ-Tonhöhentabelle.

## Wichtige Deskriptorgrenze: keine Verschiebung um einen Gegnertyp

**Bestätigt durch `$C0A9B2–$C0ABD8`:** Der Original-Grafikindex wird als Byte
von der geladenen Forme-Typenliste gelesen, mit18 multipliziert und für Grafik-
und Soundfelder verwendet. Der echte Typrecord beginnt bei DATA+`$2BAA`:

| Offset | Inhalt |
|---|---|
|+0|Grafikdeskriptorpointer, LONG|
|+4|Animationsframezahl, WORD|
|+6|Animationszeitparameter, WORD|
|+8|Breiten-/Grafikparameter, WORD|
|+10|Zerstörungs-Sound-ID, WORD → Actor+`$8A`|
|+12|Schuss-Sound-ID, WORD → Actor+`$8C`|
|+14|Einflug-Sound-ID, WORD → Actor+`$8E`|
|+16|Angriffs-Sound-ID, WORD → Actor+`$90`|

Die früheren Grafikextraktoren lesen korrekt den Pointer bei+8 relativ zum
Hilfsanfang DATA+`$2BA2` / Dump`$2DAF2`. **Dessen erste acht Bytes sind nicht die
Soundfelder des folgenden Grafikrecords.** Ein blindes Lesen dort würde die
Soundzuordnung um einen Typ verschieben und bei Index0 sogar`$FFFF` liefern.
Das neue Skript nimmt deshalb den tatsächlichen Recordanfang:
USS`$1ACEA+18*i`, Dump`$2DAFA+18*i`. Der Soundteil liegt bei
DATA+`$2BB4+18*i`; dessen Kopie nach Actor+`$8A` wird bei`$C0AA24–$C0AA32` belegt.

Die38 Grafikpointer/Framezahlen stimmen weiterhin exakt mit der bestehenden
Stage5b-/VYGR-Mappingtabelle überein. Alle2194 Typ-/Angriffsbytes und Koordinaten
aller100 VYLV-Levels wurden zusätzlich gegen das Original-Forme geprüft. Es wird
**keine bisherige Grafikzuordnung geändert**. Indizes6 und11 sind im Original-
Typenbestand vorhanden, kommen aber in den100 Levels nicht vor.

## Zerstörung: charakteristische, aber gemeinsam genutzte Klänge

Die Beobachtung typspezifischer Klänge ist mit dem Code vereinbar. Sie bedeutet
jedoch nicht38 exklusive Samples: Die38 Einträge wählen aus den sechs IDs
**1,3,8,9,18,20**. Gleiche IDs verwenden dieselben Bytes, denselben PER und denselben
Panningteiler; eine zusätzliche typspezifische Pitch-/Synthesestufe ist nicht belegt.
Die Position und mögliche vorzeitige Verdrängung beeinflussen den hörbaren Eindruck.

**Player-Explosion = ID19**, kein Mitglied dieser Gegnergruppe.
Player-Schuss =17. Die vier IDs4/13/14/23 sind unbenutzte Dateisegmente und werden
von keinem der hier rekonstruierten Typ-/Gameplay-Ereignisse angefordert.
Weitere eigene Menü-, Extra-Leben- oder Game-Over-Samples sind im geprüften
Ereignispfad nicht nachgewiesen; dafür werden keine erfundenen Zuordnungen ergänzt.

Für den bekannten Level1-Fall gilt: VYLV14→VYGR15 hat
**Zerstörung3, Schuss2, ENTRY6, ATTACK7**. Alle vier Zuordnungen stammen aus dem
Originalrecord, nicht aus einer gehörten Ähnlichkeit oder einer geratenen Reihenfolge.

## Vollständige Zuordnung

`Gfx` ist der nullbasierte VYLV-/Originalindex, `VYGR` der1-basierte Typ.
Alle vier Sound-IDs sind1-basiert;0 ist nur das leere Pending-Wort.

| Gfx | VYGR | Zerstörung | Schuss | ENTRY | ATTACK |
|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 1 | 10 | 6 | 6 |
| 1 | 2 | 3 | 15 | 6 | 7 |
| 2 | 3 | 8 | 16 | 11 | 6 |
| 3 | 4 | 20 | 2 | 7 | 6 |
| 4 | 5 | 8 | 12 | 11 | 6 |
| 5 | 6 | 9 | 12 | 6 | 11 |
| 6 | 7 | 3 | 2 | 7 | 11 |
| 7 | 8 | 3 | 10 | 6 | 21 |
| 8 | 9 | 1 | 15 | 6 | 11 |
| 9 | 10 | 18 | 15 | 6 | 21 |
| 10 | 11 | 3 | 5 | 7 | 6 |
| 11 | 12 | 3 | 5 | 7 | 11 |
| 12 | 13 | 8 | 10 | 7 | 6 |
| 13 | 14 | 20 | 12 | 6 | 21 |
| 14 | 15 | 3 | 2 | 6 | 7 |
| 15 | 16 | 1 | 16 | 11 | 6 |
| 16 | 17 | 1 | 15 | 11 | 6 |
| 17 | 18 | 9 | 5 | 11 | 21 |
| 18 | 19 | 1 | 2 | 6 | 21 |
| 19 | 20 | 8 | 10 | 11 | 21 |
| 20 | 21 | 9 | 2 | 21 | 7 |
| 21 | 22 | 3 | 2 | 11 | 6 |
| 22 | 23 | 8 | 10 | 21 | 7 |
| 23 | 24 | 20 | 16 | 7 | 21 |
| 24 | 25 | 3 | 5 | 11 | 21 |
| 25 | 26 | 18 | 15 | 21 | 6 |
| 26 | 27 | 9 | 5 | 7 | 11 |
| 27 | 28 | 1 | 2 | 6 | 7 |
| 28 | 29 | 3 | 5 | 7 | 11 |
| 29 | 30 | 8 | 10 | 11 | 21 |
| 30 | 31 | 3 | 15 | 21 | 6 |
| 31 | 32 | 18 | 15 | 6 | 7 |
| 32 | 33 | 20 | 16 | 7 | 11 |
| 33 | 34 | 1 | 5 | 11 | 21 |
| 34 | 35 | 8 | 12 | 21 | 6 |
| 35 | 36 | 18 | 16 | 21 | 7 |
| 36 | 37 | 20 | 2 | 6 | 21 |
| 37 | 38 | 8 | 5 | 11 | 7 |

Die CSV nennt zusätzlich Record-, Grafikdeskriptor-, Sample- und Datei-Adressen.
Keine dieser Tabellen wird in Stage7b5b eingebaut.
