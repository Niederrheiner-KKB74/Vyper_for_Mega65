# Stage10a3 – Formationsstart, Angriffe während des Einflugs, Explosionsfarben

Basis: Stage10a2 (`main` 475355c, vom Benutzer nach Hardwaretest gemergt).
Separate Quellen `src/engine/stage10a3*.asm`, `src/tests/stage10a3*.asm`,
Build `tools/build_stage10a3.py`, Release `releases/stage_10a/stage10a3/`.
Stage10a2 und alle älteren Stable-Stände bleiben unverändert; das Buildskript
prüft das zusätzlich gegen Commit 475355c.

## Benutzerbefunde (Vergleich mit dem Amiga-Original, 22.10.2026)

1. Die Rechts-Links-Bewegung der Formation beginnt im Original, sobald der
   erste Gegner seinen Platz erreicht hat – nicht erst nach dem kompletten Aufbau.
2. Im Original starten Angriffe bereits während des Einflugs. Bei Levels mit
   langem Einflug ist das ein deutlicher Gameplay-Unterschied.
3. Explosionen von Gegnern haben die Farben des Gegners im jeweiligen Level;
   die Player-Explosion bleibt grau.

## Ursache im Code

**Punkte 1 und 2:** `attack.a_postframe` setzte `a_ready` erst, wenn jeder
lebende Gegner in `e_phase=3` war (Aufbau-Barriere aus Stage4b-2). Dasselbe Flag
sperrt sowohl das Pendeln (`a_preframe`) als auch den Angriffs-Scheduler.

**Punkt 3:** `pal.glyph_colour` schrieb für Explosionen in privaten
Pixiepuffern (`c_es=4`) Color-RAM-Byte `$00`, also Bank1-Einträge 0..15 mit der
festen Level-1-Graupalette aus Stage5b.

## Änderungen

| Stelle | Stage10a2 | Stage10a3 |
|---|---|---|
| `a_postframe`-Barriere | alle lebenden Gegner in Formation | erster lebender Gegner mit `c_es=1` und `e_phase=3` |
| Pendeln | nach komplettem Aufbau | ab erster Ankunft |
| Angriffs-Countdown (100 Frames, dann 30) | nach komplettem Aufbau | ab erster Ankunft |
| `glyph_colour`, private Puffer | Explosion `$00`, sonst `$10` | immer `$10` |

Unverändert: höchstens 3 gleichzeitige ATTACK, Intervalle 100/30 Frames,
Auswahl nur aus `FORMATION` (`c_es=1`, `e_phase=3`), Einflugkurven und
-timing, Schussregeln, Player-Explosion (direkte Glyphs `$305..$31F`, `$00`).

**Ankunft in bewegter Formation:** Nach dem Ende der Einflugkurve folgt wie
bisher RETURN (`e_phase=2`), das jedes Frame ±1 je Achse auf
`e_tx + a_offset` zuläuft. Das Pendeln bewegt den Slot nur 1 Pixel je 2
Frames, RETURN holt also immer auf; höchstens 8 zusätzliche Frames bei
maximalem Offset. Keine Kurvendaten geändert.

**Explosionsfarben:** Die sieben Explosionsframes verwenden die Nibbles
2/5/7/8, also dieselbe Konvention `Nibble = Amiga-Plane + 1` wie die Gegner.
Mit `$10` landen sie auf den Level-Einträgen 18/21/23/24
(Originalwörter 1/4/6/7). Die direkte Glyph-Renderroutine `c_render_enemy` hat
keinen Aufrufer; direkte Explosionsglyphs werden nur für den Player gezeichnet.

**Adressen:** Beide Routinen sind durch NOP-Auffüllung exakt so lang wie in
Stage10a2 (30 bzw. 16 entfernte Bytes ersetzt). Alle nachfolgenden Adressen
bleiben gleich.

## Offen / Abnahme

- Assembly und D81 stehen noch aus (KickAssembler 5.25 in dieser Umgebung
  nicht verfügbar). Build: `python3 tools/build_stage10a3.py --kickass <KickAss.jar> --zx0 <zx0>`.
- Abnahme auf echter Hardware (Regel19): Pendelbeginn bei erster Ankunft,
  Angriffe während langer Einflüge, Gegnerexplosion in Levelfarben in
  mehreren Levels, Player-Explosion weiterhin grau.
- Ob das Original die Zahl der Angreifer während des Einflugs begrenzt oder
  einen anderen ersten Countdown verwendet, ist nicht belegt; die bestehenden
  Testparameter (3 / 100 / 30) wurden beibehalten.
