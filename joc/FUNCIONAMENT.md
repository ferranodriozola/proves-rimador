# El joc del Rimador — funcionament intern

Nota per a tu d'aquí a un any. El [`README.md`](README.md) explica **què és** el
joc i **com posar-lo en marxa**; això d'aquí explica **com funciona per dins**:
d'on surt cada dada, qui la transforma, què fa cada fitxer i on són les costures.

Al final hi ha un apartat de [**coses que convé saber**](#12-coses-que-convé-saber)
amb el que encara està obert.

---

## 1. La idea de tot plegat

El joc és una **pàgina estàtica** a `rimador.cat/joc/`. No té servidor propi. Tota
la lògica passa al navegador i les úniques coses que baixa són fitxers de text
que hi ha comitejats al repositori.

Està **aïllat de la resta del web** a propòsit:

| | web principal | joc |
|---|---|---|
| CSS | `css/*.scss` → gulp → `dist/css/styles.min.css` | `joc/css/joc.css`, a pèl |
| JS | `js/*.js` → gulp → `dist/js/script.min.js` | `joc/js/*.js`, mòduls ES natius |
| dades | tot el diccionari (46 MB) a IndexedDB | 1 índex + 1 fitxer de rimes per partida |

El `gulpfile.js` només mira `css/` i `js/` de l'arrel, o sigui que **res d'aquesta
carpeta no passa per cap compilació**. El navegador es carrega els mòduls tal com
són.

El que **sí** que comparteix amb el web principal són tres coses, i totes tres per
alguna raó:

- **L'estètica** (rosa/cian), escrita a part.
- **El dialecte triat** (`localStorage['rimadorDialecte']`) i **l'identificador
  d'usuari** (`rimador_usuari_id`): les dues meitats del lloc han de coincidir en
  què estàs mirant i qui ets.
- **La manera de gestionar versions**, que és la mateixa idea aplicada dues
  vegades (apartat 9).

---

## 2. D'on surten les dades

### La cadena sencera

```
diccionaris/diccionari.5.2.3.txt      ← l'edites tu a mà (quines paraules hi ha)
diccionaris/col_10.txt                ← l'edites tu a mà (com sona cadascuna)
        │
        │  diccionaris/python/*.py  (workflow diccionaris.yml)
        ▼
diccionaris/separat/col_0,1,2,5,6,7,8.txt          paraula, lema, codi, síl·labes…
dialectes_col/<ca|nw|va|ba>/col_3_rimacons_*.txt   clau de rima CONSONANT
dialectes_col/<ca|nw|va|ba>/col_4_rimaass_*.txt    clau de rima ASSONANT
        │
        │  joc/eines/generar_dades.py   ← A MÀ, no hi ha cap workflow
        ▼
joc/dades/versions.json       quins dialectes hi ha i el resum de cada fitxer
joc/dades/<codi>/index.json   les claus jugables d'aquell dialecte
joc/dades/<codi>/rimes/N.txt  els grups de rimes
        │
        │  fetch() des del navegador
        ▼
la partida
```

Les columnes són **fitxers paral·lels**: la línia *N* de `col_0.txt` és la
paraula, la de `col_2.txt` el seu codi gramatical i la de `col_3_rimacons_ca.txt`
la seva clau de rima consonant en central. Tot l'encaix és per número de línia;
per això el generador s'atura de seguida si les columnes no tenen la mateixa
llargada.

### On és cada cosa: `camins.py`

El generador **no sap cap ruta**. Les demana totes a
`diccionaris/python/camins.py`, que és el vocabulari compartit de tots els
scripts del repositori:

```python
sys.path.insert(0, os.path.join(ARREL, "diccionaris", "python"))
import camins

camins.dialectes()                 # ['ba', 'ca', 'nw', 'va'] — les carpetes de dialectes_col/
camins.cami_columna(0)             # diccionaris/separat/col_0.txt
camins.cami_dialecte('va', 3)      # dialectes_col/va/col_3_rimacons_va.txt
camins.llegir_columna(cami)        # una línia per fila, sense salt final
```

Això no és cosmètic. La rima **ja no és a `diccionaris/separat/`**: hi era fins a
l'agost del 2026 i llavors es va moure a `dialectes_col/<codi>/`, perquè depèn de
com es parli. El generador del joc apuntava a la ruta vella i havia deixat de
funcionar. Ara segueix els camins que digui `camins.py`, i si un dia es tornen a
moure, el joc hi va al darrere sense tocar res.

**Els dialectes tampoc no es declaren enlloc**: són les subcarpetes de
`dialectes_col/`. Un dialecte nou és una carpeta amb la seva transcripció, i el
generador ja el troba.

### Els dos invariants que ho fan possible

Aquí hi ha tota la gràcia del disseny. El diccionari sencer fa 46 MB i el joc no
es pot permetre esperar-lo, o sigui que la generació es recolza en dues coses:

**1. Una clau consonant sempre implica la mateixa clau assonant.** El generador
ho comprova a cada passada, per a cada dialecte, i s'atura si algun dia deixa de
ser cert:

```python
anterior = cons_a_asson.setdefault(clau, rima_asson[i])
if anterior != rima_asson[i]:
    raise SystemExit(f"[{codi}] la clau consonant '{clau}' apunta a dues claus assonants …")
```

Conseqüència: si agrupes els fitxers **per clau assonant** i, a dins, els
subdivideixes **per clau consonant**, un sol fitxer serveix les dues dificultats.

- **Fàcil** (assonant) = *totes* les paraules del fitxer.
- **Difícil** (consonant) = només les de la secció on és la paraula objectiu.

**Una sola descàrrega per partida**, tant si jugues en fàcil com en difícil.

**2. No cal cap llista de paraules objectiu.** Pot ser objectiu qualsevol paraula
d'una clau consonant amb prou rimes, i quantes n'hi ha se sap només amb l'índex.
L'índex guarda el recompte i el joc tria la clau amb probabilitat proporcional a
aquest recompte, de manera que **totes les paraules objectiu són igual de
probables** sense haver-les de llistar enlloc.

### Els números d'ara

| dialecte | claus jugables | paraules objectiu | fitxers | mediana | el més gros |
|---|---|---|---|---|---|
| Central (`ca`) | 500 | 123.429 | 38 | 63 KB | 1,5 MB |
| Nord-occidental (`nw`) | 484 | 122.673 | 52 | 28 KB | 1,3 MB |
| Valencià (`va`) | 488 | 122.461 | 51 | 28 KB | 1,3 MB |
| Balear (`ba`) | 496 | 124.563 | 42 | 60 KB | 1,5 MB |

En total, `joc/dades/` fa **30 MB** i 183 fitxers de rimes. Es publica sencer a
Pages, però una partida només en baixa **tres**: el `versions.json` (7 KB),
l'`index.json` del seu dialecte (7 KB) i un fitxer de rimes (34 KB de mediana).

Els fitxers no són els mateixos a cada dialecte, ni tan sols n'hi ha el mateix
nombre: el nord-occidental parteix les paraules en 52 grups assonants i el
central en 38. Per això la numeració (`rimes/14.txt`) **no vol dir res per si
sola**: és la posició dins la llista de grups d'aquell dialecte, i canvia si es
regeneren les dades.

---

## 3. El format dels fitxers generats

### `dades/versions.json`

```json
{
  "generat": "2026-08-29 21:10:26 UTC",
  "dialectes": [
    { "codi": "ca", "nom": "Central" },
    { "codi": "nw", "nom": "Nord-occidental" }
  ],
  "fitxers": {
    "ca/index.json": "13c5c9275d6a",
    "ca/rimes/0.txt": "5f2a1b9c4e01"
  }
}
```

Fa dues feines alhora: diu **quins dialectes hi ha** (i com es diuen, i en quin
ordre van a la tira) i **quina versió té cada fitxer**. El joc no sap res dels
dialectes si no és per aquí, o sigui que no pot oferir-ne cap del qual no tingui
les dades.

### `dades/<codi>/index.json`

```json
{"dialecte":"ca","min_rimes":50,"fitxers":38,
 "claus":[["a",0,1616],["abblə",4,961],["adʒə",4,427], …]}
```

Cada entrada de `claus` és `[clauConsonant, númeroDeFitxer, nombreDObjectius]`.
Res més: ni les paraules ni cap altra metadada. Les claus van **ordenades
alfabèticament**, i això importa (apartat 7).

### `dades/<codi>/rimes/N.txt`

```
#aðə              ← capçalera de secció: clau de rima consonant
*cascada          ← l'* marca que pot ser OBJECTIU (no és verb)
cavalcava         ← sense *, només val com a RIMA (aquí, una forma verbal)
*cami>camí        ← si la forma real porta accents, va després del ">"
```

Tres decisions que val la pena recordar:

- **La part esquerra ja és la forma normalitzada.** El joc no normalitza res del
  fitxer en temps d'execució: només parteix línies per `\n`, mira el primer
  caràcter i busca un `>`. Tot el cost de treure accents ja s'ha pagat al Python.
- **L'`*` separa els dos papers d'una paraula.** Objectiu (la que t'han de rimar)
  i resposta (la que pots escriure) no són el mateix conjunt: els verbs valen com
  a resposta però mai com a objectiu, perquè rimar-hi amb altres formes
  conjugades seria massa fàcil. Es decideix **quan es generen les dades**.
- **El `>` només hi és quan cal.** Si la paraula no porta accents, la línia és una
  sola paraula i el `mostrar` és el mateix que el `normalitzada`.

---

## 4. `generar_dades.py`, pas a pas

```bash
python joc/eines/generar_dades.py            # tots els dialectes (~40 s)
python joc/eines/generar_dades.py ca va      # només aquests
```

Constants de dalt de tot que manen:

| constant | ara | què fa |
|---|---|---|
| `MIN_RIMES` | 50 | una clau consonant és jugable si té **més de** 50 formes úniques |
| `EXCLOURE_VERBS_OBJECTIU` | `True` | els verbs no poden ser paraula a rimar |
| `EXCLOURE_PLURALS_OBJECTIU` | `False` | si es posés a `True`, els plurals tampoc |
| `NOMS_DE_DIALECTE` | 4 entrades | com es diu cada codi i en quin ordre va a la tira |

El procés, per a cada dialecte:

1. **Llegeix les columnes**: paraula i codi del diccionari (compartides), rima
   consonant i assonant del dialecte.
2. **Filtra les respostes vàlides**: fora els noms propis (codi que comença per
   `NP`) i tot el que no sigui alfabètic un cop tret els guionets i els apòstrofs
   (així *adeu-siau* i *d'acord* hi entren).
3. **Agrupa per clau consonant** en `{formaNormalitzada: formaPerMostrar}`. Si
   dues entrades col·lapsen a la mateixa forma normalitzada (*dona* / *dóna*), es
   queda **la més curta d'escriure**: només serveix per ensenyar-la.
4. **Marca els objectius.** Subtilesa: una forma és objectiu si **alguna** de les
   seves entrades no és verb. *Poder* és verb i nom alhora; com a nom, pot ser
   objectiu.
5. **Comprova l'invariant** consonant → assonant i peta si falla.
6. **Qualifica les claus**: més de `MIN_RIMES` formes *i* almenys un objectiu.
7. **Escriu un fitxer per grup assonant** dels que fan falta. Cada fitxer conté
   el grup assonant **sencer**, seccions no qualificades incloses: fan falta per
   validar el mode fàcil.
8. **Escriu l'`index.json`** del dialecte.

I al final de tot, **el `versions.json`** amb el resum de tot el que hi ha
(inclosos els dialectes que no s'hagin regenerat en aquesta passada).

Dues coses que fa i que no es veuen:

- **No reescriu el que no ha canviat** (`escriure_si_cal`). Una passada sense
  canvis al diccionari no deixa cap diff ni toca cap data de fitxer.
- **Neteja el que sobra**: els `rimes/N.txt` que ja no apunta ningú, i les
  carpetes de dialectes que hagin desaparegut de `dialectes_col/`.

> ⚠️ **Regenerar les dades canvia la paraula del dia** d'aquell dia per a qui
> encara no l'hagi jugada, perquè la tria depèn de l'ordre i dels pesos de
> l'índex. Val més fer-ho de nit.

---

## 5. Els mòduls JS, un per un

Deu mòduls ES. `index.html` només en carrega un (`principal.js`) i la resta entren
per `import`. La divisió és estricta: **`ui.js` és l'únic que toca el DOM** i
**`motor.js` no en sap res**.

```
index.html
    └── principal.js          el fil conductor
            ├── dades.js          versions, fetch i parsing
            ├── dialecte.js       quin dialecte es juga
            ├── objectius.js      quina paraula toca
            ├── motor.js          rellotge, validació, puntuació
            │       └── normalitza.js
            ├── ui.js             tot el DOM
            ├── magatzem.js       localStorage
            ├── compartir.js      graella d'emojis + porta-retalls
            └── classificacio.js  enviar/llegir el rànquing
```

### `principal.js` — el fil conductor

L'únic mòdul amb estat global de debò:

```js
const estat = { mode, dificultat, segons, dialecte, partida, ultimResum, data };
```

Lliga els botons amb les pantalles, demana les dades, construeix la `Partida`, i
quan s'acaba desa el rècord i pinta el final. No hi ha router ni framework:
`mostrarPantalla()` posa `hidden` a totes les `<section class="pantalla">` menys
una.

**L'arrencada és asíncrona** i té un ordre que importa: primer el `versions.json`
(per saber quins dialectes hi ha), després `dialecte.inicial()` (per saber quin
es juga), després la tira, i tot seguit l'`index.json` d'aquell dialecte, que es
demana sense esperar-lo perquè estigui a punt abans que ningú premi cap botó. Si
el `versions.json` no arriba, es juga en central i prou.

### `dades.js` — versions, descàrrega i lectura

- `carregarVersions()` — el `versions.json`, sempre amb `?t=` i mai cachejat. Si
  falla, estira dels resums desats al `localStorage` (apartat 9).
- `carregarIndex(dialecte)` i `carregarFitxerDeRimes(dialecte, numero)` — guarden
  **la promesa**, no el resultat, de manera que dues crides simultànies
  comparteixen la mateixa descàrrega. La memòria cau va per dialecte, o sigui que
  anar i venir de la tira no rebaixa res.
- `respostesValides(fitxer, clau, dificultat)` — el `Map` de respostes: en
  **difícil** una còpia de la secció; en **fàcil** la fusió de totes les seccions.

L'anàlisi (`analitzar`) recorre el text una vegada comparant codis de caràcter
(`35` = `#`, `42` = `*`) i deixa cada secció com
`{ paraules: Map<normalitzada, mostrar>, objectius: [normalitzada, …] }`.

### `dialecte.js` — quin dialecte es juga

La germana de `dialecteInicial` / `lligarTriaDeDialecte` de `js/script.js`, amb
les mateixes regles i **la mateixa clau de `localStorage`**:

1. El `?d=` de l'adreça, si el codi existeix. **No es desa**: obrir l'enllaç que
   t'ha passat algú val per a aquella visita i no t'ha de canviar el de sempre.
2. El que hi hagi desat a `rimadorDialecte`.
3. El central.

Triar-ne un a la tira sí que el desa i l'escriu a l'adreça amb `replaceState`
(no `pushState`: triar un dialecte no és anar a cap altra pàgina).

Els codis vàlids no són aquí: els passa `principal.js` a partir del
`versions.json`.

### `objectius.js` — quina paraula toca

- **`llavor(text)`** — variant de cyrb53: barreja els bits d'una cadena en un
  enter de 32 bits.
- **`generador(sembra)`** — mulberry32, un PRNG petit i **determinista**.
- **`triarClau(index, aleatori)`** — tria ponderada, amb la suma acumulada dels
  objectius i una **cerca binària** sobre els talls.

L'acumulat es guarda en un **`WeakMap` indexat per l'array de claus**, i no en una
sola variable com abans: amb quatre dialectes, anar i venir de la tira alternaria
dos índexs i una sola casella no encertaria mai.

### `motor.js` — la partida

Una classe `Partida` que **no toca el DOM**: avisa amb els *callbacks* `alTic` i
`alFinal`.

- **El rellotge**: `setInterval` cada 100 ms perquè es vegi fluid, però el temps
  de veritat el marca `instantFinal = Date.now() + segons * 1000`. Si el
  navegador s'atura (pestanya de fons, mòbil que s'adorm), no es descompensa.
- **`provar(text)`** retorna un dels cinc `RESULTAT`: `BUIT`, `OBJECTIU`,
  `REPETIDA`, `NO_RIMA` o `ENCERT`. En aquest ordre exacte.
- **La paraula objectiu no val com a resposta**: el constructor fa
  `this.respostes.delete(objectiu.normalitzada)`. Pot fer-ho sense por perquè
  `respostesValides()` sempre torna un `Map` nou.
- **Les errades no s'apunten**: provar dues vegades una paraula que no rima torna
  a dir "No rima" i no pas "Ja introduïda".

### `normalitza.js` — el contracte amb el Python

Vint-i-set línies, però són **la peça més delicada del joc**:

```js
.trim().toLowerCase()
.replace(/’/g, "'")     // apòstrof tipogràfic
.replace(/·/g, '')      // el punt volat de la l·l
.normalize('NFD').replace(/[̀-ͯ]/g, '')   // fora diacrítics, cedilla inclosa
```

Ha de **coincidir exactament** amb `normalitzar()` de `generar_dades.py`. Si es
desincronitzen, hi ha paraules del fitxer que el joc no reconeixerà mai, i **no
hi haurà cap error visible**: simplement dirà "No rima" a coses que hi rimen.

### `ui.js` — tot el DOM

- `preparar()` omple l'objecte `el` amb tots els `getElementById`.
- `grupOpcions()` converteix un grup de `<button class="opcio">` en un
  *radiogroup* accessible, amb `valor()`, `seleccionar()` i `activar()`.
- `pintarTiraDialectes()` pinta la tira **tal com li arriba** la llista: no sap
  quins dialectes hi ha ni com es diuen.
- `texteBoto()` existeix perquè els botons de l'arc de Sant Martí porten el text
  dins d'un `<span>`.
- `animarEntrada()` força un *reflow* perquè l'animació es torni a disparar quan
  es repeteix el mateix resultat.
- `filaRecord()` és compartida per "Els meus rècords", la classificació per
  modalitats i la de cada dia.

### `magatzem.js` — el que es recorda

Tot embolcallat en `try/catch`: en navegació privada el `localStorage` peta i el
joc ha de continuar funcionant igual.

| clau | què hi ha |
|---|---|
| `rimador.joc.records.v2` | `{ "illimitat\|dificil\|45\|va": 12, … }` |
| `rimador.joc.diaria.v2` | `{ data: "2026-08-29", partides: { "ca\|facil": {…} } }` |
| `rimador.joc.sobrenom.v1` | el sobrenom de la classificació |
| `rimador.joc.versions.v1` | còpia dels resums, per si el `versions.json` falla |
| `rimadorDialecte` | **compartida amb el cercador** |
| `rimador_usuari_id` | **compartida amb el cercador** |

- **Els rècords van per modalitat**, amb l'identificador
  `mode|dificultat|segons|dialecte`.
- **La migració v1 → v2** es fa un sol cop, en carregar el mòdul: els rècords
  vells (de tres trossos) eren tots en central i se'ls hi posa el codi `ca`.
  Després, la clau v1 s'esborra.
- **De la paraula del dia només es desa el dia d'avui.** Quan canvia la data,
  l'entrada vella se substitueix sencera i el magatzem no creix mai. La clau va
  per dialecte, perquè cadascun té la seva paraula.

`avui()` fa servir l'**hora local** del navegador, no UTC.

### `compartir.js` — la graella d'emojis

Quadrets blaus, cinc per fila, màxim sis files. **No diu ni la paraula que tocava
ni cap de les rimes.** Sí que diu el dialecte, perquè sense això dos resultats del
mateix dia no es podrien comparar i ningú no sabria per què.

`compartirResultat()` prova `navigator.share`, i si no hi és cau al porta-retalls:
primer `navigator.clipboard`, i si tampoc, el `<textarea>` amagat amb
`document.execCommand('copy')`.

### `classificacio.js` — el rànquing

Vegeu l'apartat 8.

---

## 6. El flux d'una partida

```
arrencar()
   ├─ carregarVersions()          dades/versions.json?t=…
   ├─ dialecte.inicial(codis)     ?d= → localStorage → 'ca'
   └─ carregarIndex(dialecte)     dades/<codi>/index.json?v=<resum>

comencarPartida()
   │
   ├─ prepararParaula()
   │     ├─ carregarIndex(dialecte)
   │     ├─ clauDelDia(index, data, dialecte) o clauAleatoria(index)
   │     ├─ carregarFitxerDeRimes(dialecte, fitxer)
   │     ├─ triarParaula(fitxer, clau, aleatori)   → { normalitzada, mostrar }
   │     └─ respostesValides(fitxer, clau, dif)    → Map<normalitzada, mostrar>
   │
   ├─ ui.pintarObjectiu() / ui.mostrarPantalla('joc')
   └─ new Partida({…}).comencar()
            │  cada 100 ms → alTic  → ui.actualitzarRellotge()
            │  cada Enter  → provar() → ui.avisar() / ui.afegirTrobada()
            ▼
        alFinal(resum)  →  acabarPartida()
            ├─ desarRecord(identificador, punts)
            ├─ desarResultatDiari()   (només en mode diària)
            ├─ ui.pintarFinal()
            └─ prepara el bloc d'enviament a la classificació
```

---

## 7. La paraula del dia

No hi ha cap servidor que la digui. **Tothom la calcula**, a partir de la data,
del dialecte i del mateix `index.json`:

```js
const aleatori = generador(llavor(`rimador-joc-${dataISO}-${dialecte}`));
const seleccio = triarClau(index, aleatori);             // consumeix un valor
const objectiu = triarParaula(fitxer, clau, aleatori);   // consumeix el següent
```

Detalls que importen:

- **Cada dialecte té la seva paraula.** No pot ser la mateixa per a tothom: la
  paraula surt de l'índex de claus de rima i cada dialecte té el seu. Encara que
  la llavor no dugués el dialecte, hi cauria en una paraula diferent igualment;
  posant-l'hi, això queda **dit** en comptes de passar de retruc, i dos dialectes
  no s'hi poden trobar per casualitat. Un dia qualsevol: *esgarriacries* en
  central, *botilleres* en nord-occidental, *gilberts* en valencià i *supercròs*
  en balear.
- **La dificultat no entra a la llavor.** La paraula és la mateixa tant si la
  jugues en fàcil com en difícil; l'únic que canvia és quantes rimes s'accepten.
- **La data és local.** Qui viu en un altre fus horari veu la paraula de demà
  abans.
- **Depèn de l'ordre i dels pesos de l'índex.** Regenerar `dades/` la canvia.
- **Un intent per dialecte, dificultat i dia.** El bloqueig és a `localStorage` i
  prou: esborrar-lo, o obrir una finestra privada, permet repetir. És un joc, no
  un examen.

---

## 8. La classificació: el circuit sencer

```
navegador                Google                    tu, a mà                 navegador
─────────                ──────                    ────────                 ─────────
classificacio.js   POST   Apps Script    →   full   compilar_          →   classificacio.json
enviarPuntuacio()  no-cors  doPost()        de      classificacio.py       carregarClassificacio()
                            appendRow()     càlcul  (llegeix el CSV        modalitats + diària
                                                     publicat, valida
                                                     i desdupla)
```

### L'enviament (`classificacio.js`)

`POST` amb `mode: 'no-cors'` — no es pot llegir la resposta, o sigui que "enviat"
vol dir "el `fetch` no ha petat", no pas "s'ha desat".

**S'envia des d'on sigui.** `estaConfigurat()` només mira que hi hagi
`URL_ENVIAMENT`, o sigui que des de `localhost` i des del repositori de proves les
puntuacions arriben al full de debò.

El cercador no funciona així: `registrarCerca` (`js/script.js:985`) surt de
seguida si l'amfitrió no és `rimador.cat` o `rimador.github.io`, perquè les
cerques de prova no valen res i només fan soroll. Aquí la decisió és la
contrària, i a consciència: una classificació que no deixa enviar res mentre la
proves no es pot provar de veritat. El filtre de debò és el compilador, que és qui
decideix què es publica; si al full hi entra soroll, s'esborra la fila allà.

### Les dues dates

El navegador envia el **dia de la partida**; el servidor de Google apunta el **dia
que ha arribat l'enviament**. Són columnes diferents del full (`DataPartida` i
`Data`) perquè **no són el mateix**: qui juga la paraula del dia a les 23.55 i
l'envia a les 00.05 ha jugat la d'ahir. El rànquing per dia agrupa per
`DataPartida`; la `Data` serveix per veure quan va passar de debò.

### El backend (`apps_script_classificacio.gs`)

Poques línies. Valida que els punts siguin entre 0 i 10.000 i que la
`DataPartida` tingui la forma `AAAA-MM-DD`; si no la té, la deixa buida i ja hi
posarà el compilador la d'arribada. Escriu una fila de deu columnes:

```
Data | DataPartida | Sobrenom | Mode | Dificultat | Segons | Dialecte | Punts | Paraula | Usuari
```

### El compilador (`compilar_classificacio.py`)

Aquí és on es decideix de debò què es publica. Necessita `pandas`:

```bash
python joc/eines/compilar_classificacio.py
```

1. Llegeix el full publicat en CSV.
2. **Es planta si falten les columnes de sempre**, però **no si falten les noves**
   (`DataPartida`, `Dialecte`): les files d'abans dels dialectes es donen per
   centrals i pel dia que van arribar, i no es perden.
3. **Revalida els sobrenoms** i aplica la llista `PARAULES_VETADES`, comparant
   sense accents i en minúscules.
4. **Desdupla per persona**: la clau és l'`usr_…` si hi és, i si no el sobrenom
   sense accents. De cada persona i modalitat, només la millor puntuació.
5. Escriu els dos rànquings.

### Què en surt

```json
{
  "actualitzacio": "29/08/2026 23:16:27",
  "modalitats": {
    "illimitat|dificil|45|ca": { "titol": "Il·limitat · Difícil · Llampec · Central",
                                 "dialecte": "ca", "top": [ … ] }
  },
  "diaria": {
    "2026-08-26": { "ca": { "paraula": "esgotador", "dificil": [ … ] } }
  }
}
```

**Els dos es veuen al joc**, cadascun a la seva pestanya de la pantalla de
classificació. El bloc `diaria` es calculava des del principi però no el llegia
ningú; ara té la seva pantalla, amb una pastilla per dia (els últims 30) i una
taula per dificultat.

Les dues pestanyes **estan filtrades pel dialecte que tens triat**: el rànquing
del central i el del valencià són de paraules diferents i barrejar-los no voldria
dir res.

### La lectura

`carregarClassificacio()` fa `fetch` amb `?t=${Date.now()}`. És la mateixa regla
que el `versions.json`: **el fitxer que diu com estan les coses ara no es pot
cachejar mai**. Aquest canvia cada cop que passes el compilador, sense que canviï
la versió de res.

---

## 9. La gestió de versions

És **una sola idea aplicada dues vegades**, i és la mateixa que la del diccionari.

### Les dades: resum de contingut

`generar_dades.py` calcula un `sha256` escurçat a 12 caràcters de cada fitxer i
l'escriu al `dades/versions.json` — exactament el que fa
`diccionaris/python/versions.py` amb les columnes. La versió d'un fitxer **canvia
exactament quan el fitxer ha canviat**: ni abans ni de més.

Al navegador:

```
dades/versions.json?t=1788038423657          ← mai cachejat
dades/ca/index.json?v=13c5c9275d6a           ← cachejable per sempre
dades/ca/rimes/14.txt?v=6d2aafff65ef         ← cachejable per sempre
```

Si el `versions.json` no es pot llegir (sense xarxa, servidor caigut, fitxer
romput), s'estira dels resums de l'última vegada, desats al `localStorage`. El
que el navegador tingui a la memòria cau es va demanar amb **aquells** resums, o
sigui que donant-los per bons se serveix una generació sencera i coherent de les
dades. És el mateix rescat que fa `carregarVersions` a `js/script.js`. I si no hi
ha res de què estirar, cada fitxer es demana amb un `?v=t<ara>` sempre diferent,
que és pitjor però mai incoherent.

Una diferència amb el `versions.json` del diccionari: **aquí les claus són
camins** (`ca/rimes/0.txt`) i no noms de fitxer sols. Allà el navegador indexa la
memòria cau d'IndexedDB pel nom (`rutaFitxer.split("/").pop()`) i cada fitxer és
únic; aquí el `ca/rimes/0.txt` i el `va/rimes/0.txt` es dirien igual.

### El codi: el `?v=` del commit

El `deploy.yml` posa els set primers caràcters del `GITHUB_SHA` a tots els `?v=`
quan detecta canvis. Ara `joc/` hi entra com l'arrel:

```yaml
git diff … -- 'css/*.scss' 'js/*.js' 'avis/*.js' 'avis/*.css' 'joc/js/*.js' 'joc/css/*.css'
```

I el `sed` no escriu només als HTML, sinó també **a les importacions entre
mòduls**:

```yaml
find joc/js -type f -name "*.js" -exec sed -i -E "s/(\.js\?v=)[^']*/\1$NOVA_VERSIO/g" {} +
```

Això últim fa falta perquè **una importació no hereta el `?v=` de l'etiqueta
`<script>`**. Abans només `principal.js` i `joc.css` en duien, i els altres vuit
mòduls s'importaven a pèl: refrescar l'entrada deixava la resta a la memòria cau
del navegador i es barrejaven versions. El `?v=dev` que hi ha al repositori és el
valor de treball; el desplegament el substitueix (i al repositori de proves, on el
pas de *cache busting* no corre, s'hi queda i funciona igual).

Les **dades** del joc no passen per aquí, i no és cap oblit: ja porten el resum
del seu contingut, que és millor. Un canvi al diccionari no ha de rebentar la
memòria cau del CSS, ni al revés.

---

## 10. `index.html` i `joc.css`

L'HTML té **totes les pantalles alhora**, amagades amb l'atribut `hidden`. No hi
ha plantilles ni generació de marcatge: `ui.js` només canvia `hidden`, textos i
llistes. Les úniques coses que es creen amb `createElement` són les files de
rècords, les de la classificació, les pastilles, la tira de dialectes i els `<li>`
de paraules trobades.

`joc.css` són 870 línies escrites a mà, mòbil primer, amb tota la paleta a
`:root`. Val la pena recordar-ne dues:

```css
[hidden] { display: none !important; }
```

L'`!important` hi és perquè hi ha regles (`.boto--gran`, `.carregant`) que fixen
el `display` i, sense això, guanyarien i les pantalles amagades es veurien.

```css
@media (prefers-reduced-motion: reduce) { /* anul·la totes les animacions */ }
```

---

## 11. Taula de referència ràpida

| fitxer | què fa | qui l'escriu |
|---|---|---|
| `index.html` | totes les pantalles, amagades amb `hidden` | tu |
| `css/joc.css` | l'estètica, a pèl (no passa pel gulp) | tu |
| `js/principal.js` | fil conductor: pantalles, estat, esdeveniments | tu |
| `js/dades.js` | versions, `fetch` i anàlisi dels fitxers de rimes | tu |
| `js/dialecte.js` | quin dialecte es juga (`?d=`, `localStorage`, central) | tu |
| `js/objectius.js` | tria ponderada de clau + PRNG de la paraula del dia | tu |
| `js/motor.js` | classe `Partida`: rellotge, validació, puntuació | tu |
| `js/normalitza.js` | fora accents — ha de coincidir amb el Python | tu |
| `js/ui.js` | l'únic mòdul que toca el DOM | tu |
| `js/magatzem.js` | `localStorage`: rècords, dia jugat, sobrenom, versions | tu |
| `js/compartir.js` | graella d'emojis + `navigator.share` / porta-retalls | tu |
| `js/classificacio.js` | enviar la puntuació i llegir el rànquing | tu |
| `dades/versions.json` | quins dialectes hi ha i el resum de cada fitxer | `generar_dades.py` |
| `dades/<codi>/index.json` | les claus jugables d'aquell dialecte | `generar_dades.py` |
| `dades/<codi>/rimes/N.txt` | els grups de rimes | `generar_dades.py` |
| `dades/classificacio.json` | el rànquing publicat | `compilar_classificacio.py` |
| `eines/generar_dades.py` | diccionari + rima → `dades/` | tu |
| `eines/compilar_classificacio.py` | full CSV → `classificacio.json` | tu |
| `eines/apps_script_classificacio.gs` | codi que viu a Google, no aquí | tu |

---

## 12. Coses que convé saber

### El full de càlcul necessita dues columnes noves 🔴

És **l'únic pas que queda per fer a mà**, i fins que no es faci, les puntuacions
noves perdran el dialecte i el dia de la partida. A la fila 1 del full hi ha
d'haver:

```
Data | DataPartida | Sobrenom | Mode | Dificultat | Segons | Dialecte | Punts | Paraula | Usuari
```

Les que hi falten són `DataPartida` (segona) i `Dialecte` (setena). El compilador
ja aguanta que no hi siguin (dona les files per centrals i pel dia d'arribada),
o sigui que no peta res mentrestant, però el rànquing per dialecte no tindrà mai
res que no sigui central.

També cal **tornar a desplegar l'Apps Script** després d'enganxar-hi la versió
nova: el codi que corre a Google és una còpia, no el fitxer del repositori.

### Cap dels dos scripts és a cap workflow

Ni `generar_dades.py` ni `compilar_classificacio.py`. Les dades del joc i el
rànquing es refresquen quan els passes tu i els comiteges. El `README.md` apunta
que es podrien programar a l'estil de `stats.yml`; la del rànquing seria la que
més s'ho val, perquè avui la classificació és tan fresca com l'últim cop que te'n
vas recordar.

### La classificació és de confiança i prou

El `POST` no està autenticat: qualsevol pot enviar-hi el que vulgui fins a 10.000
punts, amb el sobrenom que vulgui. Per a un joc de rimes és una decisió
raonable, però convé saber-ho: l'única defensa real és que el rànquing el
publiques tu, a mà, executant el compilador — i que el compilador té l'última
paraula sobre què s'accepta.

### Les dades ocupen 30 MB al repositori

Quatre dialectes per 7,5 MB. Es publiquen sencers a Pages i cada partida només en
baixa un fitxer, o sigui que no costa res a qui juga; però sí que és espai al
repositori, i es torna a escriure sencer cada cop que canvia la rima d'un
dialecte. Si un dia hi ha un cinquè dialecte, seran uns 38 MB. El `.gitignore` no
els toca a posta: han d'anar al paquet que es publica.

### El `?v=dev` no és cap error

És el valor de treball de les importacions i de l'HTML del joc. Al desplegament de
`rimador.cat` el substitueix el commit; al repositori de proves s'hi queda, perquè
allà el pas de *cache busting* no corre. En tots dos casos funciona.
