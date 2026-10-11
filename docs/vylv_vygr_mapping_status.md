# VYLV → VYGR: Zuordnungsstatus (10.10.2026)

## Verbindliche Korrektur

**VYLV `graphic_type = 14` → VYGR-Gegnertyp 15 (1-basierte Typzählung).**

Der Benutzer hat diese Beziehung anhand des laufenden Originalspiels in WinUAE visuell bestätigt und die vorherige Aussage `14 → 31` ausdrücklich zurückgenommen. **Weder `14 → 31` noch `14 → 12` ist korrekt.**

Level 1 verwendet laut rekonstruiertem VYLV-Record `graphic_type = 14`; deshalb muss bei der künftigen Implementierung von Level 1 **VYGR-Typ 15** angezeigt werden. Dieser besitzt nach der bisherigen Extraktion **6 Animationsframes**.

## Wichtig: Die übrige Tabelle ist noch nicht verifiziert

Die ältere Umrechnungsregel in `docs/stage3b2.md` (`0,1 → 12`, `14 → 12`, sonst `index - 1`) ist **keine zuverlässige, aus dem Amiga-Original nachgewiesene Abbildung**. Sie darf nicht ungeprüft für weitere Levels übernommen werden. Insbesondere die Beschreibung `14 → 12` als „bestätigte Korrektur“ ist durch die neuere visuelle Prüfung widerlegt.

Bisher **einziger individuell bestätigter VYLV→VYGR-Eintrag**:

| VYLV graphic_type | VYGR-Typ (1-basiert) | Status | Grundlage |
|---:|---:|---|---|
| 14 | **15** | **Bestätigt** | Visueller Vergleich des Benutzers mit Level 1 des Original-Amiga-Spiels |

**Alle anderen VYLV-Indizes: noch offen.** Die Zuordnung von 32 Startbildschirm-Gegnergrafiken zu VYGR-Typen ist nicht automatisch eine Zuordnung der VYLV-Indizes. Ohne Analyse der originalen Descriptor-Auswahlroutine oder weitere verifizierte Vergleiche keine weiteren Zuordnungen behaupten.

## Technische Umsetzung in nächster Stage

1. **Stage 3b-4a bleibt unverändert und stabil.** Diese Datei dokumentiert nur die neuen Erkenntnisse.
2. In einer Folgestage die bisherige pauschale Zuordnungsformel durch eine **explizite Lookup-Tabelle** ersetzen.
3. Eintrag `14 → 15` als bestätigten Kontrollfall eintragen; unbekannte Einträge mit Status „unbestätigt“ versehen, nicht stillschweigend als korrekt behandeln.
4. Bei jedem Level die Original-VYLV-Indizes beibehalten. Die Übersetzung zum VYGR-Typ muss zentral und prüfbar erfolgen.
5. Möglichst die Amiga-Routine rekonstruieren, die den Level-Grafikindex in einen Gegnerdeskriptor/Framezeiger umsetzt; anschließend die vollständige Zuordnung aller verwendeten Indizes prüfen.
6. Bei Zählweisen strikt zwischen **VYLV-Bytewert**, **VYGR-Typnummer (1-basiert)** und **internem Arrayindex (0-basiert)** unterscheiden. Nicht ohne Dokumentation um eins korrigieren.

## Weitere gesicherte Beobachtung (Punkte)

Die Punktewerte hängen nach Beobachtung des Benutzers ausschließlich von der Level-Zehnergruppe ab:

- `k = (level - 1) // 10` (für Level ≥ 1)
- `formation_points = 100 + 50*k`
- `attack_points = 175 + 50*k`

Diese Werte sind **nicht** aus `VYLV.DAT` auszulesen. Die HUD-Werte `FORMATION 100` / `ATTACK 115` aus dem frühen Mockup waren nur Testwerte; für Level 1–10 lautet Attack korrekt **175**.

## Datenbasis für weiterführende Untersuchung

- WinUAE-Startbildschirm-Savestate `Vyper_Startscreen.uss` (32 sichtbare Gegner; nicht alle 36 Typen)
- Originaldiskette `VYPER.ADF` (u. a. `Forme`, `Level`, `Attack`)
- Extrahierte `VYLV.DAT` / `VYGR.DAT`
- Die Dateien sind ggf. als Chat-Anhänge verfügbar, **nicht voraussetzen, dass sie im GitHub-Repository liegen**.

**Keine automatische Codeänderung durch dieses Dokument.** Vor der nächsten Gameplay-Stage den bestätigten Eintrag integrieren und die restlichen Indizes gezielt verifizieren.

## Umsetzung in Stage 3b-5b

Die Engine von Stage 3b-5b verwendet die zentrale Tabelle
[`assets/vylv_vygr_mapping.json`](../assets/vylv_vygr_mapping.json).
Der Builder erzeugt daraus sowohl Typnummern als auch Bestätigungsflags.
Einzig Index 14 ist bestätigt und verwendet **Typ 15, internes Verzeichnisindex 14,
sechs Originalframes**. Alle übrigen Einträge behalten ausschließlich den historischen
Fallback und tragen `confirmed: false`. Die sechs Frames werden automatisch gegen
die Originaldatei geprüft. Stabile Quellen und Release-Dateien von Stage 3b-4a bleiben
unverändert; die alten 14→12/31-Aussagen dürfen für neue Stages nicht verwendet werden.

Die oben separat beschriebenen echten Punktewerte sind weiterhin eine Beobachtung für
eine spätere Gameplay-Stage. Stage 3b-5b implementiert ausdrücklich noch keine Treffer-
oder Scorelogik und verändert die bisherigen HUD-Mockupwerte nicht.
