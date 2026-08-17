# `pronoms/` — verb + pronom feble

Tot el que genera les combinacions de verb amb pronom feble enclític (`anar-hi`,
`cantar-me`, `digues-ho`, `ves-hi`) en el format del diccionari del Rimador.

És una carpeta **de treball**, no de producció: res d'aquí no el llegeix el web.
El diccionari que serveix `js/script.js` viu a `diccionaris/` i aquesta carpeta
no el toca mai — escriu els seus propis fitxers a part.

## Estat

La generació **amb un pronom està acabada**: 13 fitxers `verb_pronom_*.txt`,
626.779 línies, 45 MB. La **integració al web no està començada** (no hi ha cap
`W` a `js/script.js`, el dataset no existeix en format columnes ni surt a
`diccionaris/versions.json`, i no hi ha caselles a la UI). Les combinacions de
**dos** pronoms (`porta-l'hi`, `anar-se'n`) són la fase 2 i no s'han tocat.

Detall que convé recordar: els `.txt` es van generar l'11 d'agost del 2026 i el
diccionari base es va regenerar el 13 d'agost, o sigui que van una mica
endarrerits respecte de `diccionaris/separat/`.

---

## Mapa de la carpeta

```
pronoms/
├── README.md                    aquest fitxer
├── pla.md                       el pla general del projecte (5 fases)
├── pla_un_pronom.md             el pla concret de la generació amb 1 pronom
├── pronoms.docx                 el quadre normatiu de l'enclisi (material d'origen)
│
├── enclisi.py                   ortografia + fonètica + rima de l'enclisi
├── llicencies.py                quins pronoms admet cada verb i cada persona
├── generar_tot.py               el driver: llegeix el diccionari i escriu la sortida
├── llista_verbs.py              treu la llista de lemes verbals del diccionari
│
├── verbs.json                   9.016 lemes verbals (entrada del scraper)
├── verbs_anotats_num.json       els mateixos 9.016 amb les categories del DIEC
│
├── verb_pronom_*.txt            LA SORTIDA: 13 fitxers, un per pronom
│
├── done/                        scripts i dades ja consumits, desats per traça
└── txt_fets/                    la primera generació (hi + en), ja substituïda
```

---

## Els documents

| Fitxer | Què és |
|---|---|
| `pla.md` | El pla general, en 5 fases: què hi ha ara (§1), quines combinacions són vàlides (§2), estratègia de generació (§3), **integració a la UI** (§4), esquema de codis (§5) i càlcul de la rima (§6). És el document a rellegir per continuar, perquè la feina que queda és la Fase 3. |
| `pla_un_pronom.md` | El pla d'execució de la generació amb un sol pronom: les 5 classes de verb, les decisions P1–P6, el format del codi (§4), l'arquitectura de mòduls (§5), el volum previst (§6) i el resultat real amb totes les comprovacions de sanitat (§9). Aquest és el document que manà: on contradiu `pla.md`, guanya. |
| `pronoms.docx` | El quadre de l'enclisi (forma plena i reduïda de cada pronom, per funció: acusatiu, datiu, reflexiu) i l'ordre de col·locació dels dos pronoms. És el material de partida contra el qual es va verificar la taula `ENCLISI` d'`enclisi.py`. |

> ⚠️ **Referències obsoletes a `pla.md`.** La §5 encara descriu el format de codi
> antic (`WN00_1HI`, amb guió baix, i els codis `EA`/`ED` per a `els`) i cita un
> `pronoms/pronoms.json` que ja no existeix. El format viu és el de
> `pla_un_pronom.md` §4: 10 caràcters, sense separador, i els 13 pronoms estan
> definits a `enclisi.py`.

---

## El generador

Tres mòduls i un driver, en comptes dels tres scripts duplicats de `txt_fets/`:

```
diccionaris/separat/col_*.txt ──┐
                                ├──> generar_tot.py ──> verb_pronom_<pronom>.txt
verbs_anotats_num.json ─────────┘         │
                                          ├── llicencies.py   quins pronoms pot dur el verb
                                          └── enclisi.py      com s'escriu i com sona
```

```bash
python3 pronoms/generar_tot.py --tots
```

Sense arguments només fa `hi` i `en` (era el pas de validació contra els fitxers
vells); també accepta una llista solta: `python3 pronoms/generar_tot.py hi ho en`.

### `enclisi.py` — com s'escriu i com sona

L'única definició de l'enclisi. No llegeix ni escriu fitxers i no sap res de
verbs: transforma `(forma, transcripció, síl·labes, pronom)` en tot el que
necessita una línia del diccionari.

- **Taules**: `ENCLISI` (forma plena darrere consonant o diftong / reduïda
  darrere vocal), `FONEMA` (l'AFI de cada enclític, amb la reducció vocàlica del
  central ja aplicada), `PRONOM_CODI` (les 2 lletres de cada pronom, tretes de la
  forma enclítica: `-ne` → `NE`, `-nos` → `NS`, `-los` → `LS`) i `ORDRE_PRONOMS`
  (l'ordre gramatical de col·locació).
- **`transcriure()`** aplica les 6 regles de sàndhi, totes amb precedent al
  diccionari: la `-r` muda de l'infinitiu que reapareix (`anar-hi` /ənˈaɾi/), la
  consonant muda d'un grup final que només torna davant de vocal (`cantant-hi`
  /kəntˈanti/ però `cantant-ne` /kəntˈannə/), la sonorització de la `-s`
  (`digues-hi` /dˈiɣəzi/), l'espirantització de `-vos`, l'assimilació de la `-n`
  (`cantant-me` /kəntˈammə/) i la semivocalització de `-hi`/`-ho` darrere vocal
  (`veure-hi` /bˈɛwɾəj/).
- **`_consonant_muda()`** no es fia de la llista de grups: compara sempre la
  grafia amb la transcripció real, perquè `ressurt` fa /rəsˈur/ (muda) i `port`
  fa /pˈɔrt/ (sona), i perquè una consonant **assordida** no és una consonant
  muda (`perd` → /pˈɛrt/ no recupera cap [d]).
- **`calcular_rimes()`** fa servir el mateix càlcul que
  `diccionaris/pythons/creador_rima + dicc (a partir de col_10).py`, a posta,
  perquè les dues rimes no puguin divergir mai.
- **`silabes()`**: el guionet suma síl·laba, l'apòstrof no, i la semivocal
  tampoc (`veure-hi` = 2, com `veure`).
- **`construir_codi()`** munta el codi de 10 caràcters i comprova l'amplada.
- **`generar_forma()`** és la porta d'entrada que fa servir el driver. Amb dos
  pronoms llança `NotImplementedError`: la fase 2 necessita les seves regles
  d'apòstrof.

### `llicencies.py` — qui pot dur què

Respon una sola pregunta, `permet(lema, pronom, persona)`, i és la que decideix
tot el volum. Llegeix `verbs_anotats_num.json` i classifica cada lema en **5
classes** segons les categories del DIEC:

| Classe | Verbs | Pronoms |
|---|---|---|
| `sense_info` — el DIEC no en diu res | 422 | **0** (decisió P1, en un `if` aïllat per poder-ho canviar) |
| `inherent` — totes les construccions són pronominals | 392 | 5 (només la casella del reflexiu) |
| `transitiu` (± pronominal) | 6.762 | 13 (tots) |
| `intr_pron` — intransitiu amb construcció pronominal | 29 | 9 (universals + `es`) |
| `intr_pur` | 1.411 | 8 (només universals) |

També hi viuen les **dues matrius de concordança** de l'imperatiu:
`MATRIU_PERSONA` descarta el solapament parcial de referents (`*cantem-me`), i
`REFLEXIU_EXACTE` limita els pronominals inherents al reflexiu que concorda amb
el subjecte (`penedeix-te` sí, `*penedeix-me` no).

Executable pel seu compte, treu l'informe de verbs per classe i per pronom:

```bash
python3 pronoms/llicencies.py
```

### `generar_tot.py` — el driver

- Llegeix les 10 columnes de `diccionaris/separat/col_*.txt` i comprova que
  tinguin el mateix nombre de línies.
- `FORMES` tradueix els 16 codis EAGLES que ens interessen a `(forma verbal,
  persona)`: infinitiu, gerundi i les 14 etiquetes d'imperatiu foses en 5
  persones (el sufix `Y` marca homografia i la `X` la 1a conjugació; cap de les
  dues no canvia la persona).
- `comprovar_base()` és una xarxa de seguretat: si una forma base porta dos
  accents primaris o té camps buits, atura la generació, perquè el càlcul de la
  rima (tot el que va darrere de l'últim accent) sortiria malament **en silenci**.
- Escriu un fitxer per pronom i informa del recompte, de la mida, del repartiment
  per forma verbal i de les formes descartades amb el motiu.

### `llista_verbs.py`

Un pas previ, d'una sola passada: llegeix `diccionaris/diccionari.5.2.3.txt`,
agafa el lema (camp 1) de tota entrada amb codi `V…` i el desa sense repeticions
a `verbs.json`. És el que va produir la llista de 9.016 lemes.

---

## Les dades d'entrada

| Fitxer | Què conté |
|---|---|
| `verbs.json` | Llista plana de **9.016 lemes verbals**, tal com surten del diccionari. Entrada del scraper. |
| `verbs_anotats_num.json` | Els mateixos 9.016 lemes amb `{categories, estat}` tret del DIEC: `{"abadanar": {"categories": ["v. tr."], "estat": "OK"}}`. **8.594 OK**, 413 no trobats i 9 sense categories — els 422 de la classe `sense_info`. És l'únic fitxer de dades que llegeix `llicencies.py`. |

---

## La sortida: `verb_pronom_*.txt`

Un fitxer per pronom, en el mateix format que `diccionaris/diccionari.5.2.3.txt`:
10 camps separats per `$`, una línia per forma.

```
ves-hi$anar$WM02S1HI00$ezi$ei$2$Vicc$Viq$Diec$bˈezi
 │      │    │          │   │  │  └──┬───┘      └── 9 transcripció AFI
 │      │    │          │   │  │     └──────────── 6-8 Vicc / Viq / Diec (heretats del verb)
 │      │    │          │   │  └────────────────── 5 síl·labes
 │      │    │          │   └───────────────────── 4 rima assonant
 │      │    │          └───────────────────────── 3 rima consonant
 │      │    └──────────────────────────────────── 2 codi
 │      └───────────────────────────────────────── 1 lema del verb base
 └──────────────────────────────────────────────── 0 la forma
```

Els camps 6–8 (els enllaços a Viccionari, Viquipèdia i DIEC) s'hereten del verb
base a posta: la UI ha d'apuntar al lema, no a la forma amb pronom.

### El codi

10 caràcters, posicional, sense separador — com els codis EAGLES d'aquest
diccionari, que `js/script.js` ja indexa per posició:

```
W  N  000  1  HI  00
0  1  2-4  5  6-7 8-9

0    W = verb amb pronom (la lletra estava lliure: només hi havia A D N P V Z)
1    forma: N infinitiu · G gerundi · M imperatiu
2-4  persona: 000 (infinitiu i gerundi) · 02S 01P 02P 03S 03P (imperatiu)
5    nombre de pronoms: 1 o 2
6-7  pronom 1     EM ET ES NS US EL LA LS LE LI NE HO HI
8-9  pronom 2     00 si no n'hi ha
```

Amb això els filtres surten sols: `startsWith('W')` per a tota la secció,
`'WN'`/`'WG'`/`'WM'` per forma, `'WM02S'` per als imperatius de «tu», `codi[5]`
per al nombre de pronoms.

### Els 13 fitxers

| Fitxer | Línies | Mida |
|---|---:|---:|
| `verb_pronom_ens.txt` | 58.830 | 4,5 MB |
| `verb_pronom_els.txt` | 57.648 | 4,4 MB |
| `verb_pronom_en.txt` | 57.648 | 4,4 MB |
| `verb_pronom_li.txt` | 57.648 | 4,3 MB |
| `verb_pronom_hi.txt` | 57.648 | 4,2 MB |
| `verb_pronom_em.txt` | 50.213 | 3,8 MB |
| `verb_pronom_el.txt` | 47.514 | 3,5 MB |
| `verb_pronom_ho.txt` | 47.514 | 3,5 MB |
| `verb_pronom_la.txt` | 47.514 | 3,7 MB |
| `verb_pronom_les.txt` | 47.514 | 3,8 MB |
| `verb_pronom_et.txt` | 34.163 | 2,6 MB |
| `verb_pronom_us.txt` | 34.090 | 2,6 MB |
| `verb_pronom_es.txt` | 28.835 | 2,2 MB |
| **TOTAL** | **626.779** | **45 MB** |

Són 81 codis diferents dels 91 possibles: els 10 que falten són exactament els
que bloqueja la matriu de concordança. La generació va donar 626.786 línies i
ara n'hi ha 7 menys: són les files duplicades de `ves` que arrossegava el
diccionari base i que s'han esborrat a mà (`pla_un_pronom.md` §9).

---

## `done/` — ja consumit

Scripts que van fer la seva feina i dades que en van sortir. Es desen per poder
reconstruir d'on venen les categories dels verbs, no per tornar-los a executar.

| Fitxer | Què va fer |
|---|---|
| `scrap_diec+num.py` | El scraper que va produir `verbs_anotats_num.json`: per a cada lema consulta `dlc.iec.cat`, i es queda amb **tots** els resultats de la cerca (`haver1`, `haver2`…), no només el primer. |
| `scrap_diec.py` | La versió anterior, que només llegia el primer resultat i va produir `verbs_anotats.json`. Substituïda per l'anterior. |
| `verbs_anotats.json` | La sortida d'aquell primer scraper. **No la fa servir ningú**; hi és per poder comparar. |
| `verbs_prova.json` | 7 verbs triats per provar els scrapers: `voler`, `haver`, `esdevenir`, `ploure`, `queixar`, `dinyar`, `morir`. |
| `verbs_anotats_prova.json` / `..._prova_num.json` | El resultat dels dos scrapers sobre aquells 7 verbs. La diferència entre els dos fitxers és justament el motiu de la reescriptura: `haver` surt com a `v. aux.` al primer i com a `v. aux.` **+ `v. tr.`** al segon. |
| `filtrar_resultats.py` | Informe sobre `verbs_anotats.json`: quins verbs no van quedar `OK` i quines categories úniques va tornar el DIEC (és el que va donar la llista de categories a classificar). |
| `revisar_r_infinitius.py` | Auditoria del diccionari base: quins infinitius tenen la transcripció acabada en `r` quan no hauria de sonar. Sol ser contaminació d'un homògraf no verbal (`militar` nom). Es pot passar per les columnes o per un `.txt` de 10 camps. |

---

## `txt_fets/` — la primera generació

La tongada inicial, feta amb tres scripts separats (un per forma verbal) i només
amb `hi` i `en`. **Substituïda** per `enclisi.py` + `llicencies.py` +
`generar_tot.py`, que reprodueixen els infinitius i els gerundis al 100 % i
canvien 15 imperatius en generalitzar la sensibilització de la consonant muda.

| Fitxer | Línies |
|---|---:|
| `imperatius_hi_en.txt` | 88.334 |
| `infinitius_hi_en.txt` | 17.828 |
| `gerundis_hi_en.txt` | 17.578 |

Els tres `*generar_*.py` duen un asterisc al davant del nom. Fan servir el
**format de codi antic** (`WG00_1HI`, amb guió baix i el nombre de pronoms en
posició variable, que és el que la §4 de `pla_un_pronom.md` va corregir) i els
codis `EA`/`ED` per a `els`, tots dos abandonats. Si es comparen sortides, cal
tenir-ho present: les absències respecte dels fitxers nous no són errors, són el
filtre de llicències que abans no existia (5.528 pronominals inherents + 2.914
verbs sense informació).

---

## Reconstruir-ho tot de zero

```bash
# 1. la llista de lemes verbals, del diccionari  ->  verbs.json
python3 pronoms/llista_verbs.py

# 2. les categories del DIEC  ->  verbs_anotats_num.json   (lent: 9.016 consultes)
python3 "pronoms/done/scrap_diec+num.py"

# 3. comprovar la classificació abans de generar res
python3 pronoms/llicencies.py

# 4. generar  ->  verb_pronom_*.txt
python3 pronoms/generar_tot.py --tots
```

El pas 2 depèn de `requests`, `beautifulsoup4` i `tqdm`; els passos 1, 3 i 4 no
necessiten res que no sigui la biblioteca estàndard. En condicions normals
només cal el pas 4: les categories del DIEC no canvien.
