# Speicherbelegung – bestätigter Stage-3a-2-Test

| Adresse | Verwendung | Status |
| --- | --- | --- |
| `$2001` | BASIC-65-Startzeile des Testprogramms | Stage 3a-2 |
| `$2100` | Maschinenprogramm (SYS 8448) | Stage 3a-2 |
| `$6000` | SEQ-Lesepuffer (256 Byte) | Stage 3a-2 |
| `$6100` | DMA-Rücklesepuffer | Stage 3a-2 |
| `$7000` | Level-1-Datensatz (849 Byte) | Stage 3a-2 |
| `$20000-$3FFFF` | ROM-Bereich; **nicht** als freies Daten-RAM verwenden | Fehlerursache frühere Stage 3a-2 |
| `$40000-$53F80` | VYLV.DAT, 81.793 Byte (Endadresse inklusiv) | erfolgreich getestet |
| `$54000-$5B8A7` | VYGR.DAT, 30.888 Byte (Endadresse inklusiv) | erfolgreich getestet |

Die Speicherbelegung der Stage-2ja-Engine ist separat aus deren ASM zu übernehmen; die oben genannten niedrigen Adressen gelten nur für das unabhängige Loader-Testprogramm.

Level-1-Datensatz: Quelle `VYLV.DAT` Offset `$328`, Länge `$351`, Anfangsbytes `01 00 02 16 10 00 02 00`.
