# Originalexplosionen – sieben Frames, nicht acht

Der Benutzer bestätigt nach dem XEMU-Test, dass es sieben Explosionsframes
gibt. `explosion_amiga_planes.txt` wird als ursprünglicher verlustfreier
Extraktionsdatensatz unverändert aufbewahrt. Seine Überschrift und der als
Frame 7 bezeichnete Record sind falsch zugeordnet: Deskriptor $3827A ist die
Playergrafik (gleiche Maske; 238/256 Pixel stimmen mit dem freigegebenen
Player überein). Records 0–6 sind die sieben Explosionen.

`build_explosion_assets.py` konvertiert die Rohrecords unverändert, markiert
Record 7 in `conversion.json` als ausgeschlossen und verweigert seine
Auswahl für die Explosion. `explosion_07_ncm.bin` dient nur der Nachvollziehbarkeit
und ist nicht in PRG/D81 eingebunden. Keine Ersatzgrafik wird erzeugt.

Sieben Frames × drei 50-Hz-Ticks = 21 Ticks, für Player und Gegner identisch.
Diese Abspielgeschwindigkeit behauptet nicht das Original-Amiga-Timing.
