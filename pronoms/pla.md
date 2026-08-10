# Pla: combinacions verb + pronom feble al Rimador

> Document de disseny. **No s'ha escrit cap generador ni s'ha tocat el diccionari de producció.**
> Totes les xifres d'aquest document surten de mesures reals sobre `diccionaris/separat/col_*.txt`
> i `pronoms/verbs_anotats.json` (agost del 2026, diccionari 5.2.3, 619.785 entrades).

---

## 0. Resum executiu

| Fase | Decisió recomanada |
|---|---|
| 1. Llengua | Generar **un sol pronom** per forma. Restringir acusatiu i partitiu per transitivitat; deixar `hi` obert; restringir el reflexiu per concordança de persona. **Deixar les combinacions dobles per a una fase 2**, tret d'un subconjunt curat (`anar-se'n`, `emportar-se'l`…). |
| 2. Generació | Script reproduïble que fa el *join* `verbs_anotats.json` ↔ `col_1`, itera les formes reals del diccionari (`VMN`, `VMG`, `VMM*`) i aplica taules tancades. **Cal afegir 3 camps nous** a la llista de verbs. |
| 3. UI | **Opció B: filtre opcional, desactivat per defecte.** Secció nova "Verbs + pronoms" amb 3 subcaselles (infinitiu / gerundi / imperatiu). **Sense un tercer nivell** per tipus de pronom. |
| 4. Codificació | Codi propi amb prefix **`W`** (lletra lliure), format `W` + forma + persona + `_` + pronom. Compatible amb el `startsWith()` que ja fa servir la UI. |
| 5. Rima | **Alternativa (a): calcular la transcripció real** = transcripció base (`col_9`) + enclític + 5 regles de sàndhi. L'alternativa (b) (heretar la rima del verb) **falla** en el cas central: `anar` → `a`, però `anar-hi` → `aɾi`. |
| Dades | **Dataset separat, carregat sota demanda**, no fusionat amb `col_*.txt`. |

---

## 1. Fase 0 — Què hi ha ara

### 1.1 El diccionari

Format de `diccionaris/diccionari.5.2.3.txt`, 10 camps separats per `$`:

| # | Camp | Exemple (`escenari`) |
|---|---|---|
| 0 | paraula | `escenari` |
| 1 | lema / d'on ve | `escenari` |
| 2 | codi EAGLES | `NCMS000` |
| 3 | **rima consonant** | `aɾi` |
| 4 | **rima assonant** | `ai` |
| 5 | síl·labes | `4` |
| 6 | Viccionari | `Vicc` |
| 7 | Viquipèdia | `Viq` |
| 8 | DIEC | `Diec` |
| 9 | transcripció AFI | `əsənˈaɾi` |

### 1.2 Com es calcula la rima avui

A `creador_rima + dicc (a partir de col_10).py`:

```python
final = transcripcio.split("ˈ")[-1]                      # col_3, rima consonant
vocal = [l for l in final if l in "ɔəaeiou@Eɛˈ"]         # col_4, rima assonant
```

Tres conseqüències importants per a aquest projecte:

1. La rima consonant és **tot el que va després de l'ÚLTIM accent primari**. Les formes noves han de portar **un sol `ˈ`**, sobre el verb (és la norma: el grup verb+pronoms es pronuncia amb un únic accent tònic, el del verb).
2. La rima assonant només conserva vocals plenes: **`j` i `w` es descarten**. Això fa que la decisió "`-ho` darrere vocal és `u` o `w`?" canviï els resultats de la rima assonant. Vegeu §5.3.
3. `col_5` (síl·labes) **no el genera cap script del repositori**: no es dedueix ni de la transcripció (1.817 files no hi quadren) ni de res més. És un recompte **ortogràfic** heretat de la font. Per a les formes noves l'haurem de calcular nosaltres.

### 1.3 El motor del rimador

`js/script.js` carrega els 10 fitxers `col_*.txt` a 10 arrays paral·lels (índex `i` = una entrada), els cacheja a IndexedDB amb versió, i a cada cerca recorre linealment les 619.785 entrades filtrant per síl·labes, lletra inicial, rima (`col_3` o `col_4`), noms propis i plurals.

Els filtres de categoria són **tots** de la forma `item[2].startsWith(prefix)` (`crearCriteris`), i les caselles s'associen per **text de l'etiqueta** (`checkboxLabel in checkboxCriteria`). Estructura fixa de dos nivells: 6 seccions × subcategories.

**Pes actual:** 41,9 MB de columnes, ~68 bytes per entrada.

### 1.4 El pipeline (dues portes d'entrada)

```
    edició de diccionari.5.2.3.txt          edició de col_10 (canvis aquí)/*.txt
                 │                                        │
    separar_arxiu (workflow                   pre_proces + creador_rima
    "actualitzar_versio_general")             (workflow "diccionaris")
                 │                                        │
        genera col_0 … col_9                  genera col_0,1,2,3,4,9  ⚠ NO 5,6,7,8
                 │                                        │
                 └──────────► versions.json (+1) ◄────────┘
                              naufragues, mots_de7, bot
```

⚠️ **Trampa a evitar:** la porta de `col_10` **no regenera `col_5`, `col_6`, `col_7`, `col_8`**. Si s'hi afegeixen línies, les quatre columnes queden desalineades i tot el diccionari es corromp. Qualsevol alta d'entrades noves ha d'entrar per `diccionari.5.2.3.txt` (o per un dataset propi, que és el que recomano a §3).

### 1.5 La llista de verbs

`pronoms/verbs_anotats.json`: **9.016 verbs**, extrets del diccionari i anotats amb les categories del DIEC (`scrap_diec.py`).

- Estat: 8.511 OK · 413 no trobats al DIEC · 92 sense categories.
- **El join és perfecte:** els 9.016 lemes coincideixen exactament amb els 9.016 lemes verbals únics de `col_1`. És la clau d'unió natural.

Camps que hi ha (13 categories úniques, descompostes en construccions atòmiques):

| Construcció | Verbs |
|---|---|
| `v. tr.` | 6.729 mencions → **6.695 verbs amb construcció transitiva no pronominal** |
| `v. intr.` | 1.888 |
| `v. intr. pron.` | 1.349 |
| `v. tr. pron.` | 69 |
| `v. aux.` | 23 |

- Verbs amb **alguna** construcció pronominal: 1.394.
- Verbs **només** pronominals (inherents: `abstenir-se`, `penedir-se`, `queixar-se`…): 389.

**Camps que falten** (i que cap categoria del DIEC dona):

| Camp que falta | Per a què el necessitem | Impacte |
|---|---|---|
| **Preposició regida** (`a` / `en` / `amb` / `de`) | decidir si el verb admet `hi` per complement de règim, i `en` per complement amb `de` | mitjà (§2.4) |
| **Ditransitivitat** (admet CI de 3a persona) | decidir `li` / `els` datiu | **alt** — avui és indeduïble |
| **Pronominal inherent vs. reflexiu ocasional** | `penedir-se` (obligatori) vs. `rentar-se` (opcional) | mitjà |
| Verb de moviment | `en` de CCL d'origen (`anar-se'n`) | baix |

### 1.6 Precedents útils que ja hi ha al diccionari

Hi ha **1.829 entrades amb guionet**, i el seu tractament fonètic és exactament el que necessitem:

| Entrada | Transcripció | Què demostra |
|---|---|---|
| `agar-agar` | `əɣˈaɾəɣˈar` | la **r final es pronuncia `ɾ`** quan darrere el guionet hi ha vocal; `r` quan és final absoluta |
| `despús-ahir` | `dəspˈuzəˈi` | **sonorització de la `-s`** a través del guionet |
| `més-enllà` | `mˈezəɲʎˈa` | ídem |
| `vis-a-vis` | `bˈizəβˈis` | sonorització **+ espirantització de `v` → `β`** darrere vocal |
| `Al-Àndalus` | `əlˈandəlus` | un grup amb guionet pot tenir **un sol accent primari** |
| `abans-d'ahir` | `əβˈansdəˈi` (4 síl.) | l'apòstrof **no compta com a síl·laba** |

També confirma que `col_5` compta síl·labes ortogràfiques del mot sencer (`despús-ahir` = 4, `vis-a-vis` = 3).

---

## 2. Fase 1 — Quines combinacions verb+pronom són vàlides

Fonts normatives consultades (§9). El quadre gràfic de l'enclisi està **confirmat** i coincideix exactament amb la taula que ja tens a `pronoms.docx`.

### 2.1 Ortografia de l'enclisi (verificada, no inventada)

La regla **no** és fonètica sinó **gràfica**: depèn de com acaba el verb **escrit**.

> Forma **plena** amb guionet si el verb acaba en **consonant o en `u`** (diftong);
> forma **reduïda** amb apòstrof si acaba en **qualsevol altra vocal**.

| Pronom | Darrere consonant o `-u` | Darrere vocal (excepte `u`) |
|---|---|---|
| em | `-me` | `'m` |
| et | `-te` | `'t` |
| es | `-se` | `'s` |
| ens | `-nos` | `'ns` |
| us | `-vos` | `-us` |
| el | `-lo` | `'l` |
| la | `-la` | `-la` |
| els | `-los` | `'ls` |
| les | `-les` | `-les` |
| li | `-li` | `-li` |
| en | `-ne` | `'n` |
| ho | `-ho` | `-ho` |
| hi | `-hi` | `-hi` |

Aplicat a les tres formes:

- **Infinitiu** — acaba en `-r` (consonant gràfica, encara que sigui muda) → sempre forma plena: `cantar-me`, `cantar-lo`, `cantar-ne`, `anar-hi`.
  Excepció: els infinitius en **`-re`** acaben en vocal → `veure'l`, `escriure'n`, `prendre's`, però `veure-la`, `veure-hi`.
- **Gerundi** — sempre acaba en `-nt` → sempre forma plena: `cantant-me`, `cantant-ho`, `anant-hi`.
- **Imperatiu** — varia forma per forma; és l'únic cas on cal mirar la lletra final:
  `canta'm` / `canteu-me` / `cantem-nos` / `canti'm` / `pren-me` / `beu-ne` / `digues-ho` / `ves-hi`.

**El repartiment no és per persona sinó per lletra final.** Verificat sobre les dades: `-a` i `-i` (canta, canti) → apòstrof; `-eu`, `-iu` (canteu, abaltiu) → guionet perquè acaben en `u`; `-em`, `-in`, `-s` (cantem, cantin, digues) → guionet perquè acaben en consonant.

### 2.2 Correcció sobre l'imperatiu: no hi ha "vós" a les dades

L'enunciat parlava de `tu/vós/vostè/vosaltres`. Les etiquetes reals del diccionari són:

| Etiqueta | Entrades | Persona | Exemple |
|---|---|---|---|
| `VMM02S00` | 8.966 | tu | `abaixa` |
| `VMM01P00` | 8.816 | nosaltres | `abaixem` |
| `VMM02P0X` | 7.648 | vosaltres | `abaixeu` |
| `VMM02P00` | 1.156 | vosaltres | `abaltiu`, `abateu` |
| `VMM03S0Y` | 8.795 | vostè | `abaixi` |
| `VMM03P0Y` | 8.771 | vostès | `abaixin` |
| `VMM02S0Y` | 7 | soroll | `obre`, `omple` |
| `VMM03S00` / `VMM03P00` | 4 | soroll | `càpiga`, `sàpiga` |

`VMM02P0X` i `VMM02P00` **són la mateixa persona** (7.648 + 1.156 ≈ 8.800 ≈ un per verb): la `X` marca els verbs de la 1a conjugació i el `0` la resta. És un artefacte de l'etiquetatge d'origen, **no** una distinció vós/vosaltres. La forma de "vós" i la de "vosaltres" són homògrafes (`canteu`), o sigui que no cal tractar-les per separat.

⚠️ **Decisió pendent D1:** `VMM03S0Y`/`VMM03P0Y` (vostè/vostès) són **homògrafes del subjuntiu** (`vagi` és alhora `VMSP1S0Y` i `VMM03S0Y`). Si generem `vagi-hi`, la forma és correcta com a imperatiu de cortesia però el diàleg d'homògrafs no ho distingirà. Són 17.566 formes base (28 % del total). *Les incloem o les deixem fora?*

### 2.3 Compatibilitat pronom ↔ verb, pronom per pronom

#### Acusatiu determinat: `el` / `la` / `els` / `les`
Exigeixen verb amb **construcció transitiva**. Derivable amb fiabilitat: **6.695 verbs** (els que tenen `v. tr.` no pronominal). ✅ Regla clara.

#### `ho` (neutre)
També és acusatiu, però substitueix un CD **neutre o proposicional** (`això`, `allò`, una subordinada), no un SN determinat. La restricció formal és la mateixa (verb transitiu), però el conjunt natural és més estret: els verbs que admeten CD oracional (`dir`, `saber`, `veure`, `fer`, `voler`, `entendre`…).
Amb les dades actuals només podem aplicar-hi la restricció de transitivitat, i llavors surten formes gramaticalment correctes però semànticament estranyes (`abadernar-ho`).
⚠️ **Decisió pendent D2:** acceptem la sobregeneració de `ho`, o el limitem a una llista curada de verbs de dicció/percepció/cognició?

#### Datiu de 1a i 2a persona: `em` / `et` / `ens` / `us`
**No es poden restringir per transitivitat.** A més del CI pròpiament dit, el català té el **datiu ètic o d'interès**, que s'adjunta a pràcticament qualsevol verb (*no me'l toquis*, *se'm va morir*, *menja't la sopa*). Restringir-los per transitivitat deixaria fora formes perfectament vives.
**Recomanació:** permetre'ls amb tots els verbs. És la classe que més sobregenera, però l'alternativa (restringir) genera falsos negatius pitjors.

#### Datiu de 3a persona: `li` / `els`
Exigeix que el verb admeti un CI. Prototípicament ditransitius (`donar`, `dir`, `portar`, `enviar`), però també molts intransitius (`agradar`, `convenir`, `doldre`, `passar`).
**Les categories del DIEC no codifiquen la ditransitivitat.** No és derivable de les dades actuals.
⚠️ **Decisió pendent D3:** (a) tractar-los com els datius de 1a/2a i obrir-los a tots els verbs; (b) limitar-los als transitius (aproximació grollera: perd `agradar-li`); (c) afegir un camp nou de ditransitivitat. **La meva recomanació és (a)**, coherent amb el tractament del datiu ètic i sense necessitat de dades noves.

#### `hi`
**Contraintuïtivament, és el pronom MENYS restringit, no el més.** `hi` recull:
1. el **complement circumstancial** de lloc, manera o instrument — i gairebé qualsevol verb d'acció admet un CC (*cantar-hi*, *dormir-hi*, *menjar-hi*, *ploure-hi*);
2. el complement de règim amb `a` / `en` / `amb` (*pensar-hi*, *dedicar-s'hi*) — aquest sí, verb per verb;
3. el complement predicatiu (*tornar-s'hi*).

Com que (1) és quasi universal, no cal cap camp nou: **`hi` es pot obrir a tots els verbs**. ✅ (I és, precisament, el cas que motiva tot el projecte: `anar-hi`.)

#### `en`
Recull quatre coses: CD partitiu indeterminat (→ **verbs transitius**), CCL d'origen amb `de` (→ verbs de moviment), complement de règim amb `de` (*parlar-ne*, *penedir-se'n*) i predicatiu amb `fer-se`/`dir-se`.
El partitiu ja cobreix la majoria i és derivable per transitivitat.
**Recomanació:** generar `en` per als **6.695 transitius** (partitiu) i afegir-hi els verbs de règim amb `de` quan tinguem el camp nou. Marcat com a millora, no com a bloqueig.

#### Verbs pronominals
Dues subtileses que canvien la generació:

1. **L'infinitiu del diccionari no porta el pronom**: hi ha `penedir` (`VMN00000`), no `penedir-se`. O sigui que les formes pronominals **s'han de generar**, no extreure.
2. **El pronom reflexiu concorda amb el subjecte.** A l'infinitiu i al gerundi el pronominal no genera *una* forma sinó **cinc**: `penedir-me`, `penedir-te`, `penedir-se`, `penedir-nos`, `penedir-vos`. A l'imperatiu la persona ja el fixa:

   | Persona | Forma |
   |---|---|
   | tu | `penedeix-te` |
   | nosaltres | `penedim-nos` |
   | vosaltres | `penediu-vos` |
   | vostè | `penedeixi's` |
   | vostès | `penedeixin-se` |

   Aquesta és una **restricció forta i fiable** que redueix molt el volum de l'imperatiu i n'apuja molt la qualitat.

#### Concordança de persona a l'imperatiu (regla general)
Val per a tots els pronoms, no només el reflexiu:

- El pronom **reflexiu ha de coincidir** amb la persona de l'imperatiu: `canta't` ✅ (tu + 2a sing.), `canta-us` ❌ (tu + 2a pl.).
- Un pronom de 1a/2a persona **no reflexiu** no pot coincidir amb el subjecte: `digueu-me` ✅ (vosaltres + 1a sing.), `diguem-me` ❌ (nosaltres + 1a sing.).

Sense aquesta regla es generen ~7.978 formes agramaticals per cada casella de rima de l'imperatiu de 1a persona del plural. **Recomanació: implementar-la des del primer dia.**

### 2.4 Combinacions de dos pronoms — **recomanació: fase 2**

Motius concrets, per ordre de pes:

1. **Volum.** Amb un sol pronom ja generem 804.258 formes (§3.1). Amb parelles vàlides (~40 per forma base) passaríem de 2,5 milions: **quatre vegades el diccionari sencer**.
2. **És un segon sistema ortogràfic independent**, no una extensió del primer. Cal implementar, com a mínim: l'ordre de col·locació (`es` > `et`/`us` > `em`/`ens` > `li`/`els` > `el`/`la`/`els`/`les` > `en` > `hi` > `ho`); la transformació `li` → `hi` amb inversió d'ordre (`li`+`el` = `l'hi`, `li`+`la` = `la hi`, `li`+`els` = `els hi`, `li`+`les` = `les hi`); la regla de l'apòstrof "tan a la dreta com sigui possible" (`prengui-s'ho`, no `prengui's-ho`); l'excepció `el`+`en` = `l'en` (`treu-l'en`, no `treu-le'n`); i el fet que `es`/`et`/`em` en primera posició prenen sempre forma plena o elidida (`se`, `te`, `me`).
3. **Depèn justament de les dades que no tenim** (§1.5): una parella datiu+acusatiu pressuposa ditransitivitat.
4. **El retorn poètic és baix.** Les formes de doble pronom són esdrúixoles o sobreesdrúixoles i **no rimen amb res del diccionari actual**: `emporta-te'n` (0 rimes), `renta-te'l` (0 rimes), `porta-l'hi` (0 rimes). Només rimarien entre elles.

**Excepció recomanada (fase 1.5):** el subconjunt **verb pronominal inherent + segon pronom** (`anar-se'n`, `emportar-se'l`, `penedir-se'n`, `oblidar-se'n`) és freqüent, lexicalitzat i es pot fer sobre una llista curada de poques desenes de verbs, sense necessitat de resoldre el cas general.

---

## 3. Fase 2 — Estratègia de generació

### 3.1 Volum: la dada que condiciona tot el disseny

Formes base disponibles al diccionari: **61.866** (8.914 infinitius + 8.789 gerundis + 44.163 imperatius).

| Abast | Formes noves | vs. diccionari actual (619.785) |
|---|---|---|
| Infinitius × 13 pronoms | 115.882 | +19 % |
| Infinitius + gerundis × 13 | 230.139 | +37 % |
| Tot × només `hi`/`ho`/`en` | 185.598 | +30 % |
| **Tot × 13 pronoms** | **804.258** | **+130 %** |

I la cobertura de rima (quantes formes noves rimen amb alguna paraula que **ja** existeix):

| Forma | Formes noves | Rimen amb el diccionari actual |
|---|---|---|
| Infinitiu | 115.882 | **96,4 %** |
| Gerundi | 114.257 | 44,7 % |
| Imperatiu | 574.119 | **32,3 %** |
| Total | 804.258 | 43,3 % |

**Lectura:** l'infinitiu és on hi ha gairebé tot el valor (96 % de cobertura) i només el 14 % del volum. L'imperatiu és el 71 % del volum i el que menys rima amb res. De les 20.069 classes de rima que generarien les formes noves, **17.330 no existeixen avui al diccionari**: aquestes formes es rimen sobretot **entre elles**.

### 3.2 Arquitectura del generador

Script reproduïble a `pronoms/generar_formes.py`:

```
verbs_anotats.json ──┐
                     ├─► regles de compatibilitat  ──► (verb, forma_base, pronom) vàlids
col_1 (lema) ────────┘                                          │
col_0/2/5/9 (forma, codi, síl·labes, AFI) ──────────────────────┤
                                                                ▼
                          taula d'enclisi (§2.1)  +  taula fonètica (§5.2)
                                                                ▼
                       forma gràfica · codi W · rima cons. · rima ass. · síl·labes · AFI
                                                                ▼
                              pronoms/formes_pronominals.txt  (mateix format $)
```

Punts clau del disseny:

- **No cal cap motor de transcripció grafema→fonema.** Reutilitzem `col_9` de la forma base i hi enganxem l'enclític aplicant 5 regles de sàndhi (§5.2). Això és el que fa el mètode viable.
- **Tot són taules tancades**: 13 pronoms × 2 formes gràfiques, 13 transcripcions, una matriu de concordança de persona. Res no depèn d'heurístiques.
- **Iterem sobre les formes reals del diccionari**, no sobre paradigmes reconstruïts. Així no inventem res: si el diccionari té `ves` i no `vés`, generarem `ves-hi`.
- **Sortida en el mateix format `$` de 10 camps**, per poder reaprofitar `separar_arxiu` sense tocar-lo.

### 3.3 Dades noves que cal afegir a la llista de verbs

Per ordre de prioritat:

| Prioritat | Camp | Valors | Bloqueja |
|---|---|---|---|
| 1 | `pronominal_inherent` | booleà | distingir `penedir-se` de `rentar-se`; ja parcialment deduïble (389 verbs) |
| 2 | `preposicio_regida` | `a` / `en` / `amb` / `de` / cap | `en` de règim, `hi` de règim |
| 3 | `ditransitiu` | booleà | `li` / `els` datiu (només si es descarta la recomanació D3-a) |
| 4 | `moviment` | booleà | `en` de CCL d'origen |

Els camps 1 i 2 es poden extreure **del text de les definicions del DIEC** que `scrap_diec.py` ja descarrega però descarta: avui el `patro_categories` només captura `v. ...` fins al primer `[`. Les definicions contenen les preposicions de règim de manera prou sistemàtica. **Recomanació: reaprofitar el mateix scraping en comptes de fer una llista manual.**

---

## 4. Fase 3 — Integració al rimador (UI i filtres)

### 4.1 Opció A (barrejades) vs. Opció B (filtre opcional)

La dada que decideix — cerca de **`escenari`** (rima consonant `aɾi`):

| | Resultats |
|---|---|
| Avui | **755** |
| Amb totes les formes verb+pronom | **8.401** (+7.646) |

**Pràcticament tots els 7.646 afegits són el mateix patró**: infinitiu en `-ar` + `hi` (n'hi ha 7.668 al diccionari) — `abacallanar-hi`, `abadanar-hi`, `abadernar-hi`, `abadocar-hi`, `abaixar-hi`… Amb l'opció A, la paraula que va motivar el projecte deixaria de ser útil: el resultat real quedaria enterrat sota 7.600 infinitius consecutius amb la mateixa terminació.

**→ Recomanació: Opció B, i desactivada per defecte.**

Arguments addicionals:

- **Rendiment.** `buscarParaula` recorre linealment totes les entrades a cada cerca. Amb l'opció A la càrrega inicial passaria de 41,9 MB a ~96 MB i la cerca es faria 2,3× més lenta **per a tothom**, també per als qui no vulguin aquestes formes.
- **Efectes col·laterals.** Les llistes derivades (`paraules_naufragues.json`, `mots_de7_*`, `bot/resultat_ordenat_cons.json`) es generen de les mateixes columnes. Fusionar-ho canviaria **silenciosament** la llista de nàufragues: paraules que avui no rimen amb res passarien a rimar amb una forma verbal composta. Amb un dataset separat, aquestes llistes queden intactes.

### 4.2 Estructura de caselles recomanada

```
☐ Verbs + pronoms          ← nova secció, al costat de "Verbs"
   ☐ Infinitiu             (cantar-ho, anar-hi)
   ☐ Gerundi               (cantant-ho, anant-hi)
   ☐ Imperatiu             (canta-ho, ves-hi)
```

Dos nivells, exactament el patró de les altres sis seccions. **Recomano NO afegir un tercer nivell per tipus de pronom**, tot i que la sobrecàrrega de resultats el faria temptador:

- El contenidor de caselles és un patró rígid de 2 nivells a `js/components.js` i a `obtenirValorsSegonsPrimerCaracter()`; un tercer nivell obliga a reescriure `toggleList`, `handleCheckboxClick` i el mapatge d'índexs de `mostrarLlista`.
- 13 pronoms són massa caselles; agrupar-los en famílies (acusatiu / datiu / reflexiu / adverbials) obliga l'usuari a saber gramàtica per filtrar rimes.
- Si el volum molesta a la pràctica, la solució natural **no és un tercer nivell de caselles sinó un desplegable més** a `dropdown-container` ("Pronom: Indiferent / hi / ho / en / …"), consistent amb "Comença per" i "Incloure plurals".

⚠️ **Decisió pendent D4:** ho deixem en dos nivells per a la v1 i ja mirarem l'ús real, o vols el desplegable de pronom des del principi?

### 4.3 Càrrega sota demanda

El dataset nou es carrega **la primera vegada que l'usuari marca la casella**, amb el seu propi número de versió a `versions.json` i el seu propi registre a IndexedDB. Qui no la marqui mai no en descarrega ni un byte.

---

## 5. Fase 4 — Esquema de codificació

**Sí, cal un codi**, i ha de complir tres coses: no col·lisionar amb els codis EAGLES actuals, funcionar amb el `startsWith()` que ja fa servir tota la UI, i permetre recuperar de quin verb i de quina combinació surt cada entrada.

Comprovat: les primeres lletres ocupades són només `A`, `D`, `N`, `P`, `V`, `Z`. **`W` és lliure.**

### Format (implementat des dels infinitius)

```
W · <forma> · <persona> · _ · <npron> · <pronom1> [pronom2]

    forma    N infinitiu · G gerundi · M imperatiu
    persona  00  (infinitiu i gerundi)
             02S 01P 02P 03S 03P  (imperatiu)
    npron    1 o 2 — nombre de pronoms combinats, com a xifra explícita
    pronomN  codi de 2 lletres, en l'ordre gramatical (CI abans que CD…)
```

`npron` és tècnicament redundant (el nombre de pronoms ja es dedueix de la llargada del que ve després), però es guarda **explícit i a posició fixa** perquè un filtre futur de "combinacions dobles" el pugui mirar directament sense haver d'enumerar totes les parelles de pronoms possibles.

Codi de 2 lletres per pronom (els 14 de `pronoms/pronoms.json`; avui només es generen `HI` i `EN`, la resta queden reservats):

| em | et | es | ens | us | el | la | els (ac.) | les | li | els (dat.) | en | ho | hi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `EM` | `ET` | `ES` | `NS` | `US` | `EL` | `LA` | `EA` | `LE` | `LI` | `ED` | `EN` | `HO` | `HI` |

| Forma | Codi | `col_1` |
|---|---|---|
| `anar-hi` | `WN00_1HI` | `anar` |
| `anar-ne` | `WN00_1EN` | `anar` |
| `anant-hi` *(pendent)* | `WG00_1HI` | `anar` |
| `ves-hi` *(pendent)* | `WM02S_1HI` | `anar` |
| `penedeix-te` *(pendent)* | `WM02S_1ET` | `penedir` |
| `porta-l'hi` *(doble pronom, fase 2, pendent)* | `WM02S_2LIEL` | `portar` |

Per què aquest ordre i no un altre:

- `startsWith('W')` → tota la secció; `startsWith('WN')` → infinitius; `startsWith('WM')` → imperatius; `startsWith('WM02S')` → imperatius de "tu". Les tres caselles de §4.2 surten gratis amb el `crearCriteris` que ja existeix.
- El pronom va **al final** perquè el nivell 1 i 2 de la UI són forma i persona. Un filtre per pronom necessitaria un `crearCriterisSufix` nou — 3 línies, i només si es decideix D4.
- `col_1` guarda el **lema del verb base**, igual que la resta d'entrades verbals. Així la UI ja pot mostrar `anar-hi (anar)` i els enllaços a Viccionari/DIEC continuen apuntant al verb.

### Retocs mínims a `js/script.js` que això implica

| Funció | Canvi |
|---|---|
| `actualitzarRimes()` | `parts[2][0] === "V"` → `"V" \|\| "W"`, perquè surti el lema entre parèntesis |
| `descriureCategoria()` | afegir `if (codi.startsWith("W")) return "verb amb pronom"` |
| `obtenirPesJerarquia()` | afegir `W` (proposo pes 5, com els verbs) |
| `obtenirValorsSegonsPrimerCaracter()` | un `case "W"` nou amb els 3 índexs |
| `CriterisVerbsPronoms` | objecte nou, 4 entrades |

Els filtres existents de plurals i noms propis miren `array2[i][0] === "N"/"A"/"D"/"P"`, o sigui que **ignoren `W` automàticament**. No cal tocar-los.

---

## 6. Fase 5 — Càlcul de la rima

### 6.1 Les dues alternatives

**(b) Heretar la rima del verb base i ajustar-la per la terminació del pronom.**
Sembla la barata, però **falla precisament al cas que motiva el projecte**:

```
anar → col_3 = "a"        (la -r és muda: /ənˈa/)
"a" + "i"  =  "ai"        ✗
anar-hi                =  "aɾi"   ✓
```

La `-r` **reapareix** davant d'enclític vocàlic i no és a la rima heretada. El mateix passa amb la sonorització (`digues` → `iɣəs`, però `digues-ho` → `iɣəzu`) i amb l'espirantització. L'opció (b) donaria rimes falses en desenes de milers d'entrades, i falses **de manera invisible**: la paraula sortiria a la llista equivocada sense cap error.

**(a) Calcular la transcripció real de la forma verb+pronom i derivar-ne la rima amb el mateix codi de `creador_rima`.** ✅ **Recomanada.**

Important: (a) **no** vol dir escriure un transcriptor de català des de zero. Vol dir:

```
transcripció(verb+pronom) = col_9(forma base) + sàndhi + transcripció de l'enclític
```

La transcripció de la base ja la tenim feta i validada; l'enclític és una taula de 13 entrades; el sàndhi són 5 regles. A partir d'aquí, la rima surt del codi que ja existeix, sense duplicar lògica:

```python
cons = transcripcio.split("ˈ")[-1]
ass  = "".join(c for c in cons if c in "ɔəaeiou@Eɛ")
```

### 6.2 Les 5 regles de sàndhi

Totes tenen precedent al diccionari actual (§1.6):

1. **`-r` d'infinitiu** — muda quan el verb va sol (`cantar` /kəntˈa/), **sona sempre que hi ha enclític** (decisió D5, resolta). Quina ròtica depèn de la posició:
   · entre vocals, bategant `[ɾ]`: `anar-hi` /ənˈaɾi/, `fer-ho` /ˈfɛɾu/ — *precedent: `agar-agar` → `əɣˈaɾəɣˈar`*;
   · en coda, davant consonant `[r]`: `cantar-ne` /kəntˈarnə/, `dur-la` /ˈdurlə/ — *precedent: `abaderna` → `əβəðˈɛrnə`*.
   Els infinitius en `-re` no hi entren: no acaben en `-r` i ja duen la ròtica a dins (`veure'n` → `bˈɛwɾən`).
2. **Sonorització de `-s` final** davant vocal o consonant sonora: `digues-ho` → `dˈiɣəzu`, `digues-ne` → `dˈiɣəznə`. *Precedent: `despús-ahir` → `dəspˈuzəˈi`.*
3. **Espirantització de `v-`** de `-vos` darrere vocal: `[b]` → `[β]`. *Precedent: `vis-a-vis` → `bˈizəβˈis`.*
4. **Semivocalització de `-ho`/`-hi`** darrere vocal: `canta-ho` → `[ˈkantəw]`, `canta-hi` → `[ˈkantəj]`. *Precedent: `taula` → `tˈawlə`, `remei` → `rəmˈɛj`.*
5. **Un sol accent primari**, sobre el verb. Imprescindible perquè `split("ˈ")[-1]` doni la rima del grup sencer i no la de l'enclític.

Transcripció de cada enclític (reducció vocàlica del català central, ja aplicada):

| | | | | | |
|---|---|---|---|---|---|
| `-me` `mə` | `-te` `tə` | `-se` `sə` | `-nos` `nus` | `-vos` `bus`/`βus` | `-lo` `lu` |
| `-la` `lə` | `-los` `lus` | `-les` `ləs` | `-li` `li` | `-ne` `nə` | `-us` `us` |
| `-ho` `u`/`w` | `-hi` `i`/`j` | `'m` `m` | `'t` `t` | `'s` `s` | `'l` `l` |
| `'ns` `ns` | `'ls` `ls` | `'n` `n` | | | |

### 6.3 Síl·labes (`col_5`)

Regla tancada i exacta, sense necessitat de sil·labejador:

```
síl·labes(verb+pronom) = col_5(forma base) + (1 si l'enclític va amb guionet, 0 si va amb apòstrof)
```

`cantar-ho` = 2+1 = 3 · `canta'm` = 2+0 = 2 · `anar-hi` = 2+1 = 3.
*Precedent: `abans-d'ahir` = 4 síl·labes, l'apòstrof no en suma.*

### 6.4 Ambigüitats que NO resolc

✅ **D5 — La `-r` davant enclític consonàntic: RESOLTA (agost del 2026).** Es pronuncia. La font normativa deia el contrari (`dur-la` = /ˈdulə/), però s'ha decidit seguir la parla real.

El cost és alt i convé tenir-lo present, perquè les formes en `-ne` queden gairebé aïllades:

| Infinitius en | Verbs | Rimes si la `r` fos muda | Rimes amb la `r` sonora |
|---|---|---|---|
| `-ar` | 7.668 | /anə/ → 1.448 (1.290 comunes) | /arnə/ → **26** (14 comunes) |
| `-ir` | 883 | /inə/ → 2.493 (2.337 comunes) | /irnə/ → **3, totes noms propis** |
| `-er` tònic | 29 | /enə/ → 9 | /ernə/ → **0** |
| `-er` àton | 81 | /ənə/ → 0 | /ərnə/ → 0 |
| `-ur` | 2 | /unə/ → 101 | /urnə/ → 19 |

Amb el filtre de noms propis en "No" (el valor per defecte), `sortir-ne` no ensenyarà **cap** rima. En canvi `hi` no en queda afectat (la `r` ja hi sonava): manté el 96,2 % de cobertura. L'asimetria reforça la lectura de §3.1: el valor d'aquesta funció és sobretot a `hi`.

⚠️ **D6 — `-ho` i `-hi` darrere vocal: `[u]/[i]` o `[w]/[j]`?** No és cosmètic: `col_4` descarta `j` i `w`, o sigui que la **rima assonant canvia**. `veure-ho` amb `w` → assonant `ɛə`; amb `u` → assonant `ɛəu`. Recomano `[w]`/`[j]` (és el que fa el diccionari amb els diftongs), però és una decisió teva.

⚠️ **D7 — Vocal + vocal idèntica.** `vagi-hi`: /ˈbaʒi/ (fusió) o /ˈbaʒii/ (hiat)? El diccionari no té cap precedent. Afecta tots els imperatius de vostè en `-i` amb `hi`.

⚠️ **D8 — Coherència amb el sàndhi existent.** El diccionari actual és **inconsistent**: `despús-ahir` sonoritza (`dəspˈuzəˈi`) però `abans-d'ahir` no (`əβˈansdəˈi`). Nosaltres aplicarem la regla sempre. Això vol dir que les formes noves seran més consistents que les velles, no menys — però convé saber-ho.

---

## 7. Exemples de validació

Calculats amb el mètode de §6 i **contrastats contra `col_3` real** del diccionari:

| Forma | Codi `W` | AFI | Rima cons. | Rima ass. | Síl. | Rimes al diccionari actual |
|---|---|---|---|---|---|---|
| **`anar-hi`** ✅ generat | `WN00_1HI` | `ənˈaɾi` | `aɾi` | `ai` | 3 | **755** — *escenari*, abecedari, acapari… ✅ |
| `anar-ne` ✅ generat | `WN00_1EN` | `ənˈarnə` | `arnə` | `aə` | 3 | 26 — arna, sarna, encarna |
| `cantar-ho` *(pendent, no és `hi`/`en`)* | `WN00_1HO` | `kəntˈaɾu` | `aɾu` | `au` | 3 | 51 — acaparo, amaro, aclaparo |
| `cantar-me` *(pendent)* | `WN00_1EM` | `kəntˈarmə` | `armə` | `aə` | 3 | 22 — alarma, arma *(la `-r` sona, §D5)* |
| `anant-hi` *(pendent, gerundi)* | `WG00_1HI` | `ənˈanti` | `anti` | `ai` | 3 | 84 — aguanti, abrillanti |
| **`ves-hi`** *(pendent, imperatiu tu)* | `WM02S_1HI` | `bˈezi` | `ezi` | `ei` | 2 | 6 — desi, pesi *(sonorització, §6.2-2)* |
| `aneu-hi` *(pendent, imperatiu vosaltres)* | `WM02P_1HI` | `ənˈɛwi` | `ɛwi` | `ɛi` | 3 | 18 — creui, apreui |
| `penedeix-te` *(pendent, pronominal)* | `WM02S_1ET` | `pənəðˈɛʃtə` | `ɛʃtə` | `ɛə` | 4 | 0 — només rimaria amb formes germanes |
| `digues-ho` *(pendent)* | `WM02S_1HO` | `dˈiɣəzu` | `iɣəzu` | `iəu` | 3 | 0 |
| `emporta-te'n` *(pendent, doble pronom, fase 2)* | `WN00_2ETEN` | `əmpˈɔrtətən` | `ɔrtətən` | `ɔəə` | 4 | 0 |
| `porta-l'hi` *(pendent, doble pronom, fase 2)* | `WM02S_2LIEL` | `pˈɔrtəli` | `ɔrtəli` | `ɔəi` | 3 | 0 |

El cas d'origen queda validat: **`anar-hi` i `escenari` comparteixen `col_3 = aɾi` i `col_4 = ai`**, i cauen en grups de síl·labes diferents (3 i 4), que és exactament com el rimador ja presenta els resultats.

Les dues últimes files reforcen la recomanació de §2.4: les formes de doble pronom no rimen amb res del diccionari existent.

---

## 8. Què queda pendent de confirmar abans d'implementar

| | Decisió | Recomanació meva |
|---|---|---|
| **D1** | Incloem els imperatius de vostè/vostès (`vagi-hi`), homògrafs del subjuntiu? 17.566 formes base | Sí, però al final |
| **D2** | `ho` obert a tots els transitius (sobregenera) o llista curada? | Obert, i revisar-ho amb resultats reals |
| **D3** | `li`/`els` datiu: obert a tots, limitat a transitius, o camp nou? | **Obert a tots** (com el datiu ètic) |
| **D4** | Filtre per tipus de pronom a la v1? | **No**; si cal, desplegable, no tercer nivell de caselles |
| ~~**D5**~~ | ~~La `-r` d'infinitiu davant enclític consonàntic és muda?~~ | ✅ **Resolta: sona.** Implementat |
| **D6** | `-ho`/`-hi` darrere vocal: `[w]`/`[j]` o `[u]`/`[i]`? | `[w]`/`[j]` |
| **D7** | `vagi-hi`: fusió o hiat? | Sense precedent — decideix tu |
| **D9** | Abast de la v1: només infinitius (115.882 formes, 96 % de cobertura de rima) o tot (804.258, 43 %)? | **Infinitius + gerundis primer**; imperatius en una segona tongada |
| **D10** | Fem la fase 1.5 (pronominals inherents + segon pronom: `anar-se'n`, `emportar-se'l`)? | Sí, val molt la pena |

Cap d'aquestes decisions bloqueja les altres: el generador es pot escriure amb totes elles com a paràmetres de configuració.

---

## 9. Fonts

- [GEIEC 13.4.2 — La forma dels pronoms febles](https://geiec.iec.cat/text/13.4.2) i [13.5.1 — L'ordre dels pronoms](https://geiec.iec.cat/text/13.5.1) (IEC)
- [GIEC 8.3 — La forma i la posició dels pronoms febles respecte al verb](https://giec.iec.cat/textgramatica/codi/8.3.1d) (IEC)
- [Gramàtica bàsica i d'ús 16.2 i 16.4 — Combinacions de pronoms febles](https://gbu.iec.cat/text/16.4) (IEC)
- [CPNL — 37. Els pronoms febles](https://www.cpnl.cat/gramatica/66/37-els-pronoms-febles) i [38. La combinació de pronoms](https://www.cpnl.cat/gramatica/59/38-la-combinacio-de-pronoms) — quadre d'enclisi confirmat
- [CNL de Girona — Les combinacions binàries de pronoms febles (PDF)](https://blogs.cpnl.cat/nivelldcalonge/files/2012/03/Combinacions-bin%C3%A0ries-de-pronoms-febles.pdf) — ordre de col·locació, `li` → `hi`, excepció `el`+`en` = `l'en`
- [Viquipèdia — Ortologia del català](https://ca.wikipedia.org/wiki/Ortologia_del_catal%C3%A0): «muda, final dels infinitius seguits d'un pronom feble amb cons. (*dur-la*, *estimar-nos*)» / «[ɾ] final dels infinitius seguits d'un pronom feble amb vocal (*anar-hi*, *fer-ho*)»
- [Viquipèdia — Pronom feble](https://ca.wikipedia.org/wiki/Pronom_feble): «El conjunt format pel verb i el pronom o pronoms febles que el segueixen es pronuncia amb un únic accent tònic (el del verb)»
- [Gramàtica normativa valenciana (AVL) — 22. Els pronoms febles: aspectes formals (PDF)](https://lletradebatalla.wordpress.com/wp-content/uploads/2012/10/pronoms-febles-gramc3a0tica-normativa-avl.pdf)
