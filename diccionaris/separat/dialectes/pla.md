# Pla: dialectes al Rimador.cat

> Document de disseny. **No s'ha escrit cap generador ni s'ha tocat res de producció.**
> Totes les xifres surten de mesures reals sobre `diccionaris/separat/col_*.txt` i sobre
> els quatre fitxers de `separat/dialectes/terminal_aina/` (agost del 2026, diccionari
> 5.2.3, 619.783 files).

---

## 0. Resum executiu

| | Decisió recomanada |
|---|---|
| **Què és un dialecte, en dades** | **Una sola columna nova: la `col_3` (rima consonant).** La `col_4` es dedueix de la `col_3` dins el navegador (comprovat: 0 excepcions en 619.783 files). Tot el que hi ha a la resta de columnes és el mateix per a tots els dialectes. |
| **Quant costa** | **~370 KB comprimits per dialecte**, baixats només si algú tria aquell dialecte i desats a IndexedDB com tota la resta. Cap cost per a qui es queda al central. |
| **Font de les transcripcions** | Un **lèxic per parell `(paraula, transcripció central)`**, editable a mà i partit en trossos com la `col_10`. L'espeak-ng no corre mai als workflows: només en local, i només per a les paraules que falten. |
| **Correccions** | El mateix lèxic és el lloc on es corregeixen. Quan es corregeix una transcripció central, el parell canvia i el dialecte queda marcat "a revisar" tot sol. |
| **Selecció al web** | Un `<select>` nou, el primer de tots, a `dropdown-container`. Preferència recordada al `localStorage`. Commutació **sense recarregar** la pàgina. |
| **Enllaç** | Pàgina pròpia per dialecte: `rimador.cat/valencia/`, `/balear/`, `/nord-occidental/`. Es generen al desplegament a partir de l'`index.html` (una sola font). El paràmetre `?d=va` també val, per als enllaços compartits. |
| **Gestors `.yml`** | Un pas nou dins l'acció composta `publicar-diccionari`, després de les columnes internades i abans del `versions.json`. **Cap workflow nou.** |
| **Estadístiques** | Un camp `dialecte` a `registrarCerca`, una columna nova al full, `fillna('central')` a l'històric i un bloc nou a `dades.html`. La "Rima" registrada deixa de tenir sentit sense el dialecte al costat: cal agrupar-hi. |
| **Llistes derivades** | Nàufragues i mots de 7 **són diferents a cada dialecte** (4.049 nàufragues al central, 4.686 en valencià). Fase a part, després que el cercador funcioni. |
| **Etiqueta** | Els dialectes surten **en proves**. El central porta 604 files corregides a mà; els dialectes no en porten cap. |

---

## 1. Què hi ha ara

### 1.1 Els quatre fitxers que ja tens

`separat/dialectes/terminal_aina/`, fets amb `processar_veus.sh` (espeak-ng compilat, veus `ca`, `ca-va`, `ca-nw`, `ca-ba`), una línia per fila de la `col_0`:

| fitxer | files | mida |
|---|---:|---:|
| `col_0_transcripcio_ca.txt` | 619.783 | 9,8 MB |
| `col_0_transcripcio_ca_va.txt` | 619.783 | 8,7 MB |
| `col_0_transcripcio_ca_nw.txt` | 619.783 | 8,7 MB |
| `col_0_transcripcio_ca_ba.txt` | 619.783 | 9,8 MB |

I `diferencies.txt`, el `diff` entre la `col_9` de debò i l'espeak `ca`.

### 1.2 Tres fets del format que fan que això surti barat

Mesurats sobre les columnes publicades d'ara mateix:

1. **`col_3` = la cua de la `col_9` després de l'últim `ˈ`** — 0 files on no quadri.
2. **`col_4` = les vocals de la `col_3`** (`ɔəaeiou@Eɛˈ`) — 0 files on no quadri, i les 10.055 rimes consonants només donen 135 assonants.
3. **Cap altra columna depèn de la pronúncia.** La `col_5` (síl·labes) és un recompte **ortogràfic** heretat de la font, i la paraula, el lema, el codi i els tres enllaços són els mateixos es pronunciï com es pronunciï.

Conseqüència: **un dialecte és una `col_3` i prou.** No cal duplicar cap altra columna, ni publicar cap transcripció sencera, ni tocar el diccionari base.

### 1.3 Quatre trampes del codi d'ara que s'han de tenir presents

| # | Trampa | On |
|---|---|---|
| 1 | **La clau de la memòria cau és el NOM del fitxer, no el camí**: `rutaFitxer.split("/").pop()`. Dos `col_3.idx.txt` en carpetes diferents es trepitjarien a IndexedDB i al `versions.json`. **Els fitxers de dialecte han de dur el codi al nom**: `col_3.va.idx.txt`. | `js/script.js:365` (`llegirFitxerAmbIndexedDB`) i `generar_versions.py` |
| 2 | `nombresDeFitxers = 17` és a mà. Amb dialecte actiu en són 19. | `js/script.js:196` |
| 3 | **`deploy.yml` no poda `separat/dialectes/`**: els 35 MB de transcripcions crues que hi ha ara ja s'estan pujant a Pages a cada desplegament. Cal treure'ls (com la `col_9`). | `.github/workflows/deploy.yml`, pas "Aprimar el paquet" |
| 4 | Els fitxers de l'espeak **acaben amb salt de línia** i les `col_*.txt` **no** (el navegador fa `split('\n')` sense filtrar: un salt final li afegeix una fila fantasma). El generador l'ha de treure. | `generar_columnes_publicades.py`, docstring de `partir()` |

---

## 2. Què és un dialecte, en dades

### 2.1 Què es publica per dialecte

Només la `col_3`, internada com totes les altres (taula de valors + un número per fila):

| dialecte | rimes consonants | taula | índex | **comprimit (Pages)** |
|---|---:|---:|---:|---:|
| central (avui) | 10.055 | 71 KB | 2,00 MB | 367 KB |
| valencià (`va`) | 10.811 | 72 KB | 2,03 MB | **370 KB** |
| nord-occidental (`nw`) | 10.666 | 71 KB | 2,00 MB | **368 KB** |
| balear (`ba`) | 10.086 | 72 KB | 2,00 MB | **367 KB** |

La `col_4` **no es publica**: el navegador la fabrica passant el filtre de vocals a les ~10.000 entrades de la taula (un bucle de mil·lisegons), i amb això té la taula assonant i el número de cada fila. Val la pena recordar que això mateix es podria fer amb el central i estalviar-se la `col_4` d'ara (uns 200 KB comprimits a cada visita), però és un canvi a part i no cal barrejar-lo amb això.

### 2.2 Com de diferents són, de debò

Files que canvien de rima respecte del central:

| dialecte | rima consonant | rima assonant | rimes assonants diferents | nàufragues |
|---|---:|---:|---:|---:|
| central | — | — | 135 | 4.049 |
| valencià | 409.409 (66,1 %) | 365.024 (58,9 %) | 191 | 4.686 |
| nord-occidental | 365.625 (59,0 %) | 363.947 (58,7 %) | 209 | 4.527 |
| balear | 120.949 (19,5 %) | 40.917 (6,6 %) | 171 | 4.159 |

Dues conseqüències: (a) no és cap detall cosmètic, dos de cada tres paraules rimen amb una altra gent en valencià; (b) **cada dialecte té la seva llista de nàufragues** i les d'ara només valen per al central.

### 2.3 Alternativa descartada (amb números)

*"En comptes d'una columna sencera, publiquem una taula petita que digui, per a cada una de les 10.055 rimes centrals, quina és la rima valenciana."*

Seria un fitxer de 10.000 línies en comptes de 2 MB. **No funciona:** la rima dialectal no és funció de la rima central. En valencià, **1.368 dels 10.055 grups de rima central es parteixen** (428.712 files afectades) i 840 rimes valencianes n'ajunten dues o més de centrals. Cal la fila. Descartat.

---

## 3. D'on surten les transcripcions i com es mantenen

### 3.1 El problema de fons

Els quatre fitxers d'ara són **una foto d'un `col_0` concret**. Van per número de fila i no porten cap paraula a dins. El dia que el diccionari guanyi o perdi una entrada, totes les files de sota es desplacen i cada paraula hereta la pronúncia d'una altra, **sense que res se'n queixi**: és exactament la trampa que el `creador_rima` ja vigila amb els camps 5 a 8.

I no es poden regenerar dins el workflow: l'espeak-ng que els va fer és una compilació teva (`src/espeak-ng`), i el de l'`apt` d'Ubuntu no té per què donar el mateix.

### 3.2 Tres maneres de resoldre-ho

| | Com | A favor | En contra |
|---|---|---|---|
| **A** | Deixar-ho per fila, com ara, i comprovar amb un resum que el `col_0` no ha canviat | 8,7 MB per dialecte, res a fer | Qualsevol alta al diccionari obliga a **refer els quatre fitxers sencers** en local. Bloqueja el flux de la `col_10` |
| **B** ✅ | **Un lèxic per parell `(paraula, transcripció central)` → transcripció dialectal** | Sobreviu a qualsevol reordenació. Les paraules que falten es poden llistar exactament. Es pot editar i fer `grep`. Resol els homògrafs sol (vegeu §3.5) | 44,3 MB al repositori per als tres dialectes (no es publica mai) |
| **C** | Tres camps més dins `diccionari.5.2.3.txt` (13 camps) | Alineació garantida per construcció, s'edita al mateix lloc que la resta | El diccionari base passa de 41,9 a **~67 MB**: GitHub avisa a partir de 50 i bloqueja a 100. I amb el v.6 (4 milions de files) es multiplica |

**Recomanació: B.** Format d'una línia, amb el mateix separador de la `col_10`:

```
paraula € transcripció central € valencià € nord-occidental € balear
```

```
'Ndrangheta € ndɾəŋɡˈɛtə € ndɾaŋɡˈeta € ndɾaŋɡˈetɛ € ndɾəŋɡˈətə
a € ˈa € ˈa € ˈa € ˈə
```

**529.293 línies** (90.490 files del diccionari són parells repetits i no hi surten dues vegades), 44,3 MB. Partit en 500 trossos com la `col_10 (canvis aquí)`, són 91 KB per fitxer: editable, i cap fitxer s'acosta al límit de GitHub.

### 3.3 Per què la clau és el parell i no la paraula

Perquè **el central ja distingeix els homògrafs i l'espeak no**. Al diccionari hi ha **91 grafies amb més d'una transcripció** (245 files): `be` /bˈɛ/ i /bˈe/, `cos`, `cop`, `com`, `coc`… Totes 91 fan sortir avui el diàleg d'homògrafs.

Els fitxers de l'espeak donen **una sola transcripció per grafia**: en valencià només en sobreviuen 3, i encara són artefactes de majúscules (`TikTok`/`tiktok`, `WhatsApp`/`whatsapp`, `Rodamots`). O sigui que, tal com estan, **en dialecte es perdrien les 91 distincions**: `cop` i `cos` rimarien amb el que no toca i el diàleg no sortiria mai.

Amb la clau `(paraula, transcripció central)`, cada variant del central té la seva línia al lèxic i la seva transcripció dialectal. Són **245 files a omplir a mà una vegada**, i queda arreglat per sempre.

### 3.4 El cicle de manteniment

```
   edició del diccionari (per la porta que sigui)
                    │
                    ▼
   generar_dialectes.py  ── llegeix col_0 + col_9 + el lèxic
                    │
      ┌─────────────┴─────────────┐
      │                           │
  tots els parells           en falta algun
  hi són                          │
      │                           ▼
      ▼                  ┌────────────────────────────────┐
  escriu les col_3       │ paraula NOVA        → ATURADA   │
  de cada dialecte       │ transcripció central CANVIADA:  │
  + internades           │   hereta la del mateix mot,     │
  + versions.json        │   ho apunta a "a_revisar.txt"   │
                         │   i CONTINUA                    │
                         └────────────────────────────────┘
                                        │
                                        ▼
                         en local: espeak_paraules.py transcriu
                         només aquelles i les afegeix al lèxic
```

La distinció entre les dues és important i és la que fa que això sigui usable:

* **Paraula que no és al lèxic → el workflow peta.** No hi ha manera d'endevinar-ne la pronúncia i publicar-la sense seria servir una rima inventada.
* **Paraula que hi és però amb una altra transcripció central** (o sigui: has corregit el central) → **no peta**. Es queda la transcripció dialectal que hi havia, i la fila surt a `a_revisar.txt`. Si no fos així, corregir cinquanta transcripcions centrals de cop et deixaria el web aturat fins a repassar-ne cent cinquanta de dialectals.

Aquest segon cas és, de fet, **el mecanisme de propagació de correccions**: no cal recordar res, el sistema et diu quines files dialectals han quedat sospitoses.

### 3.5 Què sabem que està malament ara mateix

| Cosa | Files | Detall |
|---|---:|---|
| El central corregit a mà respecte de l'espeak `ca` | **604** | `Abelard` /əβəlˈar**t**/ contra /əβəlˈar/, `absolt`, `acuita`, `agnusdei`… Són la llista exacta del que ja has corregit una vegada i que **als altres tres dialectes continua sense corregir** |
| Transcripcions **sense cap `ˈ`** | **11** | `bull` (×6), `Bush`, `Cook`, `Iu`, `Ius`, `Wood`. Sense accent, la rima consonant és la paraula sencera i **l'assonant queda buida**: les onze rimarien assonantment entre elles |
| L'espeak lletreja | **1** | `anc` → `ˌaˈenəcˌe` ("a-ena-ce"). És l'única `c` de tot el fitxer |
| Homògrafs perduts | **245** | §3.3 |

Pressupost de revisió inicial: **~860 files per dialecte**, la majoria mecàniques (les 604 són sobretot la `-t` i la `-r` finals, i es poden portar de la `diferencies.txt` amb un script d'ajuda).

### 3.6 Validacions que han de fer petar la generació

Al `generar_dialectes.py`, en el mateix esperit del `generar_versions.py` ("val més que peti aquí que no pas servir un 404 silenciós"):

1. Tantes files com la `col_0`, i **sense salt de línia final**.
2. Cap transcripció sense `ˈ`.
3. Cap rima assonant buida.
4. Cap caràcter fora de l'inventari AFI conegut (`abdefijklmnoprstuvwzðŋɔəɛɡɣɱɲɾʃʎʒˈˌβθχ` i l'espai). Això sol enxampa l'`anc`.
5. Cap vocal de l'inventari que no sigui a la llista del filtre assonant (si un dia una veu treu una vocal nova, la rima assonant l'ignoraria en silenci).
6. Menys de 65.536 rimes diferents (per sobre, el navegador puja sol a `Uint32Array`, però val la pena saber-ho).

---

## 4. Fitxers i noms

```
dialectes/                                  ← es mou aquí, FORA de separat/
  README.md
  docs/pla.md                               ← aquest document
  python/
    config_dialectes.py                     ← l'interruptor: la llista de dialectes
    generar_dialectes.py                    ← lèxic + col_0 + col_9 → columnes
    espeak_paraules.py                      ← EINA LOCAL: transcriu el que falta
  lexic (canvis aquí)/
    lexic_000.txt … lexic_499.txt           ← 91 KB cadascun
  a_revisar.txt                             ← el que ha quedat sospitós
  crus/                                     ← la sortida de l'espeak tal com surt
    processar_veus.sh  ca.txt  ca_va.txt  ca_nw.txt  ca_ba.txt

diccionaris/separat/dialectes/              ← NOMÉS el que es publica
  va/col_3.va.taula.txt   va/col_3.va.idx.txt
  nw/col_3.nw.taula.txt   nw/col_3.nw.idx.txt
  ba/col_3.ba.taula.txt   ba/col_3.ba.idx.txt
```

**Per què `dialectes/` surt de `separat/`:** `separat/` és el que es baixa el navegador. Les transcripcions crues i el lèxic no s'hi han d'acostar mai (§1.3, trampa 3). Publicat només hi ha el que es baixa: sis fitxers, 1,1 MB comprimits en total.

**Per què el codi al nom del fitxer** (`col_3.va.idx.txt` i no `va/col_3.idx.txt`): la memòria cau del navegador i el `versions.json` s'indexen pel nom del fitxer sol (§1.3, trampa 1). Amb el codi al nom, no cal tocar res del `llegirFitxerAmbIndexedDB` ni pujar la versió d'IndexedDB, i per tant **cap visitant no es torna a baixar el diccionari**.

### 4.1 `config_dialectes.py`, l'interruptor

Un únic lloc que digui quins dialectes hi ha, igual que `config.py` diu quin diccionari es publica. D'aquí surt tot: quins fitxers genera el workflow, què surt al `versions.json`, quines opcions ensenya el `<select>` i quines pàgines es creen al desplegament.

| codi | nom al web | veu espeak | adreça |
|---|---|---|---|
| `ca` | Català central | `ca` | `/` (el que hi ha) |
| `nw` | Nord-occidental | `ca-nw` | `/nord-occidental/` |
| `va` | Valencià | `ca-va` | `/valencia/` |
| `ba` | Balear | `ca-ba` | `/balear/` |

L'alguerès i el rossellonès no els fa l'espeak: no hi són, i el dia que hi siguin s'afegeixen aquí.

### 4.2 `versions.json`

Les sis parelles noves entren al mateix bloc `columnes` (les claus són noms de fitxer i no xoquen), i s'hi afegeix un bloc germà que el web llegeix per muntar el desplegable:

```json
{
  "columnes": { "...": "...", "col_3.va.taula.txt": "…", "col_3.va.idx.txt": "…" },
  "dialectes": [
    { "codi": "va", "nom": "Valencià", "adreça": "valencia",
      "fitxers": ["col_3.va.taula.txt", "col_3.va.idx.txt"] }
  ]
}
```

Així la llista de dialectes del web surt de la mateixa generació que les dades: no pot passar que el desplegable ofereixi un dialecte que encara no s'ha publicat.

---

## 5. Els gestors `.yml`

### 5.1 Res de workflows nous

Les dues portes d'entrada al diccionari (editar `diccionari.5.2.3.txt` o editar la `col_10`) ja comparteixen el tram final a `.github/actions/publicar-diccionari/`. **Els dialectes són un pas més d'aquell tram**, i per tant entren pels dos camins alhora i van al mateix commit:

```
   pre_procés + creador_rima          separar_arxiu
   (canvis a la col_10)               (canvis al diccionari)
            └───────────┬───────────────────┘
                        ▼
            ┌───── publicar-diccionari ─────────────────┐
            │  1. (pronoms i v.6, si toca)              │
            │  2. generar_columnes_publicades           │
            │  3. generar_columnes_internades           │
            │  4. generar_dialectes.py        ← NOU     │
            │  5. generar_versions.py                   │
            │  6. comitejar diccionaris/ + dialectes/   │
            └───────────────────────────────────────────┘
                        ▼
                 generar_llistes  →  deploy
```

**Per què el pas 4 va entre el 3 i el 5, i no en un altre lloc:**

* Després del 2, perquè necessita la `col_0` i la `col_9` **del diccionari publicat**, no del que hi havia.
* Abans del 5, perquè el `generar_versions.py` és qui comprova que tot quadra i qui escriu els resums: si els dialectes es fessin després, es publicarien sense versió i el navegador no els podria desar a la memòria cau.

### 5.2 Canvis, fitxer per fitxer

| Fitxer | Canvi |
|---|---|
| `.github/actions/publicar-diccionari/action.yml` | Un pas: `python dialectes/python/generar_dialectes.py`. **Sense `if`**: corre sempre, com el `generar_columnes_publicades`, i així les columnes dialectals són sempre les del diccionari publicat |
| `.github/actions/comitejar` (crida des de `publicar-diccionari`) | El `fitxers:` passa de `diccionaris` a `diccionaris dialectes` (l'`a_revisar.txt` també s'ha de comitejar: és el que et diu què has de mirar) |
| `diccionaris/python/generar_versions.py` | Afegir-hi les columnes dialectals i el bloc `dialectes`. La comprovació de files ha de valdre també per a elles |
| `.github/workflows/deploy.yml` | `paths-ignore`: afegir-hi `dialectes/**` (com `pronoms/**`): tocar el lèxic dispara el workflow del diccionari, que ja encadena el desplegament. **Pas "Aprimar el paquet"**: `rm -rf dialectes` i, si encara hi és, `separat/dialectes/*/crus`. **Xarxa de seguretat**: afegir-hi un `col_3.*.idx.txt` a la llista del `for cal in …` |
| `.github/workflows/generar_llistes.yml` | Res, de moment (fase 5) |

### 5.3 Quan falta una transcripció

El pas 4 acaba amb codi 1 i un missatge del mateix estil que els altres:

```
ERROR: 3 paraules noves sense transcripció dialectal.
       Passa dialectes/python/espeak_paraules.py en local i afegeix el
       resultat al lèxic. Les paraules són a dialectes/falten.txt:
         escafandrisme, retroil·luminar, tiktokera
```

El diccionari **no es publica a mitges**: el `git add` no arriba a passar i les columnes velles es queden servint-se fins que el lèxic estigui complet. És el mateix criteri que ja té el `creador_rima` amb les mides que no quadren.

---

## 6. El web

### 6.1 Com es tria el dialecte

Un `<select>` nou, **el primer de `dropdown-container`** (`js/components.js`), abans del tipus de rima: és el que decideix què vol dir tota la resta, i visualment ha de quedar separat dels filtres.

```html
<div class="triar-dialecte">
  <label for="dialecteSelector">Dialecte:</label>
  <select id="dialecteSelector">
    <option value="ca">Català central</option>
    <option value="nw">Nord-occidental</option>
    <option value="va">Valencià</option>
    <option value="ba">Balear</option>
  </select>
</div>
```

Les opcions es munten del bloc `dialectes` del `versions.json`, no escrites a mà: un dialecte que encara no s'hagi publicat no ha de sortir al desplegable.

**Ordre de prioritat en decidir quin dialecte s'ensenya:**

1. El de la pàgina, si n'hi ha (`/valencia/` → `va`).
2. El de l'adreça (`?d=va`).
3. El desat al `localStorage`.
4. Central.

**El punt 3 no fa saltar mai a una altra adreça.** Si algú entra a `rimador.cat/` amb el valencià desat, es queda a `rimador.cat/` amb el valencià posat i el desplegable ho diu. Redirigir seria un mal negoci: trenca els enllaços compartits, embolica els cercadors i fa que la pàgina que has enviat a algú no sigui la que veu.

### 6.2 Enllaços i cercadors

**Una pàgina per dialecte**, generades al desplegament a partir de l'`index.html` amb el mateix `sed` que ja ajusta el `404.html`:

| adreça | `<title>` | canonical |
|---|---|---|
| `/` | Rimador.cat | `https://rimador.cat/` |
| `/valencia/` | Rimador.cat — rimes en valencià | `https://rimador.cat/valencia/` |
| `/nord-occidental/` | Rimador.cat — rimes en nord-occidental | `https://rimador.cat/nord-occidental/` |
| `/balear/` | Rimador.cat — rimes en balear | `https://rimador.cat/balear/` |

Tres coses que això arregla de cop:

* **Es poden trobar.** "rimes en valencià" és una cerca que existeix i que avui no porta enlloc. El `sitemap.xml` les agafarà soles: es genera dels `canonical` de cada pàgina (ja és així al `deploy.yml`).
* **Es poden compartir.** El botó de piular pot enllaçar `rimador.cat/valencia/?q=taronja` en comptes d'un paràmetre que ningú no entén.
* **El `SearchAction` del JSON-LD continua sent veritat** a cada pàgina, amb la seva `urlTemplate`.

I no duplica cap manteniment: **una sola font, l'`index.html`**, com els HTML que ja es reescriuen al desplegament. El `?d=va` es continua entenent a totes les pàgines, per als enllaços que ja corrin pel món.

Al menú (`js/menu.js`), un grup nou "Dialectes" amb les tres adreces, al costat del de "Llistes".

### 6.3 Càrrega i commutació

```
DOMContentLoaded
  ├── carregarVersions()                 (ja hi és, ara també llegeix "dialectes")
  ├── col_0 + col_1..col_8               (ja hi és, sense canvis)
  ├── si el dialecte actiu ≠ central:
  │     col_3.<codi>.taula + .idx        (~370 KB, per la via de sempre)
  │     col_4 derivada de la taula       (bucle de 10.000 entrades)
  └── prepararColumnes()                 (índexs de rima del dialecte actiu)
```

En canviar de dialecte **no es recarrega la pàgina**: es baixa (o es llegeix d'IndexedDB) la columna, es refan els dos índexs de rima i es torna a fer la cerca que hi hagués a la pantalla. Amb la còpia desada són desenes de mil·lisegons; la primera vegada, el que trigui baixar 370 KB. Va sota el `Loader.mentre()`, que ja està fet per a això.

**Memòria:** es guarden les columnes de tots els dialectes que s'hagin visitat (1,2 MB cadascuna) però **els índexs de rima només del dialecte actiu** (uns 10 MB, `indexarPerRima` els refà en un moment). Guardar-los tots seria 40 MB per no res.

**Si la baixada falla:** es torna al central amb un avís visible. Ensenyar rimes centrals dient que són valencianes és pitjor que dir que no s'ha pogut.

### 6.4 El que surt bé tot sol

Tres coses que no s'han de tocar perquè ja miren la `col_3` i la `col_4`:

* **El diàleg d'homògrafs.** Compara números de rima (`js/script.js:1007`): amb la columna dialectal posada, pregunta exactament quan en aquell dialecte hi ha diferència. En valencià no preguntarà per `cop` si allà rima igual — que és el correcte.
* **Les nàufragues d'una cerca** (`calcularSiEsNaufraga`): surten de l'índex consonant, o sigui del dialecte actiu.
* **Els filtres, les caselles i la impressió**: no toquen la pronúncia.

El que **sí** que s'ha de tocar: el botó de compartir (que hi digui el dialecte i enllaci la pàgina bona) i `nombresDeFitxers`.

### 6.5 En proves

El central porta 604 files corregides a mà i els dialectes cap. Al llançament, els tres dialectes han de dur una etiqueta visible ("en proves") i un enllaç directe a `error.html`, amb un camp amagat que hi enviï el dialecte actiu: així els informes arriben ja classificats i la revisió de §3.5 la fa la gent que parla cada varietat, que és qui ho sap.

---

## 7. Llistes derivades (fase a part)

`llista_naufragues.html`, `llista_mots_de7.html` i `llista_heptasilabs.html` surten de la `col_3` i de la `col_9` **centrals**. Amb dialectes, cadascuna és una llista diferent: 4.049 nàufragues al central, 4.686 en valencià, 4.527 en nord-occidental, 4.159 en balear.

Mentre no es facin per dialecte, les pàgines han de dir **explícitament** que són del central (una línia sota el títol i prou). És més honest que ensenyar-les amb el desplegable de dialectes al costat com si canviessin.

Quan es facin: `paraules_naufragues.va.json` i companyia (noms de fitxer diferents → el `versions_llistes.json` i la memòria cau ja funcionen), el mateix `generar_naufragues.py` amb un argument, i el desplegable de dialectes també a les pàgines de llista. Els mots de 7 en glosa classifiquen agut/pla/esdrúixol amb la transcripció: allà caldrà la transcripció dialectal sencera, que el generador té a mà però que no es publica.

---

## 8. Estadístiques

### 8.1 La cadena sencera

```
registrarCerca()          →  Apps Script (doPost)  →  full de càlcul
js/script.js                 fora del repositori       una columna nova
      │                                                      │
      └──────────────────────────────────────────────────────┘
                                  ▼
                       stats/stats.py (cada nit)
                                  ▼
                    estadistiques_rimador.json  →  dades.html
```

### 8.2 Canvis, un per un

| On | Canvi | Compte amb |
|---|---|---|
| `js/script.js`, `registrarCerca()` | Un `dades.append('dialecte', dialecteActiu)` i un paràmetre més a la crida | Res |
| **Apps Script** | `appendRow` ha de posar el dialecte **a l'última posició**, la mateixa que la capçalera nova | **No és al repositori.** El del joc sí (`joc/eines/apps_script_classificacio.gs`): val la pena pujar-hi també el de les cerques, perquè ara mateix és codi que corre i que no es veu enlloc |
| **Full de càlcul** | Columna nova al final, "Dialecte" | Afegir-la **al final** i no al mig: si s'insereix entremig, totes les files velles queden desplaçades |
| `stats/stats.py` | `df['Dialecte'] = df['Dialecte'].fillna('ca')` just després de llegir el CSV | Les files d'abans del canvi no la porten. Sense el `fillna`, el `value_counts()` se les menja i els totals deixen de quadrar |
| `stats/stats.py` | La **rima** ha d'anar sempre amb el dialecte al costat | `'aɾa'` no vol dir res sense saber de quin dialecte és, i el top de rimes barrejaria coses que no són comparables. Les claus de `obtenir_top_paraules(…, 'rima')` passen a ser `['Rima', 'Tipus de rima', 'Dialecte']` |
| `stats/stats.py` | Les nàufragues es comproven contra la llista **del dialecte de la fila** | Mentre no hi hagi llistes per dialecte (§7), comptar-hi només les files del central |
| `stats/stats.py` | `recompte_dialecte` nou dins `sempre` | — |
| `js/script_dades.js` | Una entrada més a la llista de filtres (línia 7): `{ id: 'recompte_dialecte', titol: 'Dialecte' }`. El gràfic ja el munta sol | Si el JSON és vell i no porta la clau, que no peti |
| `dades.html` | Res, si va al bloc de filtres. Un `<h3>` propi si es vol destacar | — |

### 8.3 Què val la pena poder respondre

Amb el camp posat, aquestes surten soles i són les que decidiran si val la pena continuar:

* Quin percentatge de cerques es fa en cada dialecte (i si creix).
* Quanta gent **canvia** de dialecte: dispositius únics amb més d'un valor.
* Si en dialecte es troben menys paraules (proporció de `***` per dialecte): seria el senyal que les transcripcions dialectals tenen forats.
* Quines paraules es cerquen només en valencià i no al central: la llista de les que falten al diccionari.
* Els tops de rimes per dialecte, que són el material de les llistes i del joc.

---

## 9. Fora d'abast (i per què)

* **El joc** (`joc/`) es genera de la `col_3` central i té una classificació única. Fer-lo per dialecte vol dir dades ×4 i decidir si les puntuacions es barregen; no s'hi ha de tocar fins que el cercador funcioni.
* **El bot** (`bot/`) està aturat.
* **Les formes amb pronom** (v.6): la transcripció de `cantar-vos` es construeix amb regles de sàndhi damunt la del verb, i cada dialecte tindria les seves. La feina es multiplica per quatre i s'ha de fer després, no alhora. El disseny d'aquí ho aguanta: si el diccionari publicat és el v.6, el `generar_dialectes.py` demanarà els parells de les formes noves i el lèxic els haurà de tenir, generats per la mateixa via que els genera el central.

---

## 10. Fases

| Fase | Què | Es pot desplegar sol? |
|---|---|---|
| **0** | Moure `separat/dialectes/` a `dialectes/`, treure'l del paquet de Pages (§1.3), escriure el `README.md` | Sí, i **s'hauria de fer ja**: són 35 MB que ara mateix es pugen a cada desplegament |
| **1** | `config_dialectes.py`, el lèxic partit en trossos, `generar_dialectes.py` amb les validacions de §3.6, `espeak_paraules.py` | Sí. Publica sis fitxers que encara no demana ningú |
| **2** | Els 245 homògrafs i les 604 correccions conegudes, portades als tres dialectes | Sí |
| **3** | Workflows: el pas nou, el `versions.json`, la poda del `deploy.yml` | Sí |
| **4** | El web: desplegable, càrrega, commutació, preferència, `?d=`, etiqueta de proves | **Aquí es veu per primera vegada** |
| **5** | Pàgines `/valencia/`, `/balear/`, `/nord-occidental/`, menú, botó de compartir, JSON-LD | Sí |
| **6** | Estadístiques (§8) | Sí |
| **7** | Llistes per dialecte (§7) | Sí |
| **8** | Revisió lingüística contínua amb el que arribi per `error.html` | — |

L'ordre importa en dos punts i prou: la 3 necessita la 1, i la 4 necessita la 3. La 2 i la 6 poden anar quan es vulgui.

---

## 11. Decisions que necessiten resposta

1. **El lèxic (opció B) i els seus 44 MB al repositori**: es tira endavant, o es prefereix la A i refer els fitxers sencers en local a cada canvi de diccionari?
2. **Pàgines per dialecte o només `?d=`.** Les pàgines són la diferència entre poder-se trobar a Google amb "rimes en valencià" o no.
3. **Les 245 files d'homògrafs**: es fan a mà ara (fase 2) o els dialectes surten sabent que `cop` i `cos` hi rimen malament?
4. **Nom de les varietats al desplegable**: "Català central / Nord-occidental / Valencià / Balear" o alguna altra cosa. Té conseqüències a les adreces, que després no es poden canviar sense trencar enllaços.
5. **L'`espeak-ng` és prou bo per publicar-hi?** El central hi va necessitar 604 correccions (0,10 %). Si es demana la mateixa qualitat als dialectes abans de publicar-los, són tres revisions de mig any; si es publiquen en proves i es corregeixen amb el que arribi, surten aquest mes.
