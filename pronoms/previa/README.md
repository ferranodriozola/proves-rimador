# `pronoms/` — verb + pronom feble

Tot el que genera les combinacions de verb amb pronom feble enclític (`anar-hi`,
`cantar-me`, `digues-ho`, `ves-hi`) en el format del diccionari del Rimador.cat.

És una carpeta **de treball**, no de producció: res d'aquí no el llegeix el web.
El diccionari que serveix `js/script.js` viu a `diccionaris/` i aquesta carpeta
no el toca mai — escriu els seus propis fitxers a part.

## Estat

La generació **amb un pronom** i la **amb dos pronoms** estan totes dues
acabades. 1 pronom: 13 fitxers, 626.837 línies, 47,5 MB, a `txt_fets/1_pronom/`.
2 pronoms: 69 fitxers, 2.779.550 línies, 234 MB, a `txt_fets/2_pronoms/`. La
**integració al web no està començada** (no hi ha cap `W` a `js/script.js`, el
dataset no existeix en format columnes ni surt a `diccionaris/versions.json`,
i no hi ha caselles a la UI) — és la Fase 3 de `pla.md`, encara pendent per a
totes dues generacions.

---

## Mapa de la carpeta

```
pronoms/
├── README.md                    aquest fitxer
│
├── python/                      tot el codi
│   ├── enclisi.py                  ortografia + fonètica + rima de l'enclisi
│   ├── llicencies.py               quins pronoms/parelles admet cada verb i cada persona
│   ├── generar_tot_1_pronom.py     driver d'1 pronom
│   ├── generar_tot_2_pronoms.py    driver de 2 pronoms
│   ├── ajuntar_diccionari_6.py     diccionari + formes amb pronom -> diccionari.6.txt
│   ├── ajuntar_i_comptar_rimes.py  l'estudi: què passaria amb les rimes
│   └── llista_verbs.py             treu la llista de lemes verbals del diccionari
│
├── docs/                        documents i dades d'entrada
│   ├── pla.md                      el pla general del projecte (5 fases)
│   ├── pla_un_pronom.md            el pla concret de la generació amb 1 pronom
│   ├── pla_dos_pronoms.md          el pla concret de la generació amb 2 pronoms
│   ├── pronoms.docx                el quadre normatiu de l'enclisi (material d'origen)
│   ├── verbs.json                  9.016 lemes verbals (entrada del scraper)
│   └── verbs_anotats_num.json      els mateixos 9.016 amb les categories del DIEC
│
├── txt_fets/                    LA SORTIDA generada, per nombre de pronoms
│   ├── 1_pronom/                   els 13 verb_pronom_*.txt (fet)
│   └── 2_pronoms/                  els 69 verb_pronom_<p1>_<p2>.txt (fet)
│
└── antics(done)/                scripts i dades ja consumits, desats per traça
    └── 1a versio/                  la primera generació (hi + en), ja substituïda
```

---

## Els documents

| Fitxer | Què és |
|---|---|
| `pla.md` | El pla general, en 5 fases: què hi ha ara (§1), quines combinacions són vàlides (§2), estratègia de generació (§3), **integració a la UI** (§4), esquema de codis (§5) i càlcul de la rima (§6). És el document a rellegir per continuar, perquè la feina que queda és la Fase 3. |
| `pla_un_pronom.md` | El pla d'execució de la generació amb un sol pronom: les 5 classes de verb, les decisions P1–P6, el format del codi (§4), l'arquitectura de mòduls (§5), el volum previst (§6) i el resultat real amb totes les comprovacions de sanitat (§9). Aquest és el document que manà: on contradiu `pla.md`, guanya. |
| `pla_dos_pronoms.md` | El pla d'execució de la generació amb dos pronoms: el Quadre 8.9 transcrit (la font de totes les 69 parelles vàlides i la seva ortografia exacta), la heurística d'unió per decidir quin verb admet quina parella (i l'excepció dels pronominals inherents), l'arquitectura estesa, i el resultat real amb les comprovacions de sanitat. |
| `pronoms.docx` | El quadre de l'enclisi (forma plena i reduïda de cada pronom, per funció: acusatiu, datiu, reflexiu) i l'ordre de col·locació dels dos pronoms. És el material de partida contra el qual es va verificar la taula `ENCLISI` d'`enclisi.py`. |

> ⚠️ **Referències obsoletes a `pla.md`.** La §5 encara descriu el format de codi
> antic (`WN00_1HI`, amb guió baix, i els codis `EA`/`ED` per a `els`) i cita un
> `pronoms/pronoms.json` que ja no existeix (esborrat). El format viu és el de
> `pla_un_pronom.md` §4: 10 caràcters, sense separador, i els 13 pronoms estan
> definits a `enclisi.py`.

---

## El generador

Tres mòduls i un driver:

```
diccionaris/separat/col_*.txt ──┐
                                ├──> generar_tot_1_pronom.py ──> txt_fets/1_pronom/verb_pronom_<pronom>.txt
verbs_anotats_num.json ─────────┘         │
                                          ├── llicencies.py   quins pronoms pot dur el verb
                                          └── enclisi.py      com s'escriu i com sona
```

```bash
python3 pronoms/python/generar_tot_1_pronom.py
```

Sense arguments genera **els 13 pronoms** (equival a passar `--tots`); també
accepta una llista solta per generar-ne només alguns:
`python3 pronoms/python/generar_tot_1_pronom.py hi ho en`.

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
  (`veure-hi` /bˈɛwɾəj/). Les regles viuen en tres funcions a part
  —**`_sensibilitzar()`** (les que necessiten la grafia), **`_sandhi()`** (les
  que només miren els sons, al límit entre dos trossos d'AFI) i
  **`_semivocal()`**— justament perquè el cas de 2 pronoms les pugui reutilitzar.
- **`_consonant_muda()`** no es fia de la llista de grups: compara sempre la
  grafia amb la transcripció real, perquè `ressurt` fa /rəsˈur/ (muda) i `port`
  fa /pˈɔrt/ (sona), i perquè una consonant **assordida** no és una consonant
  muda (`perd` → /pˈɛrt/ no recupera cap [d]).
- **`calcular_rimes()`** fa servir el mateix càlcul que
  `diccionaris/python/creador_rima + dicc (a partir de col_10).py`, a posta,
  perquè les dues rimes no puguin divergir mai.
- **`silabes()`**: el guionet suma síl·laba, l'apòstrof no, i la semivocal
  tampoc (`veure-hi` = 2, com `veure`).
- **`construir_codi()`** munta el codi de 10 caràcters i comprova l'amplada.
- **`generar_forma()`** és la porta d'entrada que fan servir els dos drivers.
  Amb 1 pronom fa el que s'ha descrit més amunt; amb 2 pronoms deriva cap a
  **`_generar_forma_2()`**, que busca la parella a `llicencies.PARELLES` (el
  Quadre 8.9 transcrit, vegeu més avall) i n'agafa l'ortografia literal, però
  la fonètica la munta amb **les mateixes regles**, aplicades ara als **dos**
  límits que hi ha: verb|pronom1 i pronom1|pronom2. Per això
  `digues-los-ho` fa /dˈiɣəzluzu/ (les dues `-s` sonoritzen, com a
  `digues-lo` /dˈiɣəzlu/) i `cantar-los-els` /kəntˈarluzəls/ (la `-r`
  reapareix, com a `cantar-los`).

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
python3 pronoms/python/llicencies.py
```

**Per a 2 pronoms**, el mateix mòdul hi afegeix:

- **`PARELLES`**: el Quadre 8.9 (`pla_dos_pronoms.md` §1) transcrit
  literalment, `(pronom1, pronom2) -> (escrit, (fonema1, fonema2))` — la
  fonètica va **partida en els dos pronoms** perquè `enclisi` hi pugui
  aplicar el sàndhi al límit que els separa. Les 4 files que varien amb el
  verb (`us`, `ens`, `els` datiu, `els` acusatiu) guarden una parella
  `(consonant, vocal)` en lloc d'un sol valor.
- **`parella_efectiva()`** resol la transformació `li`+CD → CD+`hi`
  (`porta-l'hi`) i la distinció interna `els_dat`/`els_ac` (mateixa paraula,
  comportament diferent: el datiu es comporta com `li`, l'acusatiu només
  admet `hi`/`en`).
- **`PARELLES_VALIDES`**: les 69 parelles reals, en ordre gramatical.
- **`permet_parella()`**: la **heurística d'unió** — una parella es permet
  si el verb admet cada membre per separat, sense necessitat de dades noves
  de ditransitivitat (decisió presa amb l'usuari per no haver de tornar a
  fer scraping del DIEC).
- **`_parella_inherent()`**: l'excepció a la unió. Un pronominal inherent no
  admet cap pronom sol tret del reflexiu, o sigui que la unió, tal qual, el
  deixaria fora de tot el conjunt de 2 pronoms — i és justament el cas que
  `pla_un_pronom.md` §2.2 reservava per a aquesta fase (`penedir-ne` ❌,
  `penedir-se'n` ✅). La regla: el reflexiu sempre va **primer** (a
  l'imperatiu, el que concorda amb el subjecte), i el segon pronom és el que
  admetria un intransitiu — datius, `hi` i `en` —, més els acusatius només
  si el verb té alguna construcció `v. tr. pron.` (`endur-se'l`,
  `empassar-se-la`), cosa que decideix **`admet_cd()`**.

### `generar_tot_1_pronom.py` — el driver

- Llegeix els 10 camps del diccionari base i comprova que
  tinguin el mateix nombre de línies.
- `FORMES` tradueix els 16 codis EAGLES que ens interessen a `(forma verbal,
  persona)`: infinitiu, gerundi i les 14 etiquetes d'imperatiu foses en 5
  persones (el sufix `Y` marca homografia i la `X` la 1a conjugació; cap de les
  dues no canvia la persona).
- `comprovar_base()` és una xarxa de seguretat: si una forma base porta dos
  accents primaris o té camps buits, atura la generació, perquè el càlcul de la
  rima (tot el que va darrere de l'últim accent) sortiria malament **en silenci**.
- Escriu, a `txt_fets/1_pronom/`, un fitxer per pronom i informa del recompte,
  de la mida, del repartiment per forma verbal i de les formes descartades amb
  el motiu.
- Per defecte (`PRONOMS = enclisi.ORDRE_PRONOMS`) genera els 13; es pot cridar
  amb una llista de pronoms concrets per fer-ne només alguns.

### `generar_tot_2_pronoms.py` — el driver de 2 pronoms

Mateix disseny que el d'1 pronom, del qual **importa** `llegir_columnes`,
`comprovar_base` i `FORMES` en lloc de copiar-los (que és tota la gràcia de
partir això en mòduls: si canvia la lectura del diccionari base, canvia per
a les dues sortides alhora). En lloc d'un pronom sol, itera
`llicencies.PARELLES_VALIDES` i crida `llicencies.permet_parella()` +
`enclisi.generar_forma(..., [p1, p2], ...)`. Escriu un fitxer per parella a
`txt_fets/2_pronoms/`.

```bash
python3 pronoms/python/generar_tot_2_pronoms.py             # les 69 parelles
python3 pronoms/python/generar_tot_2_pronoms.py li:el es:hi  # només aquestes
```

### `ajuntar_diccionari_6.py` — el diccionari sencer

L'última passa: ajunta `diccionaris/diccionari.5.2.3.txt` amb els 82 fitxers
de les subcarpetes de `txt_fets/` i escriu `diccionaris/diccionari.6.txt`,
**ordenat alfabèticament** (4.026.170 línies, ~324 MB, uns 50 segons).

Dues coses hi són a posta:

* **Cap fitxer intermedi.** Les línies de `txt_fets/` no passen mai per un
  fitxer amb només les rimes de pronom: es llegeixen, es barregen amb les del
  diccionari i surten directament al fitxer final.
* **Només mira dins de les subcarpetes** de `txt_fets/`. A `txt_fets/` mateix
  hi ha el `tot.txt` de l'`ajuntar_i_comptar_rimes.py`, que ja és la suma
  d'aquests 82 fitxers: si s'hi colés, cada forma amb pronom sortiria dues
  vegades.

L'ordre és el del diccionari: à=a=À=A, è=é=e=È=É=E, ç=c, ï=i... S'ordena per
la paraula (camp 0) sense accents ni majúscules, i les que empaten es desfan
amb la paraula tal com s'escriu (`Índia` abans que `índia`).

```bash
python3 pronoms/python/ajuntar_diccionari_6.py
```

> `diccionari.6.txt` és a `.gitignore`: fa 324 MB i GitHub rebutja els fitxers
> de més de 100 MiB. El que va al repositori és el seu contingut **partit en
> columnes**, que és el que es baixa el navegador (vegeu
> `diccionaris/README.md`). El fitxer sencer és un pas intermedi i no se'n
> guarda cap còpia: si el vols mirar, refes-lo en local.

> **D'on llegeixen els generadors.** Del diccionari base
> (`diccionaris/diccionari.5.2.3.txt`), no pas de `diccionaris/separat/`. Les
> columnes de `separat/` són les del diccionari **publicat**, que ja porta les
> formes amb pronom: partir-ne seria fer pronoms de formes que ja en duen. El
> nom del diccionari base surt de `diccionaris/python/config.py`.

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

## La sortida: `txt_fets/1_pronom/verb_pronom_*.txt`

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
| `verb_pronom_ens.txt` | 58.836 | 4,5 MB |
| `verb_pronom_els.txt` | 57.654 | 4,4 MB |
| `verb_pronom_en.txt` | 57.654 | 4,4 MB |
| `verb_pronom_li.txt` | 57.654 | 4,3 MB |
| `verb_pronom_hi.txt` | 57.654 | 4,2 MB |
| `verb_pronom_em.txt` | 50.219 | 3,8 MB |
| `verb_pronom_el.txt` | 47.516 | 3,5 MB |
| `verb_pronom_ho.txt` | 47.516 | 3,5 MB |
| `verb_pronom_la.txt` | 47.516 | 3,7 MB |
| `verb_pronom_les.txt` | 47.516 | 3,8 MB |
| `verb_pronom_et.txt` | 34.169 | 2,6 MB |
| `verb_pronom_us.txt` | 34.096 | 2,6 MB |
| `verb_pronom_es.txt` | 28.837 | 2,2 MB |
| **TOTAL** | **626.837** | **47,5 MB** |

Són 81 codis diferents dels 91 possibles: els 10 que falten són exactament els
que bloqueja la matriu de concordança. La generació original va donar 626.786
línies: n'hi ha 7 menys perquè eren les files duplicades de `ves` que
arrossegava el diccionari base (`pla_un_pronom.md` §9), ja corregides a
l'origen, i 58 més que són les formes de `ser`, `ésser`, `sent`, `essent`,
`haver` i `havent` (vegeu «Correccions», al final).

---

## La sortida: `txt_fets/2_pronoms/verb_pronom_<p1>_<p2>.txt`

Mateix format de 10 camps que la sortida d'1 pronom. **69 fitxers, un per
parella del Quadre 8.9** (`pla_dos_pronoms.md` §1) — per exemple
`verb_pronom_li_el.txt` (`porta-l'hi`) o `verb_pronom_es_hi.txt`
(`avisar-s'hi`).

```
porta-l'hi$portar$WM02S2LIEL$ɔrtəli$ɔəi$3$Vicc$Viq$Diec$pˈɔrtəli
```

El codi conserva sempre la **identitat gramatical original** dels dos
pronoms (`LI`+`EL`), encara que l'ortografia surti transformada (`li`+`el`
s'escriu "l'hi", mai "hi"+"el") — el mateix criteri que ja apuntava
`pla_un_pronom.md` §4 per a aquest exemple concret.

| | Total |
|---|---:|
| Fitxers | 69 |
| Línies | 2.779.550 |
| Mida | 234 MB |

Comprovacions de sanitat (`pla_dos_pronoms.md` §3): 10 camps i codi de 10
caràcters a totes les línies, un sol accent primari per forma, 0
col·lisions amb el diccionari base, 0 duplicats exactes, i el límit
verb|pronom idèntic al que dona el camí d'1 pronom a **totes** les
2.779.550 combinacions.

L'**ortografia** surt del Quadre 8.9, cel·la per cel·la. La **fonètica**
és pròpia (el quadre no en dona), però no s'inventa res de nou: són els
fragments d'AFI de `FONEMA` més les mateixes 6 regles de sàndhi d'1
pronom, aplicades als dos límits del grup. Els casos que abans quedaven
pendents ja hi entren: `porta-li-ho` → /pˈɔrtəliw/ i `porta-la-hi` →
/pˈɔrtələj/ (semivocal, decisió P5), `porta-les-hi` → /pˈɔrtələzi/
(sonorització). L'única cosa que continua sent una reconstrucció nostra
són les formes "nues" del 2n pronom rere consonant (`-los-en` → /luzən/),
que el quadre només dona escrites.

---

## `antics(done)/` — ja consumit

Scripts que van fer la seva feina i dades que en van sortir. Es desen per poder
reconstruir d'on venen les categories dels verbs, no per tornar-los a executar.

| Fitxer | Què va fer |
|---|---|
| `scrap_diec+num.py` | El scraper que va produir `verbs_anotats_num.json`: per a cada lema consulta `dlc.iec.cat`, i es queda amb **tots** els resultats de la cerca (`haver1`, `haver2`…), no només el primer. És l'únic scraper que queda; la versió que només llegia el primer resultat s'ha esborrat. |
| `filtrar_resultats.py` | Informe sobre l'anotació d'un scraper: quins verbs no van quedar `OK` i quines categories úniques va tornar el DIEC (és el que va donar la llista de categories a classificar). |
| `revisar_r_infinitius.py` | Auditoria del diccionari base: quins infinitius tenen la transcripció acabada en `r` quan no hauria de sonar. Sol ser contaminació d'un homògraf no verbal (`militar` nom). Es pot passar per les columnes o per un `.txt` de 10 camps. |

### `antics(done)/1a versio/` — la primera generació

La tongada inicial, feta amb tres scripts separats (un per forma verbal) i només
amb `hi` i `en`. **Substituïda** per `enclisi.py` + `llicencies.py` +
`generar_tot_1_pronom.py`, que reprodueixen els infinitius i els gerundis al
100 % i canvien 15 imperatius en generalitzar la sensibilització de la
consonant muda.

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
python3 pronoms/python/llista_verbs.py

# 2. les categories del DIEC  ->  verbs_anotats_num.json   (lent: 9.016 consultes)
python3 "pronoms/antics(done)/scrap_diec+num.py"

# 3. comprovar la classificació abans de generar res
python3 pronoms/python/llicencies.py

# 4. generar 1 pronom  ->  txt_fets/1_pronom/verb_pronom_*.txt
python3 pronoms/python/generar_tot_1_pronom.py

# 5. generar 2 pronoms  ->  txt_fets/2_pronoms/verb_pronom_*_*.txt
python3 pronoms/python/generar_tot_2_pronoms.py
```

El pas 2 depèn de `requests`, `beautifulsoup4` i `tqdm`; la resta no necessita
res que no sigui la biblioteca estàndard. En condicions normals només calen
els passos 4 i 5: les categories del DIEC no canvien, i el Quadre 8.9 ja és
al codi (`llicencies.PARELLES`), no cal tornar-lo a llegir de cap font.

---

## Correccions (agost del 2026)

Una revisió de tota la generació va trobar cinc errors. Els quatre primers
estan **arreglats** i la sortida s'ha refet; el cinquè queda pendent.

| | Què passava | On | Formes |
|---|---|---|---:|
| 1 | `li`+`la` no aplicava la semivocal: `porta-la-hi` sortia /pˈɔrtələi/ per aquesta via i /pˈɔrtələj/ per la via `la`+`hi` — la mateixa paraula amb dues rimes i dos recomptes de síl·labes | `enclisi._generar_forma_2` passava el **p2 original** al `_semivocal()` en lloc del de `parella_efectiva()` | 47.514 |
| 2 | Els 396 imperatius de vostè acabats en `-ï` prenien la forma plena: `actuï-lo` en lloc de `actuï'l` | `enclisi.VOCALS_GRAFIQUES` no duia la `ï` | 7.809 |
| 3 | `ser`, `ésser`, `sent`, `essent`, `haver` i `havent` no generaven res — hi faltaven `haver-hi`, `haver-n'hi`, `ser-hi`, `ser-ne` | `FORMES` només tenia l'infinitiu i el gerundi del verb **principal** (`VMN`/`VMG`), no els de `ser` (`VSN`/`VSG`) ni els de `haver` (`VAN`/`VAG`) | +304 |
| 4 | `cantar-vos` feia /kəntˈarbus/; el diccionari escriu `corba` /kˈorβə/ i `pèl-blanc` /pˈɛlβlˈaŋ/ | la regla (4) de `_sandhi()` només espirantitzava darrere vocal, quan l'únic context que manté la [b] oclusiva és una **nasal** (`bum-bum` /bˈumbˈum/) | 85.465 |

**Pendent (error 5): l'assimilació de sonoritat del so final del verb.** El
diccionari la fa sistemàticament al límit de morfema (`baix-alemany`
/bˈaʒələmˈaɲ/, `zig-zag` /zˈidʒzˈak/, `migdia` /mˌidʒdˈiə/, `cap-rodo`
/kˈabrˈɔðu/, `but-but` /bˈudbˈut/) i `_sandhi()` només la té per a la `-s`.
Hi falten `abasteix-hi` → /əʒi/, `fuig-me` → /dʒm/, `abat-me` → /dm/ i
`ajup-li` → /bl/: unes 34.600 formes, 32.500 de les quals són imperatius
en `-eix`. Les sibilants sonoritzen també davant vocal; les oclusives,
només davant consonant sonora (`abat-hi` /əβˈati/ ja és correcte).

**Pendent: 200.202 entrades bessones.** `li`+CD i CD+`hi` donen línies
idèntiques camp per camp tret del codi (`porta-l'hi` és alhora `WM02S2LIEL`
i `WM02S2ELHI`, i igual amb `la`, `les` i `els`). És homografia real de la
llengua, però al diccionari hi surt dues vegades. Cal decidir, abans de la
Fase 3, si es col·lapsen en un sol codi o si la UI les distingeix.
