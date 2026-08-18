# `diccionaris/` — quin diccionari es publica

Hi ha **dos** diccionaris i és important no confondre'ls.

| | qui l'escriu | per a què serveix |
|---|---|---|
| `diccionari.5.2.3.txt` | **tu, a mà** | l'origen de tot: d'aquí surt la columna 10 i d'aquí parteixen les formes amb pronom |
| `diccionari.6.txt` | el workflow | el base + les 3.406.083 formes verb+pronom. És el que es publica |

El navegador no llegeix mai cap `diccionari*.txt`: llegeix `separat/col_0..col_9`,
`separat/internat/` i `versions.json` (vegeu `llegirFitxerAmbIndexedDB` a
`js/script.js`). **Aquestes columnes són les del diccionari publicat.**

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

```
canvi a "col_10 (canvis aquí)"          canvi a diccionari.5.2.3.txt
         │                                       │
   pre_procés                              separar_arxiu
   creador_rima  → diccionari base        (→ NOMÉS la columna 10,
   post_procés   → columna 10                 + post_procés a dins)
         └───────────────┬───────────────────────┘
                         ▼
              diccionari.5.2.3.txt  i  "col_10 (canvis aquí)"
                         │
                         │   ── si config.py publica el v.6: ──
                         ▼
              generar_tot_1_pronom + generar_tot_2_pronoms
              (llegeixen el diccionari base, no cap columna)
                         ▼
              ajuntar_diccionari_6  →  diccionari.6.txt
                         │
                         │   ── sempre: ──
                         ▼
              generar_columnes_publicades  →  separat/col_0..col_9
                         ▼
              internades + versions.json  →  UN SOL COMMIT
                         ▼
              nàufragues i mots de 7      (job a part)
                         ▼
                      deploy
```

Quatre coses que semblen rares i no ho són:

* **Ningú no fa les columnes del diccionari base.** No existeixen. El
  `generar_columnes_publicades.py` és l'únic que escriu `col_0..col_9`, i les
  fa del diccionari que digui `config.py`. Abans el `separar_arxiu` i el
  `creador_rima` també les escrivien i tot seguit es reescrivien: 42 MB per res.
* **La columna 10 surt del diccionari BASE, no del publicat.** Si sortís del
  v.6 tindria quatre milions de línies en cinc-cents fitxers i deixaria de
  servir per a editar-hi res.
* **El `creador_rima` no regenera les síl·labes ni els enllaços** (camps 5 a 8):
  els pren del diccionari base d'abans, fila per fila. Si a la columna 10 hi
  afegeixes o en treus una línia, tot es desplaçaria; per això comprova que les
  dues mides quadrin i s'atura si no.
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

Com que ja no la demana ningú, la `col_9.txt` s'esborra del paquet que es
publica a Pages (al repositori s'hi queda: d'ella surten les llistes de mots
de 7).

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
| `separat/col_0..col_9` | 41,6 MB | **323,6 MB** |
| fitxer més gros (`col_9.txt`) | 9,8 MB | **72,9 MB** |
| baixada real (Pages comprimeix) | 2,9 MB | ~20 MB |
| `bot/resultat_ordenat_cons.json` | 16,9 MB | 76,2 MB |

⚠️ **El `col_9.txt` a 72,9 MB va just.** GitHub avisa als 50 MB i **bloqueja
als 100**: quan el diccionari creixi un 35 % més, el push serà rebutjat i
caldrà partir les columnes en trossos, com ja es fa amb la columna 10.
