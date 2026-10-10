# Stage 3b-5c – XEMU-Testrelease (nicht Stable)

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

14 neue Hosttests bestanden. Keine behauptete eigene XEMU-Abnahme.
Originale acht Amiga-Explosionsframes mit Masken/NCM-Konvertierung im Repository;
keine Ersatzgrafiken. Stabile Stage 3b-5b bleibt unverändert.

[Technik und Koordinaten](../../docs/stage3b5c.md),
[Testprotokoll und Abnahme](../../docs/stage3b5c_xemu_test.md).
Stage 3b-5c erst nach ausdrücklicher Benutzerbestätigung als Stable markieren.
