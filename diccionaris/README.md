# `diccionaris/` — quin diccionari es publica

Hi ha **dos** diccionaris i és important no confondre'ls.

| | qui l'escriu | per a què serveix |
|---|---|---|
| `diccionari.5.2.3.txt` | **tu, a mà** | l'origen de tot: quines paraules hi ha. D'aquí surt la columna 10 i d'aquí parteixen les formes amb pronom |
| `diccionari.6.txt` | el workflow | el base + les 3.406.083 formes verb+pronom. És el que es publica |

**El diccionari són set camps, no deu.** Ni la rima consonant, ni l'assonant, ni
la transcripció no hi són: depenen del dialecte i viuen a `dialectes_col/`, amb
un `col_9` per dialecte i la rima que se'n deriva al costat.

| camp | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|---|
| | paraula | lema | codi | síl·labes | Vicc | Viq | Diec |
| columna | `col_0` | `col_1` | `col_2` | `col_5` | `col_6` | `col_7` | `col_8` |

Els números de columna són els de sempre i hi ha forats (3, 4 i 9): el
navegador, les llistes i el joc les demanen pel nom del fitxer, i renumerar-les
voldria dir tocar-ho tot per no guanyar res.

El navegador no llegeix mai cap `diccionari*.txt`: llegeix `separat/col_0..col_8`,
`separat/internat/`, les internades del dialecte que serveixi
(`dialectes_col/<codi>/internat/`) i `versions.json` (vegeu
`llegirFitxerAmbIndexedDB` a `js/script.js`). **Aquestes columnes són les del
diccionari publicat.**

## L'interruptor

`python/config.py`, una línia:

```python
DICCIONARI_PUBLICAT = "diccionari.6.txt"      # amb formes amb pronom (ara)
DICCIONARI_PUBLICAT = DICCIONARI_BASE         # el de sempre, sense pronoms
```

No cal tocar res més:

* **base** → no es generen ni les formes amb pronom ni el `diccionari.6.txt`, i
  les columnes surten del 5.2.3.
* **v.6** → es generen les formes amb pronom, se'n fa el `diccionari.6.txt` i
  les columnes surten d'ell.

En tots dos casos es fan les columnes internades, el `versions.json` i les
llistes: aquests passos no miren quin diccionari hi ha al darrere.

## L'ordre, i per què és aquest

Hi ha **dues portes** i cadascuna edita una cosa diferent:

| edites | per a | i llavors |
|---|---|---|
| `diccionari.5.2.3.txt` | afegir i treure paraules, i canviar-ne el lema, el codi, les síl·labes o els enllaços | els dialectes el segueixen: el que hi esborres desapareix de tots els `col_9` |
| `col_10.txt` | corregir com sona una paraula, als quatre dialectes alhora | les transcripcions se'n van a `dialectes_col/*/col_9` |

```
canvi a diccionari.5.2.3.txt          canvi a diccionaris/col_10.txt
(quines paraules hi ha)               (com sonen)
         └────────────────┬─────────────────────┘
                          ▼
                   sincronitzar.py
       (alinea la col_10 amb el diccionari i escriu els col_9;
        el que s'ha esborrat del diccionari desapareix de tots
        els dialectes, i s'atura si hi ha paraules noves que la
        col_10 no sap com sonen)
                          ▼
                          │   ── si config.py publica el v.6: ──
                          ▼
              generar_tot_1_pronom + generar_tot_2_pronoms
              ajuntar_diccionari_6  →  diccionari.6.txt
                          │
                          │   ── sempre: ──
                          ▼
              generar_columnes_publicades  →  separat/col_0,1,2,5,6,7,8
                          ▼
              generar_dialectes  →  dialectes_col/*/col_3 i col_4
                          ▼
              internades + versions.json + col_10  →  UN SOL COMMIT
                          ▼
              nàufragues i mots de 7      (job a part)
                          ▼
                       deploy
```

Les dues portes van al mateix lloc, o sigui que **hi ha un sol workflow**
(`.github/workflows/diccionaris.yml`): el pas que escriu els col_9 no
necessita saber quina de les dues s'ha tocat.

Cinc coses que semblen rares i no ho són:

* **Ningú no fa les columnes del diccionari base.** No existeixen. El
  `generar_columnes_publicades.py` és l'únic que escriu `col_0,1,2,5,6,7,8`, i
  les fa del diccionari que digui `config.py`.
* **La rima no s'edita mai.** Se'n deriva de la transcripció, i el càlcul és en
  un sol lloc (`generar_dialectes.py`). Abans era escrit dues vegades, en dos
  scripts diferents, amb un comentari a cada banda demanant que no divergissin.
* **La col_10 no afegeix ni treu paraules tota sola.** Els tres camps del
  davant hi són per a saber de quina paraula parla cada línia, i qui mana és el
  diccionari: si una paraula hi és i a la col_10 no, això s'atura, perquè no hi
  ha manera d'endevinar com sona.
* **La col_10 és també el registre de què hi ha a cada col_9.** És l'única
  manera de saber quines files s'han esborrat del diccionari: les
  transcripcions van per número de fila i no porten cap paraula a dins.
  Mirar-ho amb `git show HEAD` semblava més directe i no ho és: als workflows,
  el commit que dispara l'execució JA és HEAD, i la comparació sempre hauria
  sortit igual.
* **Tot va en un sol job.** Un workflow reutilitzable a part tindria el seu
  propi workspace i no veuria ni el diccionari base acabat de refer ni el
  `diccionari.6.txt`, que no es comiteja. Per això el tram compartit és una
  acció composta (`.github/actions/publicar-diccionari/`).

## El diàleg d'homògrafs

Quan cerques una paraula que surt més d'un cop al diccionari, el web ha de
decidir si les entrades rimen totes igual (i tant se val quina agafi) o no (i
t'ho pregunta amb el diàleg d'homògrafs). Abans això calia esbrinar-ho amb la
`col_9` (les transcripcions senceres): amb el diccionari base ja eren 9,8 MB
per respondre un sí o un no, i amb el publicat són **73 MB i quatre milions de
línies**, prou per deixar el navegador penjat amb el loader en cercar
qualsevol paraula repetida. Per això hi va haver un `homografs.txt` intermedi
amb només les files discrepants.

Ara no cal cap fitxer a part: la cerca ja té carregades `col_3.idx` (rima
consonant) i `col_4.idx` (rima assonant) per fer la cerca de rimes, i n'hi ha
prou de mirar-hi el número de rima de cada entrada (segons `tipusRima`). Si
totes les entrades tenen el mateix número, rimen amb les mateixes paraules i
tant se val quina s'agafi; si no, es demana (vegeu `buscarParaula` a
`js/script.js`).

Com que ja no la demana ningú, la transcripció no s'acosta al paquet que es
publica a Pages. Al repositori s'hi queda, a `dialectes_col/<codi>/`: és la
font de la rima i d'ella surten les llistes de mots de 7.

## Aturat de moment

`bot/resultat_ordenat_cons.json` (el json de rimes sencer) **ja no es genera**:
els seus dos passos són comentats a `.github/workflows/generar_llistes.yml`.
Només el llegeix el bot de Twitter, que tampoc no corre. Les nàufragues ja no
en depenen: es compten soles des de la `col_0` i la `col_3`.

> ⚠️ Si tornes a engegar el bot, recorda que el json que hi ha al repositori és
> del diccionari base i no del publicat.

## El que costa publicar el v.6

| | base | v.6 |
|---|---|---|
| files | 619.783 | 4.025.866 |
| `separat/col_0..col_8` | 25,7 MB | ~170 MB |
| `dialectes_col/` (quatre dialectes) | 68 MB | per fer: cada forma amb pronom hauria de portar la seva transcripció a cada dialecte |
| `col_10.txt` | **76,3 MB** | no hi cabria |
| baixada real (Pages comprimeix) | 2,9 MB | ~20 MB |
| `bot/resultat_ordenat_cons.json` | 16,9 MB | 76,2 MB |

⚠️ **La `col_10.txt` a 76,3 MB va just.** GitHub avisa als 50 MB i **bloqueja
als 100**: quan el diccionari creixi un 30 % més (o quan s'hi afegeixi un
cinquè dialecte), el push serà rebutjat. Llavors caldrà partir-la, i la manera
natural és un fitxer per dialecte: uns 20 MB cadascun, i el `col_10.py` és
l'únic que s'hi ha de tocar.
