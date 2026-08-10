# Pla d'acció: llista completa de verb + 1 pronom feble

> Document de treball per a la generació **completa** amb **un sol pronom**.
> El pla general (fases, integració a la UI, càlcul de la rima) és a [pla.md](pla.md);
> aquí només es concreta el *què generem* i *amb quina arquitectura*.
>
> Xifres mesurades sobre `diccionaris/separat/col_*.txt` (619.785 entrades) i
> `pronoms/verbs_anotats_num.json` (9.016 verbs), agost del 2026.

---

## 0. Resum de decisions

| Qüestió | Decisió |
|---|---|
| Acusatiu `el`/`la`/`les`/`ho` | només verbs transitius (**6.762**) |
| Datiu `em`/`et`/`ens`/`us`/`li`/`els` | tots els verbs (datiu ètic) — **P2 ✅** |
| `hi` / `en` | tots els verbs — **P3 ✅** |
| Reflexiu `es` | transitius ∪ pronominals (**7.183**); mai intransitius purs |
| Verbs pronominals **inherents** (392) | **només** admeten el reflexiu; la resta de pronoms van a la fase de 2 pronoms |
| Verbs sense informació (422) | **es salten, no generen cap pronom** — **P1 ✅**, amb un `if` aïllat per poder-ho canviar |
| Pronominals no inherents (1.070) | es generen igualment amb 1 pronom, acceptant que la qualitat baixa — **P4 ✅** |
| `-hi`/`-ho` darrere vocal | semivocal `[j]`/`[w]`, amb fusió sil·làbica — **P5 ✅** |
| Concordança de persona a l'imperatiu | **s'aplica** — descarta 86.011 formes agramaticals — **P6 ✅** |
| Codi | amplada fixa de 10 caràcters, posicional (§4) |
| Arquitectura | 3 mòduls compartits + 1 driver, no 3 scripts duplicats (§5) |

**Volum previst: 626.786 formes** — una mica més que tot el diccionari actual (619.785).

---

## 1. La correcció important: les teves dues regles es contradiuen

Has dit:

- *acusatiu (`em`/`et`/`ens`/`us`/`el`/`la`/`les`/`els`) només per a verbs transitius*
- *datiu (`em`/`et`/`ens`/`us`/`els`/`li`) per a tots els verbs*

`em`, `et`, `ens`, `us` i `els` **surten a totes dues llistes**, i és que són **la mateixa paraula** per a l'acusatiu, el datiu i el reflexiu: `cantar-me` és un sol *string*, amb una sola pronúncia i una sola rima. No podem generar-lo "només per a transitius" i alhora "per a tots els verbs".

Com que es tracta d'**una sola entrada al diccionari**, el que s'ha d'aplicar és la **unió** de condicions: si n'hi ha prou amb una lectura vàlida perquè la paraula existeixi, la paraula existeix. I com que el datiu és obert a tots els verbs, **la restricció de transitivitat queda inoperant** per a aquests cinc pronoms.

Conseqüència pràctica: **la restricció d'acusatiu només afecta `el`, `la`, `les` i `ho`**, que són els únics pronoms sense ús datiu.

| Pronom | Codi | Funcions que cobreix el mateix *string* | Verbs |
|---|---|---|---|
| `em` | `EM` | ac. + datiu + reflexiu 1a sing. | tots |
| `et` | `ET` | ac. + datiu + reflexiu 2a sing. | tots |
| `ens` | `NS` | ac. + datiu + reflexiu 1a pl. | tots |
| `us` | `US` | ac. + datiu + reflexiu 2a pl. | tots |
| `li` | `LI` | datiu 3a sing. | tots |
| `els` | `LS` | ac. 3a pl. masc. **+ datiu 3a pl.** | tots |
| `el` | `EL` | acusatiu 3a sing. masc. | **transitius** |
| `la` | `LA` | acusatiu 3a sing. fem. | **transitius** |
| `les` | `LE` | acusatiu 3a pl. fem. | **transitius** |
| `ho` | `HO` | acusatiu neutre | **transitius** |
| `hi` | `HI` | CC de lloc, règim `a`/`en`/`amb`, predicatiu | tots |
| `en` | `NE` | partitiu, CC d'origen `de`, règim `de` | tots |
| `es` | `ES` | reflexiu 3a, recíproc, impersonal | **transitius ∪ pronominals** |

Els codis de 2 lletres surten de la forma enclítica (`-ne` → `NE`, `-nos` → `NS`, `-los` → `LS`), que és el que evita que `en` i `ens` xoquin.

---

## 2. El reflexiu: resolt

Tenies dos dubtes. Els separo perquè tenen respostes diferents.

### 2.1 «Podria ser un CD»

Sí, i tant fa. A `rentar-se` el `se` **és** el CD (rentar-se un mateix); a `penedir-se` no és analitzable com a CD, és un marcador lèxic del verb. Però en tots dos casos és **un sol pronom vàlid** i genera una forma real. Per a la generació, la distinció no canvia res: `rentar-se` i `penedir-se` s'escriuen igual, es pronuncien igual i rimen igual.

Sí que importa per decidir **quins verbs** l'admeten. `es` és el pronom que exigeix més coses:

- **verbs pronominals** (1.462) → obligatori: `penedir-se`, `queixar-se`
- **verbs transitius** (6.762) → qualsevol transitiu es pot reflexivitzar (`rentar-se`), fer recíproc (`abraçar-se`) o portar el `se` impersonal/passiu (`vendre's`, `dir-se`) — i això val fins i tot per a transitius que el DIEC no marca com a pronominals (`rentar` només surt com a `v. tr.`)
- **intransitius purs** (1.411) → no: `ploure's`, `abastar-se`, `accedir-se` no existeixen

Per tant `es` → **transitius ∪ pronominals = 7.183 verbs**.

### 2.2 «Els verbs pronominals poden portar altres pronoms i no el pronominal?»

**No, i la teva intuïció és correcta.** Per als verbs **inherentment** pronominals el reflexiu és part del verb i no es pot ometre:

| | |
|---|---|
| `penedir-se` | ✅ 1 pronom |
| `penedir-se'n` | ✅ 2 pronoms → **fase 2** |
| `penedir-ne` | ❌ no existeix |

Igual amb `queixar-se'n`, `abstenir-se'n`, `adonar-se'n`. O sigui que:

> **Per als 392 verbs inherentment pronominals, l'únic pronom simple vàlid és el reflexiu.** Tots els altres pronoms d'aquests verbs es reserven per a la combinació de 2 pronoms.

Això és **derivable de les dades**: són els verbs on *totes* les construccions del DIEC porten `pron.` (`v. intr. pron.`, `v. tr. pron.`, `v. aux. pron.`). Comprovat: 392 verbs, i la intersecció amb els transitius és 0, com toca.

### 2.3 Els verbs que són transitius **i** pronominals: no cal diferenciar-los

La pregunta era com distingim un verb com `ajupir`, que el DIEC dona alhora com a `v. intr. pron.` i `v. tr.` La resposta és que **no el diferenciem, i no fa falta**.

El motiu és que generem **paraules, no oracions**. `ajup-lo` és un sol *string*, amb una pronúncia i una rima; que vingui de la lectura transitiva no en fa una entrada diferent. Per tant, per a cada pronom la pregunta és només: **hi ha ALGUNA construcció del verb que el llicenciï?** Si sí, la paraula existeix i es genera una vegada.

I hi ha una simplificació que no s'havia vist: **per a un verb transitiu, l'etiqueta `pron.` no aporta res**, perquè la transitivitat ja llicencia el reflexiu tota sola (qualsevol transitiu es pot reflexivitzar). `ajupir` (tr + pron) i `rentar` (només tr) reben **exactament els mateixos 13 pronoms**:

```
ajupir  →  ajupir-se ajupir-te ajupir-vos ajupir-me ajupir-nos ajupir-li ajupir-los
           ajupir-lo ajupir-la ajupir-les ajupir-ne ajupir-hi ajupir-ho          (13)
rentar  →  rentar-se rentar-te rentar-vos rentar-me rentar-nos rentar-li rentar-los
           rentar-lo rentar-la rentar-les rentar-ne rentar-hi rentar-ho          (13)
```

O sigui que tot es redueix a **5 classes**, i l'etiqueta `pron.` només canvia alguna cosa en dues d'elles (les 392 inherents i les 29 d'intransitiu+pronominal):

| Classe | Verbs | Pronoms | Mostra |
|---|---|---|---|
| **0** sense informació al DIEC | 422 | **0** (es salta, P1) | `abadocar`, `abcegar` |
| **1** pronominal inherent | 392 | **5** (només el reflexiu) | `abalançar`, `penedir` |
| **2** transitiu (± pronominal) | 6.762 | **13** (tots) | `ajupir`, `rentar`, `abaixar` |
| **3** intransitiu + pronominal | 29 | **9** (universals + `es`) | `anar`, `agradar`, `acudir` |
| **4** intransitiu pur | 1.411 | **8** (només universals) | `abellir`, `abastar` |

Exemple de la classe 4, on es veu què queda fora: `abellir` genera `abellir-te`, `abellir-vos`, `abellir-me`, `abellir-nos`, `abellir-li`, `abellir-los`, `abellir-ne`, `abellir-hi` — i **no** `abellir-lo`/`-la`/`-les`/`-ho` (no és transitiu) ni `abellir-se` (no és pronominal).

### 2.4 Correcció trobada en previsualitzar: els inherents a l'imperatiu

En generar la mostra va sortir **`penedeix-me`**, que és incorrecte, i la regla del §2.2 no ho evitava.

El motiu: un verb inherentment pronominal **no té lectura de datiu ni d'acusatiu** — el pronom només pot ser el reflexiu. A l'infinitiu i al gerundi això no és problema, perquè el subjecte no està fixat i les cinc persones del reflexiu són vàlides (`penedir-me`, `penedir-te`, `penedir-se`, `penedir-nos`, `penedir-vos`). Però **a l'imperatiu el subjecte ja està fixat**, i per tant només sobreviu el reflexiu que hi concorda:

| Persona | Inherent: única forma vàlida | Què cal descartar |
|---|---|---|
| 02S | `penedeix-te` | ~~`penedeix-me`~~ ~~`penedeix-nos`~~ |
| 01P | `penedim-nos` | ~~`penedim-me`~~ ~~`penedim-te`~~ |
| 02P | `penediu-vos` | ~~`penediu-me`~~ ~~`penediu-nos`~~ |
| 03S | `penedeixi's` | — |
| 03P | `penedeixin-se` | — |

O sigui que a `llicencies.py` calen **dues matrius**, no una: la general del §3.4 (per als verbs que tenen lectura de datiu disponible) i aquesta, d'exacta concordança, per als 392 inherents.

### 2.5 El cas `ajup-hi`, matisat

L'altre dia et vaig dir que `ajup-hi` no servia. Ho he de matisar: **`ajupir` no és inherentment pronominal** (el DIEC li dona `v. intr. pron.` *i* `v. tr.`), per tant la regla de dalt no l'exclou — i en la lectura transitiva amb locatiu la forma és defensable: *«a l'entrada del túnel, ajup-hi el cap»*.

El problema real de `ajup-hi` no és que sigui agramatical, sinó que **la lectura que et ve al cap primer** (la pronominal, *ajupir-se*) demana `ajup-t'hi`, que és de 2 pronoms i encara no existeix. És un problema de *qualitat percebuda*, no de gramàtica, i afecta els 1.070 verbs que són pronominals **i** alguna cosa més. Ho deixo com a decisió pendent (**P4**) perquè no té una solució neta amb aquestes dades.

---

## 3. Revisió de l'imperatiu

Tenies raó que cal remirar-lo. Tres troballes.

### 3.1 Completesa dels codis: ✅ correcta

He enumerat **tots** els codis del diccionari gran amb `M` a la posició 2 (mode imperatiu segons EAGLES). El script actual no en perd cap:

| Codi | Files | Persona |
|---|---|---|
| `VMM02S00` | 8.965 | tu |
| `VMM02S0Y` | 7 | tu (`obre`, `omple`, `reomple`…) |
| `VSM02S00` | 1 | tu (`sigues`) |
| `VMM01P00` | 8.816 | nosaltres |
| `VSM01P00` | 1 | nosaltres (`siguem`) |
| `VMM02P0X` | 7.648 | vosaltres |
| `VMM02P00` | 1.156 | vosaltres |
| `VSM02P00` | 1 | vosaltres (`sigueu`) |
| `VMM03S0Y` | 8.795 | vostè |
| `VMM03S00` | 2 | vostè (`càpiga`, `sàpiga`) |
| `VSM03S0Y` | 1 | vostè (`sigui`) |
| `VMM03P0Y` | 8.771 | vostès |
| `VMM03P00` | 2 | vostès (`càpiguen`, `sàpiguen`) |
| `VSM03P0Y` | 1 | vostès (`siguin`) |
| **Total** | **44.167** | |

Els altres codis amb `M` a la posició 2 (`NCMS000`, `NPMSG00`…) són **noms**, on la `M` és el gènere masculí, no el mode. **No hi ha `VAM*`**: `haver` no té imperatiu.

Detall que justifica incloure les variants rares: per a `obrir`, la forma de "tu" (`obre`) està etiquetada **només** `VMM02S0Y`. Si agaféssim únicament `VMM02S00`, perdríem `obre`, `omple`, `reomple`, `entreobre`, `pellobre`, `desomple` i `reobre`.

### 3.2 Què volen dir `X` i `Y` (verificat, no suposat)

- **`X` = 1a conjugació.** `VMM02P0X` són 7.625 verbs en `-ar` + 23 en `-ir`; `VMM02P00` són 871 en `-ir` + 278 d'altres + 1 en `-ar`. **No és** la distinció vós/vosaltres que jo havia suposat al pla general: `vós` i `vosaltres` són homògrafs (`canteu`) i no cal tractar-los per separat.
- **`Y` marca homografia amb una altra cel·la del paradigma.** `canti` surt alhora com a `VMM03S0Y` i `VMSP1S0Y`; `cantin` com a `VMM03P0Y` i `VMSP3P0Y`.

### 3.3 Les formes homògrafes del subjuntiu: sí que s'han de generar

Això era el teu dubte principal. La resposta és que **`canti-hi` i `cantin-hi` són correctes**, i el motiu és decisiu:

> El subjuntiu **no admet enclisi**. Els pronoms hi van al davant: *«que hi canti»*, no *«que canti-hi»*.
> L'única forma que porta el pronom **darrere** és l'imperatiu.

Per tant, quan el rimador ensenyi `canti-hi`, no hi ha cap ambigüitat possible: només pot ser l'imperatiu de cortesia (vostè). El fet que `canti` sigui homògraf del subjuntiu al diccionari base **no crea cap homògraf nou** entre les formes que generem, perquè el subjuntiu mai no arriba a tenir forma enclítica.

El que sí que cal saber: aquestes dues persones són **17.566 files (40 % de l'imperatiu)** i acaben totes en vocal (`-i`, `-in`), o sigui que són les que activen a gran escala la decisió **D7** del pla general (`canti-hi` → `/kˈantij/`, amb fusió). Segueix sent la decisió amb més impacte de tot l'imperatiu.

### 3.4 El que falta de debò: la concordança de persona

Aquest és el forat real del script actual, i no és petit: **genera 80.636 formes agramaticals**.

L'imperatiu té subjecte propi, i un pronom de 1a/2a persona només és vàlid si el seu referent **coincideix exactament** amb el subjecte (lectura reflexiva) o n'és **completament disjunt**. El solapament parcial és agramatical:

| Subjecte | `em` (1s) | `ens` (1p) | `et` (2s) | `us` (2p) | `es` (3refl) |
|---|---|---|---|---|---|
| **02S** tu | ✅ `canta'm` | ✅ `canta'ns` | ✅ refl. `canta't` | ❌ `canta-us` | ❌ |
| **01P** nosaltres | ❌ `cantem-me` | ✅ refl. `cantem-nos` | ✅ `cantem-te` | ✅ `cantem-vos` | ❌ |
| **02P** vosaltres | ✅ `canteu-me` | ✅ `canteu-nos` | ❌ `canteu-te` | ✅ refl. `canteu-vos` | ❌ |
| **03S** vostè | ✅ `canti'm` | ✅ `canti'ns` | ❌ | ❌ | ✅ refl. `canti's` |
| **03P** vostès | ✅ `cantin-me` | ✅ `cantin-nos` | ❌ | ❌ | ✅ refl. `cantin-se` |

`cantem-me` és agramatical perquè *jo* soc dins de *nosaltres*: la lectura hauria de ser reflexiva, i el reflexiu de 1a plural és `ens`, no `em`. Mateixa cosa amb `canteu-te`.

`li`, `els`, `el`, `la`, `les`, `ho`, `hi` i `en` **no** els afecta aquesta matriu: el seu referent és sempre de 3a persona o no personal, i per tant sempre disjunt del subjecte.

### 3.5 Duplicats a la sortida: acceptables

Les 88.334 línies que has generat contenen **170 formes repetides** (172 files sobrants), sempre perquè **dos lemes diferents produeixen la mateixa forma**: `atendre`/`atenir` → `atén-hi`, `botar`/`botre` → `botem-hi`. Com que el `col_1` és diferent i el rimador ensenya el lema entre parèntesis (`atén-hi (atendre)` / `atén-hi (atenir)`), **es distingeixen i tots dos són correctes**. El diccionari base ja fa exactament això. No cal desduplicar.

L'excepció menor: `ves` surt **tres** vegades, i dues són el mateix lema `anar` amb el flag `Viq` diferent (`Viq` / `NO`) — això sí que és una duplicació del diccionari base. Val la pena mirar-s'ho algun dia, però és fora de l'abast d'aquest projecte.

---

## 4. Esquema de codis: amplada fixa i posicional

El format actual (`WN00_1HI`, `WM02S_1HI`) té un problema: **el nombre de pronoms cau a una posició diferent** segons la forma (índex 5 a l'infinitiu, 6 a l'imperatiu). Això impedeix filtrar «combinacions d'un pronom» o «de dos» sense enumerar casos.

Proposo **amplada fixa de 10 caràcters, sense separador**, que és com ja funcionen els codis EAGLES d'aquest diccionari — i que `js/script.js` ja indexa per posició (`array2[i][4] === "P"` per als plurals):

```
   posició:   0    1      2 3 4      5      6 7      8 9
              W    F      P P P      N      A A      B B
              │    │      └──┬──┘    │      └─┬┘     └─┬┘
              │    │         │       │        │        │
              │    │         │       │        │        └── pronom 2 ("00" si no n'hi ha)
              │    │         │       │        └─────────── pronom 1
              │    │         │       └──────────────────── nombre de pronoms: 1 o 2
              │    │         └──────────────────────────── persona: 000 (inf/ger)
              │    │                                                02S 01P 02P 03S 03P (imp)
              │    └────────────────────────────────────── forma: N infinitiu
              │                                                   G gerundi
              │                                                   M imperatiu
              └─────────────────────────────────────────── W = verb + pronom
```

| Forma | Codi |
|---|---|
| `anar-hi` | `WN0001HI00` |
| `cantar-lo` | `WN0001EL00` |
| `anant-hi` | `WG0001HI00` |
| `ves-hi` | `WM02S1HI00` |
| `canti's` | `WM03S1ES00` |
| `porta-l'hi` *(fase 2)* | `WM02S2LIEL` |
| `penedir-se'n` *(fase 2)* | `WN0002ESNE` |

Filtres que en surten:

| Què vols | Com |
|---|---|
| tota la secció | `codi.startsWith('W')` |
| infinitius / gerundis / imperatius | `startsWith('WN')` / `'WG'` / `'WM'` |
| imperatius de "tu" | `startsWith('WM02S')` |
| només 1 pronom (o només 2) | `codi[5] === '1'` |
| conté el pronom `hi` | `codi.slice(6,8)==='HI' \|\| codi.slice(8,10)==='HI'` |

`W` és lliure: les primeres lletres ocupades del diccionari són només `A`, `D`, `N`, `P`, `V`, `Z`.

### Ordre canònic dels dos pronoms (ja per a la fase 2)

Quan hi hagi 2 pronoms, s'escriuen al codi **en l'ordre gramatical de col·locació**, no alfabètic:

```
es  >  et/us  >  em/ens  >  li/els  >  el/la/els/les  >  en  >  hi  >  ho
```

Així el codi és únic i predictible: `penedir-se'n` sempre serà `...2ESNE`, mai `...2NEES`.

---

## 5. Arquitectura del programa

La teva proposta és bona (recórrer pronom per pronom, calcular la llista de verbs, generar). Hi faig **una esmena**: no invocar tres scripts independents 13 vegades cadascun, sinó **partir el que ja tenim en mòduls compartits**.

Motiu: els tres generadors actuals ja comparteixen ~80 % del codi (`llegir_columna`, `calcular_rimes`, `silabes`, `construir_codi`, la taula d'enclisi) i **ja han divergit** entre ells — el de l'infinitiu té la semivocalització de `-hi`, el del gerundi no la necessita, el de l'imperatiu té el seu propi sàndhi de `-s`. Multiplicar-ho per 13 pronoms garanteix que se'ns escapi una incoherència.

```
pronoms/
├── llicencies.py     # verbs_anotats_num.json -> {pronom: set(lemes que l'accepten)}
│                     #   · classificador de construccions (tr / intr / pron)
│                     #   · les regles del §1 i §2
│                     #   · la matriu de persona del §3.4
│
├── enclisi.py        # tot el que és ortografia i fonètica, per forma verbal:
│                     #   · forma_enclitica(pronom, forma)   -> "-hi" / "'n" / "-me"...
│                     #   · transcriure(forma, AFI, enclitic, tipus_forma)
│                     #        - r d'infinitiu:  [ɾ] / [r]
│                     #        - t de gerundi:   [t] / cau
│                     #        - s final:        -> [z]
│                     #        - semivocal de -hi/-ho darrere vocal
│                     #   · silabes(base, enclitic, fonema)
│                     #   · calcular_rimes(AFI)
│                     #   · construir_codi(forma, persona, pronoms)
│
└── generar_tot.py    # el driver:
                      #   per cada pronom (13)
                      #     llista de lemes = llicencies[pronom]
                      #     per cada forma base del diccionari (inf/ger/imp)
                      #        si el lema hi és i la matriu de persona ho permet:
                      #           emet la línia
                      #   -> pronoms/verb_pronom_1.txt   (un sol fitxer)
```

Avantatges concrets d'aquesta forma:

- **Una sola definició** de cada regla fonètica: si canviem la `-r` de l'infinitiu, canvia a tot arreu de cop.
- **Un sol fitxer de sortida**, que és el que necessitarà la UI (§4.3 de `pla.md`: dataset separat amb la seva versió).
- Els tres scripts actuals (`generar_infinitius_hi_en.py`, `generar_gerundis_hi_en.py`, `generar_imperatius_hi_en.py`) queden com a **referència** i es poden esborrar quan `generar_tot.py` reprodueixi les seves sortides. **Proposo validar-ho així**: primer fer que `generar_tot.py` limitat a `hi`+`en` doni exactament els mateixos fitxers que ja tenim a `pronoms/txt_fets/`, i només llavors obrir-lo als 13 pronoms.

---

## 6. Volum previst

Formes base disponibles: 8.914 infinitius + 8.789 gerundis + 44.167 imperatius = **61.870**.

Repartiment per classe de verb, amb P1 i P6 aplicats i la correcció del §2.4:

| Classe de verb | Formes generades |
|---|---|
| **2** transitiu (± pronominal) | 549.786 |
| **4** intransitiu pur | 69.445 |
| **1** pronominal inherent | 5.920 |
| **3** intransitiu + pronominal | 1.635 |
| **0** sense informació | 0 |
| **TOTAL** | **626.786** |

Descartades per concordança de persona: **86.011**.

Per comparació: el diccionari actual té 619.785 entrades i pesa 41,9 MB en columnes. Aquestes 626.786 formes són **+101 %**, uns 43 MB més. Confirma la decisió de `pla.md` §4.3: **dataset separat, carregat sota demanda**, no fusionat.

---

## 7. Decisions pendents

Totes resoltes (agost del 2026):

| | Decisió | Resolució |
|---|---|---|
| **P1** | Els 422 verbs **sense informació** al DIEC (413 no trobats + 9 sense categories) | ✅ **Es salten, no generen cap pronom.** Amb un `if` aïllat i comentat a `llicencies.py` per poder-ho canviar sense tocar res més |
| **P2** | `li`/`els` datiu obert a tots els verbs | ✅ Sí, s'accepta la sobregeneració |
| **P3** | `en` obert a tots els verbs | ✅ Sí |
| **P4** | Pronominals no inherents amb 1 pronom, tot i que la lectura natural en demani 2 | ✅ Sí |
| **P5** | `-hi`/`-ho` darrere vocal: semivocal amb fusió sil·làbica | ✅ Sí, coherent amb `veure-hi` |
| **P6** | Matriu de concordança de persona a l'imperatiu | ✅ Sí, descartar les agramaticals |

Queda **una decisió nova**, sorgida en previsualitzar (§2.4): la segona matriu, d'**exacta** concordança, per als 392 verbs inherentment pronominals — la que evita `penedeix-me`. La dono per bona perquè és el mateix criteri de P6 aplicat a un cas on no hi ha lectura de datiu; si no hi estàs d'acord, digues-ho abans del pas 3.

---

## 8. Ordre de treball proposat

1. Validar aquest document (sobretot **P1** i **P6**).
2. `enclisi.py` — mou-hi la lògica dels tres scripts actuals, sense canviar-ne el comportament.
3. `llicencies.py` — el classificador i la matriu.
4. `generar_tot.py` limitat a `hi` + `en` → **ha de reproduir byte a byte** el que ja hi ha a `pronoms/txt_fets/`, tret del codi nou de 10 caràcters.
5. Obrir-lo als 13 pronoms i mesurar.
6. Comprovacions de sanitat: 10 camps per línia, un sol accent primari, cap col·lisió amb `col_0`, rimes coherents amb `col_3`/`col_4`.
