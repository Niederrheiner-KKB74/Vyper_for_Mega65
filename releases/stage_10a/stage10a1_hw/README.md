# Stage10a1-HW (Hardwaretest)

Revision 2. Basis: Stage10a1 (`releases/stage_10a/stage10a1`), byte-genau gepatcht mit `tools/patch_stage10a1_hw.py`.
Start: `LOAD "STAGE10A1",8` und `RUN`, Diskettenname `VYPER 10A1 HW2`.

1. Audio-DMA: `$D72A/$D72B` vor `$D72C` schreiben. Auf der Hardware übernimmt erst `$D72C` die Adresse.
2. Audio-Init: von `$D711` nur Bit 7 prüfen (Bits 6 und 0–2 sind Statusbits).
3. RRB-Doppelpufferung (`$D051` Bit 7 = 0): Die Hardware las den Zeilenpuffer, während er noch gefüllt wurde; links stehende Pixies hatten dadurch schwarze Linien.
4. Spielbildschirm: H320 + `$D05A=120` statt H640 + `$D05A=60`; alle GOTOX-Werte in logischen
   320er-Koordinaten (HUD 240, Leben 245/262/279/296 und 316, GAME OVER 84, GET READY 102/104).
   Die Hardware skaliert den kompletten RRB-Zeilenpuffer einschließlich GOTOX mit CHRXSCL, XEMU nur die Glyphen.

Nicht mit KickAssembler gebaut; die gleichen Änderungen stehen in den Quellen von `src/engine`.
