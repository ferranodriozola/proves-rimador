# Pla d'acció: verb + 2 pronoms febles (cas general)

> Document de treball per a la generació amb **dues** pronoms combinats
> (`porta-l'hi`, `renta-te-la`, `treu-l'en`). Continua `pla_un_pronom.md`
> (que tanca la generació amb 1 pronom) i concreta la fase que `pla.md` §2.4
> deixava per a més endavant.

---

## 0. Resum de decisions

| Qüestió | Decisió |
|---|---|
| Quines parelles de pronoms existeixen | Les del **Quadre 8.9** (font aportada per l'usuari, agost del 2026) — no un producte cartesià ni un algorisme derivat |
| Quin verb pot dur quina parella | **Heurística d'unió**: es permet si el verb admet cada pronom per separat (mateix criteri de sobregeneració que P2/P3 al pla d'1 pronom) |
| Fonètica de les parelles | Aproximació pròpia (el quadre només dona l'ortografia), pendent de repàs amb oïda nativa |
| Arquitectura | Mateixos 3 mòduls que la fase d'1 pronom, ampliats: `llicencies.PARELLES`/`permet_parella`, `enclisi._generar_forma_2`, `generar_tot_2_pronoms.py` |

**Volum obtingut: 2.751.676 formes**, 69 fitxers, 220 MB.

---

## 1. El Quadre 8.9

L'usuari va aportar una imatge del "Quadre 8.9 — Combinacions binàries de
pronoms febles" (probablement d'una gramàtica de referència), amb totes les
parelles reals de la llengua i la seva forma exacta darrere del verb. És la
font primària d'aquesta fase: substitueix qualsevol regla derivada per
lògica (la transformació `li`→`hi`, el forçat de forma plena a
`es`/`et`/`em`, l'excepció `el`+`en`) per dades explícites, cel·la per
cel·la.

**69 parelles vàlides** (un cop unificat `els` datiu/acusatiu, que la
llengua distingeix però que a la sortida són la mateixa paraula i el mateix
codi `LS`):

| 1r pronom | 2ns pronoms admesos |
|---|---|
| `es` | `et us em ens li els el la les en hi ho` (12) |
| `et` | `em ens li els el la les en hi ho` (10) |
| `us` | `em ens li els el la les en hi ho` (10) |
| `em` | `li els el la les en hi ho` (8) |
| `ens` | `li els el la les en hi ho` (8) |
| `li` | `els el la les en hi ho` (7) |
| `els` (datiu) | `els el la les en hi ho` (7) |
| `el` | `en hi` (2) |
| `la` | `en hi` (2) |
| `les` | `en hi` (2) |
| `en` | `hi` (1) |

**`li` + `el`/`la`/`els`/`les` es transforma**: el CD passa davant i `li` es
converteix en `hi` (`porta-l'hi`, `porta-la-hi`, `porta'ls-hi`,
`porta-les-hi`). El **codi** conserva sempre la identitat gramatical
original (`li`+`el` → `WM02S2LIEL`, mai `...HIEL`), coherent amb l'exemple
que ja donava `pla_un_pronom.md` §4; només l'**ortografia** surt
transformada.

**`els` datiu ≠ `els` acusatiu com a 1r pronom**: el datiu es comporta com
`li` (7 columnes, mai es transforma), l'acusatiu només admet `hi`/`en`. La
distinció viu només a `llicencies.py` (claus internes `els_dat`/`els_ac`);
la paraula i el codi de sortida són idèntics.

**Els primers pronoms `us`, `ens` i `els` (com a 1r) varien segons si el que
precedeix acaba en vocal o consonant** (`-vos-`/`-us-`, `-nos-`/`'ns-`,
`-los-`/`'ls-`), exactament com ja fa `ENCLISI` per a 1 sol pronom. Quan
això passa, **el segon pronom hi va en la seva forma "nua"** (no lligada):
`us`+`en` = `-vos-en`/`-us-en`, no `-vos-ne`; `us`+`el` = `-vos-el`, no
`-vos-lo`. És literal del quadre, no una regla que s'hagi derivat.

---

## 2. Arquitectura

Reaprofita al màxim la maquinària d'1 pronom, en lloc de duplicar-la.

### `llicencies.py`

- `PARELLES`: el Quadre 8.9 transcrit, `(pronom1, pronom2) -> (escrit,
  fonema)`. Quan la fila varia amb el verb, `escrit`/`fonema` són parelles
  `(consonant, vocal)`.
- `parella_efectiva(p1, p2)`: resol la transformació `li`+CD → CD+`hi` i la
  distinció `els_dat`/`els_ac`; retorna la clau real a `PARELLES` i el
  pronom "net" (sense sufix intern) per a la llicència.
- `PARELLES_VALIDES`: les 69 parelles, en ordre gramatical.
- `permet_parella(lema, p1, p2, persona)`: la **heurística d'unió** — la
  parella es permet si el verb admet cada membre per separat
  (`permet(lema, p, None)`), sense necessitat de dades noves de
  ditransitivitat. Amb persona donada, aplica la concordança existent
  (`MATRIU_PERSONA`) al membre que sigui `es`/`et`/`em`/`ens`/`us`.

### `enclisi.py`

`generar_forma()` deriva ara cap a `_generar_forma_2()` quan rep 2 pronoms:
busca la parella a `llicencies.PARELLES` (via `parella_efectiva`), tria la
variant consonant/vocal si cal amb `acaba_en_vocal()` (la mateixa funció que
ja hi havia), concatena l'ortografia i la fonètica **literalment** (sense
tornar a aplicar les regles de sàndhi de `transcriure()`, que són per a 1
pronom) i compta les síl·labes noves comptant els nuclis vocàlics del
fragment fonètic afegit.

**Limitació coneguda**: la fonètica de les parelles és una aproximació
pròpia construïda encadenant els mateixos fragments d'AFI que ja hi havia a
`FONEMA`, més uns quants fragments nous per a les formes "nues" (`en`→`ən`,
`el`→`əl`, `els`→`əls`, `em`→`əm`, `et`→`ət`, `ens`→`əns`). No s'hi ha
tornat a aplicar cap regla de sàndhi (semivocalització, sonorització...):
en un grapat de casos limítrofs (`li`+`hi` = `-li-hi`, on la `i` final de
`li` topa amb la `i` de `hi`) la transcripció pot no ser exacta. Es
recomana un repàs amb oïda nativa abans de donar-la per definitiva; les
formes **escrites** no en depenen i es donen per bones (verificades contra
el quadre).

### `generar_tot_2_pronoms.py`

Mateix disseny que `generar_tot_1_pronom.py`: llegeix les columnes del
diccionari base, itera `llicencies.PARELLES_VALIDES`, i escriu un fitxer per
parella a `txt_fets/2_pronoms/verb_pronom_<p1>_<p2>.txt`.

```bash
python3 pronoms/generar_tot_2_pronoms.py              # les 69 parelles
python3 pronoms/generar_tot_2_pronoms.py li:el es:hi   # només aquestes
```

---

## 3. Resultat de la generació

`python3 pronoms/generar_tot_2_pronoms.py` → **69 fitxers, 2.751.676
línies, 220 MB.**

| Comprovació | Resultat |
|---|---|
| 10 camps per línia, codi de 10 caràcters | ✅ 0 excepcions |
| un sol accent primari per forma | ✅ 0 excepcions |
| col·lisions amb el diccionari base (`col_0.txt`) | ✅ 0 |
| files duplicades exactes | ✅ 0 |
| casos de prova coneguts (`porta-l'hi`, `treu-l'en`, `renta-te-la`, `avisa'ns-hi`/`digues-nos-hi`) | ✅ tots coincideixen amb el Quadre 8.9 |

Repartiment per forma verbal: 512.756 infinitius, 508.538 gerundis,
1.730.382 imperatius. **1.517.285 combinacions descartades** per la
heurística d'unió o la concordança de persona.

Per comparació: el diccionari actual (1 pronom inclòs) fa uns 90 MB en
columnes; aquestes 220 MB noves confirmen que segueix fent falta un
**dataset separat, carregat sota demanda** (mateixa decisió de `pla.md`
§4.3).

---

## 4. Pendent

- **Repàs fonètic** amb oïda nativa dels fragments nous (§2, limitació
  coneguda), sobretot els casos `li`+`hi`/`ho`, `la`+`hi`, `les`+`hi` on hi
  ha una vocal final del primer pronom seguida directament d'un segon
  pronom que comença en vocal.
- **Integració al rimador** (Fase 3 de `pla.md`): segueix sense començar,
  tant per a 1 com per a 2 pronoms.
