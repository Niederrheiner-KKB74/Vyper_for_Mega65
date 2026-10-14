# Stage7b5a — Issue #63 — TESTBUILD, nicht Stable

Vollständiges Diskettenimage: **VYPER_STAGE7B5A.d81** (819200 Bytes).
Enthält STAGE7B5A als PRG und alle sechs SEQ-Dateien: VYTI, VYMN, VYLV,
VYGR, VYCL und VYSH.DAT. Kein Nachladen weiterer Dateien erforderlich.

In XEMU als Laufwerk8 mounten:

```basic
LOAD"STAGE7B5A",8
RUN
```

Joystick **Port2**. Originaltitel während des Ladens, danach Startmenü;
INITIAL LEVEL wählen und F1. X kehrt nach BASIC zurück.

Bitte besonders Level1,3,29,54 vergleichen: individuelle ENTRY-Countdowns,
ein/zwei ATTACK-Schwellen, maximal sechs Gegnerprojektile, keine
Wiederholung verlorener Ereignisse. Projektilbewegung/-grafik und
Angriffsplaner bleiben aus Stage7b4 erhalten. Original-DY wird nur gespeichert.

Sicherheitsfall: In Level46 starten vier Formationsplätze bei Original-Y178/195.
Deren Angriffe laufen unverändert, planen jedoch keine ATTACK-Schüsse,
weil die Originalformel dort keine positive Modulusgrenze hat.

Automatische Prüfung und technische Grenzen:
[Dokumentation](../../docs/stage7b5a_original_fire_events.md),
`test-report.json`, `event-measurements.json`, `memory-map.txt`.
Kein XEMU-/WinUAE-Lauf durch Codex; Benutzerabnahme ausstehend.

Rebuild aus dem vollständigen Repository mit den unveränderten Originalassets:

```sh
python tools/build_stage7b5a.py --kickass /path/to/KickAss.jar
```

`SHA256SUMS.txt`: deterministische Builddateien.
`DELIVERY_SHA256SUMS.txt`: zusätzlich Messungen, Testprotokoll und ZIP.
