# Diagnosebelege nach Stage10a1-HW2

Stand: 18.10.2026. Basis ist main nach PR99, Commit
`df52834b94a69f3c4909b6748974b20f6e77f598`. Dieser Konsolidierungsstand wird
als separater Entwurfs-PR zur Prüfung vorgelegt. Er ändert keine Spielengine,
Originalassets, AGENTS-Regel oder vorhandenen main-Releases. Die alten PRs
90/92/94/97/98 bleiben bis zu einer gesonderten Entscheidung offen.

## Was übernommen wird

313 Dateien aus den Diagnose-Branches; für jede Datei hält
[sources.json](sources.json) Ursprungscommit und Git-Blob-SHA fest.
291 Dokumentations-, Mess- und historische Release-Dateien werden unverändert
übernommen und beim Bauen erneut gegen die ursprünglichen Git-Blobs geprüft.
Aktive Werkzeug-/Test-/ASM-Kopien werden gezielt repariert. Die Zuordnung zu
den ursprünglichen Quellständen bleibt im Manifest erhalten.

- PR90: `6fd56b3000d56c8c0a6d274d3076de72b62be523`.
- PR92: `17d329f2ce7f002bd20df3441ec30d564dd64cb3`.
- PR94: `fd6214c1c6be1adcedea095b0ebd474288a83403`.
- PR97: `7e7f2f93682a20d9861580d87a54616dc03ae5e7`.
- PR98: `3615877fe63ae64b2b831cf019f999151eb667fe`.

Die letzte Audio-Diagnose enthält die vorherigen Diagnosebelege kumulativ;
die zusätzlichen GOTOX-Dateien werden aus PR97 ergänzt. Es werden keine alten
PRs gemergt. main-Dokumente aus den alten Branches werden nicht zurückkopiert.
Die versionsabhängigen lokalen XEMU-Steuerskripte werden nicht als aktuelle
Prüfwerkzeuge übernommen; die ursprünglichen Laufberichte bleiben erhalten.

## Einordnung nach HW2

| PR | Durch HW2 erledigt | Bleibender Wert / Grenze |
|---|---|---|
| [90](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/pull/90) | Produktiver Geometriefehler | [Register-/Hardwarevergleich](../stage10b1_user_hardware_findings.md); gleiche Werte beweisen keine gleiche Darstellung |
| [92](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/pull/92) | Entscheidung über produktive Pufferkorrektur | [Neun bytegleiche Speicherregionen](../stage10b1a_user_findings.md); NORRDEL allein korrigierte die falsche H640-Geometrie nicht |
| [94](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/pull/94) | Allgemeine Ursachenforschung für den Spielfehler | [Korrigierte Mono-Geometrie und PRE/PST-Auswertung](../stage10b1b_hardware_results_20261017.md); Export-/Wiederaufbaueffekt nicht separat durch HW2 erklärt |
| [97](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/pull/97) | H320/CHRXSCL120/logische GOTOX integriert | [Core-/XEMU-Belege und Grenzkoordinaten](../stage10b1c_h320_gotox_test.md); isolierte A/B-Hardwareabnahme weiterhin nicht dokumentiert |
| [98](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/pull/98) | CURRENT Low/High/Bank und D711-Maskierung integriert | [Sentinel-/Replay-Test und Registersemantik](../stage10b1d_audio_dma_latch.md); isolierte A/B-Hörabnahme weiterhin nicht dokumentiert |

Die HW2-Benutzerbestätigung vom17.10.2026 bezieht sich auf Core0.97 aaf4542,
ROM920413, PAL und den dort dokumentierten Spielbuild. Sie wird nicht in eine
nachträglich durchgeführte Abnahme jedes Diagnoseprogramms umgedeutet.
Der PRE/PST-Spezialbefund aus PR94 ist kein nachgewiesener weiterer HW2-Spielfehler
und kein automatischer Blocker der nächsten Stage.

## Reparaturen an den aktiven Werkzeugen

1. `compare_stage10b1_registers.py` erhält jetzt D012/D011 aus jedem
   Phasenstart und meldet Änderungen separat als `phase_context_differences`.
   Registerdifferenzen und der erste stabile Divergenzzeitpunkt bleiben getrennt.
   Das alte Binärformat wird unverändert gelesen; vorhandene Berichtsdateien
   werden nicht überschrieben. Der spätere Stage10b1a-Parser besaß diese Funktion
   bereits und bleibt unverändert.
2. `src/tests/stage10b1{,a,b}.asm`: CLOSE auf LFN2 nur nach erfolgreichem OPEN,
   anschließend Eigentumsflag löschen. Erfolgs-, CLOSE-Fehler- und DOS-Fehlerwege
   bleiben getrennt. Ein bereits vom BASIC-Aufrufer benutzter Kanal2 wird bei
   fehlgeschlagenem OPEN nicht geschlossen. Historische PRG/D81/ASM-Kopien unter
   releases/ bleiben unverändert; reparierte PRG/D81 werden separat gebaut.
3. Gemeinsame Schutzprüfung in `tools/diagnostic_baseline.py`: HW2-main ist
   erreichbarer Vorfahr; dessen vorhandene Quellen/Assets/Tools/Releases und
   AGENTS.md sind geschützt. Die alten `BASE`-Felder bleiben historische
   Provenienz in den Diagnoseformaten; sie werden nicht mehr für Git-Abfragen
   oder den Build-Schutz benötigt. Ein vollständiger Checkout des neuen Branches
   braucht keine alten Diagnose-Branches. Die ursprünglichen Branches hatten
   ihre Baselines tatsächlich in der Historie; die damaligen Review-Warnungen
   werden daher nicht als nachgewiesener Defekt jener Branches dargestellt.
4. Alle fünf Builder schreiben standardmäßig nach `build/diagnostics/stage10b1*`.
   Ziele in releases/, docs/, src/ oder tools/ werden abgelehnt. Externe
   temporäre Buildziele sind erlaubt. Auch die PRE/PST-Analyse schreibt ihre
   neuen Ergebnisse standardmäßig nach build/diagnostics/hardware_comparison
   und darf das Belegarchiv nicht überschreiben.
5. Die bestehenden Tests verwenden die frisch gebauten Artefakte. Eine alte
   falsche Mono-Breitenannahme im Stage10b1b-Test und in dessen erzeugten
   Budget-Metadaten ist an die dokumentierte H640/Scale60-Geometrie angepasst:
   Mono16/NCM32 native Pixel. Die historischen Szenen einschließlich ihrer
   falschen eingeblendeten Breitenangabe bleiben zum Vergleich erhalten;
   sie sind keine Vorlage für die nächste Spielstage. Zusätzliche Regressionstests
   führen die reparierten Cleanup-Opcodes aus und prüfen Build-/Archivschutz.

## Reproduktion

Voraussetzungen: Python3, Pillow, py65==1.2.0, Java und offizieller KickAssembler5.25.
Die bekannte JAR-SHA256 wird durch die Builder geprüft. Bezug:
[offizielle KickAssembler-Seite](https://theweb.dk/KickAssembler/).

```sh
python tools/validate_diagnostics.py --kickass /path/to/KickAss.jar
```

Der Befehl assembliert alle fünf Programme, reproduziert jeden Build unabhängig,
führt die Hosttests aus und wiederholt die historische PRE/PST-Analyse mit den
gesicherten Eingabedateien. Ergebnisse unter `build/diagnostics/`:

- `stage10b1*`: PRG, D81, ASM, Includes, Symbole und SHA256SUMS.
- `host_tests.txt` und `validation.json`: aktuelles Prüfprotokoll und Buildhashes.
- `hardware_comparison/`: neue Auswertung der unveränderten Originalmessungen.

Einzelne Tests können `DIAGNOSTIC_BUILD_ROOT` auf ein anderes Buildwurzelverzeichnis
setzen; Rebuild-Tests benötigen außerdem `KICKASS_JAR`. Der Gesamtbefehl setzt
beides selbst. Die unveränderten alten Anleitungen dokumentieren historische
Buildziele; für den aktuellen Stand gilt dieser Einstieg.

Die Hosttests modellieren CPU-/Register-/DOS-Verhalten begrenzt. Es wurde kein
neuer XEMU-, Hardware-, Foto- oder Hörtest durchgeführt. Die reparierten
Diagnosebuilds erhalten deshalb keine neue Hardware-Stable-Kennzeichnung.

## Ergebnis der Prüfung

- Alle fünf Diagnoseprogramme regulär assembliert und jeweils unabhängig
  bytegleich reproduziert; PRG und D81 vollständig geprüft.
- 52 Hosttests bestanden, einschließlich der gezielten neuen Regressionstests.
- Frischer Single-Branch-Checkout ohne die alten Diagnose-Basiscommits
  6fd56b3, 17d329f und fd6214c: derselbe Build-/Test-/Analyseablauf bestanden.
- 291 archivierte Dokumentations-/Mess-/Release-Dateien unverändert.
- Historische Hardwareanalyse erneut ausgeführt: 24 Schnappschüsse,
  zwölf PRE/POST-Paare und16Originalbilder validiert.

[Maschinenlesbarer Nachweis und Artefakthashes](validation.json),
[vollständiges Hosttest-Protokoll](host_tests.txt).
Die frisch gebauten 10b1/10b1a/10b1b-PRGs enthalten den reparierten Cleanup und
unterscheiden sich von den historischen Messprogrammen. Die frisch gebauten
10b1c/10b1d-PRGs und D81 sind mit ihren historischen Referenzen bytegleich.
Die alten Messdaten werden weiterhin anhand ihrer ursprünglichen Programme
interpretiert, nicht anhand eines rückwirkend ausgetauschten PRG.

## Vor der nächsten Spielstage

HW2 bleibt die technische Spielbasis. Koordinatengrenzen, CURRENT-Schreibfolge,
Sentinel-/Replay-Verhalten und D711-Maskierung bleiben als gezielte Prüfwerkzeuge
verfügbar. AGENTS-Regel19 verlangt weiterhin echte Hardwareabnahme neuer Grafik-
und Soundänderungen. Keine pauschale neue Registerkorrektur aus alten Messdifferenzen
ableiten. PR94 nur bei erneutem Export-/Wiederaufbauproblem gezielt fortführen.
Über Merge und Schließen der alten PRs entscheidet der Benutzer nach dieser Prüfung.
