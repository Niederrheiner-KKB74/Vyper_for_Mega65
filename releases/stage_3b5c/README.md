# Stage 3b-5c – stabile Referenz `stage3b5c-stable`

`VYPER_STAGE3B5C.d81`: PRG `STAGE3B5C` und unveränderte SEQ-Dateien
`VYLV.DAT`, `VYGR.DAT`. D81 einlegen, `LOAD "STAGE3B5C",8`, `RUN`.

Joystick/Feuer unverändert. T: Testangriff umschalten; E: Teststatus ENTRY/ATTACK.
X: Exit nach BASIC. Nach vollständiger letzter Explosion: GAME OVER; R für
Neustart mit erhaltenem Highscore, X für Exit, andere Tasten ignoriert.

Quellcode, Symbole, Assemblykarte, Buildbericht und SHA256SUMS beiliegend.
Reproduzierbarer Build aus dem vollständigen Repository:

```sh
python tools/build_stage3b5c.py --kickass /pfad/zu/KickAss.jar
python -m unittest discover -s tests -p test_stage3b5c.py -v
```

14 neue Hosttests bestanden. XEMU-Abnahme vom Benutzer am 10.10.2026 bestätigt; kein eigener vollständiger Emulatorlauf.
Originale sieben Amiga-Explosionsframes mit Masken/NCM-Konvertierung im Repository;
keine Ersatzgrafiken. Stabile Stage 3b-5b bleibt unverändert.

[Technik und Koordinaten](../../docs/stage3b5c.md),
[Testprotokoll und Abnahme](../../docs/stage3b5c_xemu_test.md).
Die ausdrückliche Benutzerbestätigung liegt vor. ASM, PRG, D81 und Prüfsummen
bleiben gegenüber dem bestätigten Testbuild unverändert.

Korrigierter Build: Kein Player-Datensatz in der Explosion; drei Sekunden
Unverwundbarkeit mit freier Joystickbewegung. Feuer bleibt währenddessen gesperrt.
