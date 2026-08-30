# El joc del Rimador.cat

Joc de rimes fet damunt del mateix diccionari fonètic que fa servir el cercador.
Viu a `rimador.cat/joc/` i va gairebé sol. El **JS** no comparteix res amb el lloc
principal: són mòduls ES que se serveixen tal com són. El **CSS** sí que passa pel
gulp (`joc/css/joc.scss` → tasca `styles-joc` → `dist/css/joc.min.css`) i comparteix
el `css/_variables.scss` amb el full del lloc, però en **surt un full a part**: els
dos tenen regles damunt de `html`, `body`, `a` i `*`, i ajuntar-los les faria xocar.
Compartir el fitxer de variables és, doncs, tot el que comparteixen: els colors de
la casa són escrits un sol cop. L'estètica és la mateixa de sempre: fons rosa,
plafons cians, vores gruixudes i tipografies de tota la vida.

Si el que vols és entendre com funciona per dins, mira
[FUNCIONAMENT.md](FUNCIONAMENT.md).

## Com es juga

Et donem una paraula i has d'escriure-hi totes les rimes que puguis abans que
s'acabi el temps.

- **Fàcil** valida contra rimes **assonants** (només les vocals a partir de la
  tònica). **Difícil**, contra rimes **consonants**.
- **Paraula del dia**: la mateixa paraula per a tothom qui juga en aquell
  dialecte, 1 minut, un intent per dificultat i dia.
- **Il·limitat**: paraula nova cada partida i tres rellotges (45 s, 1 min 30 s,
  3 min).

Els accents no compten enlloc: escriure *cami* val per *camí* i *forca* per
*força*. Si una paraula ja s'ha enviat (amb accents o sense), es rebutja.

**La paraula objectiu mai és un verb** (seria massa fàcil rimar-hi amb altres
formes verbals conjugades), però els verbs sí que valen com a resposta. Això es
decideix quan es generen les dades, no en temps d'execució.

Des del menú pots veure **Els meus rècords** (les teves millors puntuacions,
desades en aquest navegador) i la **Classificació** (les de tothom), amb dues
pestanyes: **Il·limitat**, amb una taula per cada rellotge i dificultat, i
**Paraula del dia**, on tries dia i dificultat i veus el rànquing d'aquell dia i,
a sota, els deu millors de sempre.

## Els dialectes

S'hi juga en els **quatre dialectes** que serveix el cercador, i es tria amb la
tira de la pantalla d'inici. Comparteix la memòria amb el cercador
(`localStorage['rimadorDialecte']`) i entén el mateix paràmetre a l'adreça
(`rimador.cat/joc/?d=va`), o sigui que qui hagi triat el valencià al cercador es
troba el joc en valencià sense haver-ho de tornar a dir.

El dialecte no és cap capa per sobre: **canvia les rimes de debò**, perquè cada
dialecte reparteix les paraules en grups de rima diferents. Per això:

- **Cada dialecte té la seva paraula del dia.** No pot ser la mateixa: la
  paraula surt de l'índex de claus de rima, i cada dialecte té el seu. La llavor
  du el dialecte a dins perquè això quedi dit i no passi de retruc.
- **Els rècords van per dialecte**, com van per rellotge i dificultat. Són
  personals i locals: comparar-te amb tu mateix en dialectes diferents no vol dir
  res.
- **La classificació, en canvi, NO es parteix.** Hi ha una taula per modalitat i
  prou, amb tothom qui hi ha jugat. El dialecte de cada intent surt entre
  parèntesis a la seva fila (`amb «bytownites» (Central)`). Quatre
  classificacions de quatre persones cadascuna no serien cap classificació.

Els codis no es declaren enlloc del joc: surten de `dades/versions.json`, que els
escriu el generador a partir de les carpetes de `dialectes_col/`. Els noms que es
veuen a la tira són el `NOMS_DE_DIALECTE` de `eines/generar_dades.py` i han de
coincidir amb el `DIALECTES` de `js/components.js`, que és el que pinta la tira
del cercador.

## Per què les dades són com són

El diccionari sencer fa 46 MB i 619.783 entrades. La web principal se'l carrega
tot a IndexedDB, però un joc no es pot permetre esperar això. La sortida d'aquí
es basa en dues observacions:

1. **La clau de rima consonant sempre implica la mateixa clau assonant**
   (el generador ho comprova a cada passada i s'atura si algun dia deixa de ser
   cert). O sigui que un sol fitxer per grup assonant serveix les dues
   dificultats: en fàcil valen totes les paraules del fitxer i en difícil només
   les de la secció de la paraula objectiu. **Una sola descàrrega per partida.**
2. **No cal cap llista de paraules objectiu.** Poden ser objectiu totes les
   paraules d'una clau consonant amb més de 50 rimes, i això ja se sap només
   amb l'índex. La tria és proporcional a la mida de cada grup, de manera que
   totes les paraules objectiu són igual de probables.

Resultat: **sis fitxers**, i el joc es baixa el dialecte sencer un sol cop.

```
joc/dades/versions.json   500 B    els resums
joc/dades/index.json      33 KB    les claus dels 4 dialectes + on és cada grup
joc/dades/ca.txt          7,6 MB   (1,9 MB comprimits, que és el que viatja)
joc/dades/nw.txt  va.txt  ba.txt
```

| dialecte | claus jugables | paraules objectiu | grups assonants |
|---|---|---|---|
| Central (`ca`) | 500 | 123.429 | 38 |
| Nord-occidental (`nw`) | 484 | 122.673 | 52 |
| Valencià (`va`) | 488 | 122.461 | 51 |
| Balear (`ba`) | 496 | 124.563 | 42 |

**Abans n'hi havia 183**, un per grup assonant i dialecte, perquè una partida
només necessita un grup. Sortia a 145 KB per partida —la mediana era de 11 KB,
però la tria és ponderada i els grups grossos surten més sovint—, i omplia el
repositori de fitxers que no mira mai ningú. Ara la primera partida paga 1,9 MB
i les següents no paguen res: **a partir de tretze ja s'hi guanya**.

El fitxer del dialecte es comença a baixar en obrir la pàgina, mentre tries mode
i rellotge, o sigui que quan prems «Comença» ja acostuma a ser-hi. Si encara no
hi és, surt un loader amb el percentatge de debò i una barra; si ja hi és, no
surt res, perquè preparar la partida són 90 ms.

### Què hi ha i què no

Del diccionari (619.783 entrades) en surten **470.479 formes úniques** un cop
tretes les repeticions d'accent. Fora en queden **14.705 noms propis**, que no
valen ni com a paraula a rimar ni com a resposta.

Al fitxer de cada dialecte hi arriba el **99,3–99,7 %** d'aquelles formes. El que
falta són entre 1.500 i 3.500 paraules per dialecte: les que cauen en un grup
assonant on **cap** clau consonant arriba a 50 rimes (*abutilon*, *acantolisi*,
*acefala*…). Són finals raríssims i no es publiquen perquè no s'hi podria jugar
de cap manera.

Per a una partida concreta, en canvi, **no falta cap rima**: el grup assonant
sencer va al fitxer, seccions no jugables incloses, o sigui que tot el que rima
amb la paraula que t'ha tocat hi és.

De les 470.479 formes, poden **sortir com a paraula a rimar** unes 123.000 per
dialecte: la resta són verbs (exclosos a posta), o són en claus amb menys de 50
rimes. I hi ha un centenar de claus amb prou rimes que només contenen verbs: hi
són al fitxer i valen com a resposta, però no poden ser mai la paraula objectiu.

`joc/dades/` continua fent 30 MB al repositori. La por que un fitxer derivat
s'hagi de tornar a pujar sencer a cada canvi (el motiu pel qual es va esborrar
`bot/resultat_ordenat_cons.json`) aquí no s'aplica: està mesurat que dues
versions del fitxer amb una paraula de diferència empaqueten a 1,93 MiB en
total, perquè el git fa deltes molt bé amb text ordenat de manera estable.

### Format dels fitxers de rimes

```
#aðə              <- capçalera de secció: clau de rima consonant
*cascada          <- l'* marca les paraules que poden ser OBJECTIU (no verbs)
cavalcava         <- sense *, només val com a RIMA (aquí, una forma verbal)
*cami>camí        <- si la forma real porta accents, va després del ">"
```

Els grups assonants van l'un darrere l'altre dins el fitxer del dialecte.

Com que la part esquerra ja és la clau normalitzada, el joc no ha de normalitzar
res en temps d'execució: només parteix línies. L'`*` li diu de seguida quines
paraules pot proposar com a objectiu (les que no són verbs) i quines només
accepta com a rima.

L'`index.json` guarda dues coses per dialecte: de cada clau jugable, a quin grup
és i quantes paraules objectiu té (el pes amb què es tria, així totes són igual
de probables); i de cada grup, **on comença i quant ocupa, en bytes**. Això
últim és el que permet al joc no interpretar els 7,6 MB per jugar amb un grup:
es guarda el fitxer com a `ArrayBuffer` i només descodifica el tros que li toca.
El pitjor cas mesurat —el grup més gros del central, 77.000 paraules— són 90 ms.

Els desplaçaments són en **bytes** i no en caràcters a posta: un índex de Python
són punts de codi i un de JavaScript són unitats UTF-16, i amb IPA pel mig no val
la pena jugar-s'hi.

## Regenerar les dades

Cal fer-ho a mà quan canviï el diccionari o la transcripció d'algun dialecte:

```bash
python joc/eines/generar_dades.py            # tots els dialectes
python joc/eines/generar_dades.py ca va      # només aquests
```

Els camins no els sap l'script: surten de `diccionaris/python/camins.py`, que és
el vocabulari compartit de tots els scripts del repositori. Llegeix la `col_0` i
la `col_2` de `diccionaris/separat/` i la rima de `dialectes_col/<codi>/`, i
reescriu `joc/dades/`. Triga uns 40 segons per als quatre dialectes.

Els paràmetres (rimes mínimes, si els verbs conjugats poden ser objectiu, com es
diu cada dialecte) són constants a dalt de tot de l'script. Els fitxers que no
canvien no es reescriuen, o sigui que una passada sense canvis al diccionari no
deixa cap diff.

**Important:** si es regeneren les dades, la paraula del dia d'aquell dia pot
canviar per a qui encara no l'hagi jugada, perquè la tria depèn de l'ordre i dels
pesos de l'índex. Val més fer-ho de nit.

## La gestió de versions

És **la mateixa que la del diccionari**, i val tant per a les dades com per al
codi.

**Les dades** van amb resum de contingut. `generar_dades.py` escriu
`dades/versions.json` amb un sha256 escurçat de cada fitxer, igual que fa
`diccionaris/python/versions.py` amb les columnes. El joc es baixa el
`versions.json` sense memòria cau (`?t=`) i tota la resta amb `?v=<resum>`, o
sigui que cada fitxer es torna a baixar exactament quan ha canviat i mai més.
Si el `versions.json` no es pot llegir, es fan servir els resums de l'última
vegada (desats al `localStorage`), que és el mateix rescat que fa el
`carregarVersions` de `js/script.js`.

A diferència del `versions.json` del diccionari, aquí les claus són **camins** i
no noms de fitxer sols: allà el navegador indexa la memòria cau pel nom
(`rutaFitxer.split("/").pop()`) i cada fitxer és únic, però aquí el
`ca/rimes/0.txt` i el `va/rimes/0.txt` es dirien igual.

**El codi** va amb el `?v=` de sempre, el que escriu el `deploy.yml` amb els set
primers caràcters del commit. Ara `joc/` hi entra com l'arrel: tocar
`joc/js/*.js` o `joc/css/*.scss` dispara el refresc, i el `sed` no escriu només
als HTML sinó també **a les importacions entre mòduls** (`from './ui.js?v=...'`).
Sense això, refrescar `principal.js` deixava els altres vuit mòduls a la memòria
cau del navegador, perquè una importació no hereta el `?v=` de l'etiqueta
`<script>` que va carregar el primer. El `?v=dev` que hi ha al repositori és el
valor de treball: el desplegament el substitueix.

## Classificació (leaderboard)

Funciona igual que el registre de cerques de la web: el navegador envia la
puntuació a un Google Apps Script, que l'apunta a un full de càlcul; un script de
Python llegeix el full publicat en CSV i en fa el rànquing que es veu al joc.

Fitxers:

```
joc/js/classificacio.js                  enviar la puntuació + llegir el rànquing
joc/eines/apps_script_classificacio.gs   codi per enganxar a Google Apps Script
joc/eines/compilar_classificacio.py      full CSV -> joc/dades/classificacio.json
joc/dades/classificacio.json             el rànquing que mostra el joc
```

### Posar-la en marxa (un sol cop)

1. Crea un full de càlcul a Google Sheets amb aquestes capçaleres a la fila 1:

   `Data | DataPartida | Sobrenom | Mode | Dificultat | Segons | Dialecte | Punts | Paraula | Usuari`

   Hi ha **dues dates** a posta: la `Data` és quan va arribar l'enviament (la
   posa Google) i la `DataPartida` de quin dia era la partida (la diu el
   navegador). Qui juga la paraula del dia a les 23.55 i l'envia a les 00.05 ha
   jugat la d'ahir, i el rànquing per dia ha d'agrupar per la segona.
2. Extensions → Apps Script → enganxa-hi `eines/apps_script_classificacio.gs`.
   Desplega'l com a aplicació web (accés: qualsevol) i copia l'URL `/exec`.
3. Posa aquell URL a `URL_ENVIAMENT` de `joc/js/classificacio.js`.
4. Publica el full en CSV (Fitxer → Comparteix → Publica a la web → CSV) i posa
   aquell URL a `URL_FULL_CSV` de `joc/eines/compilar_classificacio.py`.

> Si el full ve d'abans que el joc tingués dialectes, afegeix-hi les columnes
> `DataPartida` i `Dialecte` a les posicions de dalt. El compilador no perd les
> files velles: les que no les duguin es donen per centrals i pel dia que van
> arribar.

Les puntuacions **s'envien des d'on sigui**: de `rimador.cat`, del repositori de
proves i de `localhost`. El registre de cerques de la web no ho fa (vegeu
`ES_WEB_OFICIAL` a `js/script.js`, que només deixa passar els dos dominis de
debò), però aquí és a posta: una classificació que no deixa enviar res mentre la
proves no es pot provar.

El preu és que les partides de prova van al full de debò. Qui filtra de veritat és
el compilador: si un dia hi ha soroll, s'esborra la fila del full o s'afina allà,
que és on es pot fer sense deixar el joc coix mentre s'hi treballa.

### Refrescar el rànquing

**L'actualització és automàtica**: cada dia a les 22:01 UTC, el workflow
`.github/workflows/classificacio.yml` executa `joc/eines/compilar_classificacio.py`,
que llegeix el full, valida els sobrenoms, es queda la millor puntuació de cada
persona i modalitat, i reescriu `joc/dades/classificacio.json`.

Per **forçar una actualització manual** (p. ex., si has esborrat una fila del full):

- **Des de GitHub** → Actions → «Actualització automàtica de la classificació del
  joc» → «Run workflow».
- **Des de local**:
  ```bash
  python joc/eines/compilar_classificacio.py
  ```
  (Necessita `pandas`: `pip install pandas`, igual que `stats/stats.py`.)

En surten tres coses: el rànquing de cada **modalitat**
(`mode|dificultat|segons`), el de cada **dia** de la paraula del dia i el dels
**millors de sempre** a la paraula del dia (`TOP_DIARIA`, ara 10), els dos
últims per dificultat. Es veuen a les dues pestanyes de la pantalla de
classificació: la d'**Il·limitat** només ensenya les modalitats `illimitat|…`, i
la de **Paraula del dia**, les altres dues taules.

El dialecte **es guarda al full i viatja amb cada entrada**, però no parteix cap
taula: el joc el posa entre parèntesis a cada fila. Els noms (*Central*,
*Valencià*…) no són al JSON, que hi porta el codi: els tradueix el joc amb el que
digui el `versions.json`, per dir-los en un sol lloc.

## Estructura

```
joc/
  index.html            totes les pantalles, amagades amb l'atribut hidden
  css/joc.scss          estètica rosa/cian dels 90, disseny mòbil primer;
                        el gulp en fa dist/css/joc.min.css
  js/
    principal.js        lliga pantalles, motor i dades
    dades.js            versions, descàrrega i lectura dels fitxers de rimes
    dialecte.js         quin dialecte es juga (comparteix memòria amb el cercador)
    objectius.js        tria de la paraula (a l'atzar o la del dia)
    motor.js            rellotge, validació i puntuació (no toca el DOM)
    normalitza.js       accents fora; ha de coincidir amb el generador
    ui.js               tot el que toca el DOM
    magatzem.js         localStorage: rècords, paraula del dia i sobrenom
    compartir.js        graella d'emojis i porta-retalls
    classificacio.js    enviar/llegir el rànquing global
  dades/                generat pels scripts d'eines/
    versions.json         quins dialectes hi ha i el resum de cada fitxer
    index.json            les claus dels 4 dialectes i on és cada grup
    <codi>.txt            totes les rimes d'un dialecte
    classificacio.json    el rànquing publicat
  eines/
    generar_dades.py            diccionari + rima -> dades/
    compilar_classificacio.py   full CSV -> classificacio.json
    apps_script_classificacio.gs  backend per a Google Apps Script
```

El JS són mòduls ES natius i no passen per cap procés de compilació: el navegador
se'ls carrega tal com són. El CSS sí que es compila (vegeu la tasca `styles-joc`
del `gulpfile.js`), o sigui que l'`index.html` no apunta a `css/joc.scss` sinó a
`../dist/css/joc.min.css`.

## Coses que convé saber

- **La paraula del dia** surt d'un generador pseudoaleatori sembrat amb la data i
  el dialecte (mulberry32 + hash tipus cyrb53). No hi ha servidor: tothom calcula
  la mateixa paraula a partir del mateix índex. La dificultat no entra a la
  llavor, o sigui que la paraula és la mateixa tant si la jugues en fàcil com en
  difícil.
- **El bloqueig diari** es guarda a `localStorage`, amb un sol dia desat cada
  vegada: quan canvia la data, l'entrada vella se substitueix. Va per dialecte,
  perquè cada dialecte té la seva paraula.
- **Els rècords** van per mode, dificultat, rellotge i dialecte
  (`illimitat|dificil|45|va`) i es veuen a la pantalla "Els meus rècords". Els
  que hi hagués d'abans dels dialectes es migren al central el primer cop que
  s'obre el joc.
- **La classificació** es pot enviar en qualsevol partida amb un sobrenom; la
  validació de veritat (les paraules vetades, la desduplicació) la fa el
  compilador de Python.
- Si el `localStorage` no hi és (navegació privada), el joc funciona igual;
  simplement no recorda res.
