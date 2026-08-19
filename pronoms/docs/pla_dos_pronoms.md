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
| Els pronominals **inherents** | Excepció a la unió (§5): el reflexiu va sempre primer i el 2n pronom és el que admetria un intransitiu — és el cas que `pla_un_pronom.md` §2.2 reservava per a aquesta fase (`penedir-se'n`) |
| Fonètica de les parelles | Els fragments d'AFI del quadre **més les 6 regles de sàndhi d'1 pronom**, aplicades als dos límits del grup (§2) |
| Arquitectura | Mateixos 3 mòduls que la fase d'1 pronom, ampliats: `llicencies.PARELLES`/`permet_parella`, `enclisi._generar_forma_2`, `generar_tot_2_pronoms.py` |

**Volum obtingut: 2.779.550 formes**, 69 fitxers, 234 MB.

> Xifra corregida: la generació original en va donar 2.779.304. La
> diferència són els 246 grups de `ser` i `haver` que hi faltaven i els
> 130.196 que van canviar de transcripció (vegeu «Correccions» al
> `README.md`).

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
  (fonema1, fonema2))`. La fonètica va **partida en els dos pronoms** a
  posta: és el que permet aplicar el sàndhi al límit que els separa. Quan la
  fila varia amb el verb, tots dos camps són parelles `(consonant, vocal)`.
- `parella_efectiva(p1, p2)`: resol la transformació `li`+CD → CD+`hi` i la
  distinció `els_dat`/`els_ac`; retorna la clau real a `PARELLES`.
- `PARELLES_VALIDES`: les 69 parelles, en ordre gramatical.
- `permet_parella(lema, p1, p2, persona)`: la **heurística d'unió** — la
  parella es permet si el verb admet cada membre per separat
  (`permet(lema, p, None)`), sense necessitat de dades noves de
  ditransitivitat. Amb persona donada, aplica la concordança existent
  (`MATRIU_PERSONA`) al membre que sigui `es`/`et`/`em`/`ens`/`us`.
- `_parella_inherent()` + `admet_cd()`: l'excepció dels pronominals
  inherents (§5).

### `enclisi.py`

`generar_forma()` deriva ara cap a `_generar_forma_2()` quan rep 2 pronoms:
busca la parella a `llicencies.PARELLES` (via `parella_efectiva`) i tria la
variant consonant/vocal si cal amb `acaba_en_vocal()` (la mateixa funció que
ja hi havia). L'**ortografia** surt d'allà literalment. La **fonètica** no:
els dos fragments d'AFI del quadre passen per les mateixes regles de sàndhi
que amb 1 pronom, ara als **dos** límits que té un grup de dos pronoms.

Perquè això fos possible, les regles de `transcriure()` s'han partit en tres
funcions reaprofitables:

| Funció | Regles | On s'aplica amb 2 pronoms |
|---|---|---|
| `_sensibilitzar()` | (1) `-r` d'infinitiu, (2) consonant muda de grup — les que necessiten la **grafia** | límit verb\|pronom1 |
| `_sandhi()` | (3) sonorització de `-s`, (4) espirantització de `-vos`, (5) assimilació de `-n` — només miren els **sons** | als **dos** límits |
| `_semivocal()` | (6) `-hi`/`-ho` en semivocal darrere vocal | final del grup |

```
cantar-los-els  /kəntˈarluzəls/   (1) la -r reapareix, (3) la -s de "los" sonoritza
digues-los-ho   /dˈiɣəzluzu/      (3) dues vegades: verb|pronom i pronom|pronom
cantant-me'l    /kəntˈamməl/      (5) la -n del gerundi assimila
canteu-vos-en   /kəntˈɛwβuzən/    (4) + (3)
porta-li-ho     /pˈɔrtəliw/       (6) igual que veure-hi /bˈɛwɾəj/
canta-s'hi      /kˈantəsi/        (3) NO s'hi aplica: la "s" de "-s'hi" obre síl·laba
```

La (3) demana un matís que amb 1 pronom no calia: només sonoritza una `-s`
de **coda**. Un fragment d'un sol so (`-s'hi`, `-t'ho`, `-l'hi`) és
l'obertura de la síl·laba següent, i per això `renta-s'hi` fa /rˈentəsi/ i
no *[zi]*, mentre que `porta'ls-hi` fa /pˈɔrtəlzi/.

Les síl·labes es compten com abans, pels nuclis vocàlics del que s'afegeix:
com que una semivocal no és un nucli, la regla (6) ja hi queda inclosa sense
excepcions (`porta-la-hi` = 3 síl·labes, com `porta-la`).

**El que continua sent una reconstrucció nostra** són els fragments de les
formes "nues" (`en`→`ən`, `el`→`əl`, `els`→`əls`, `em`→`əm`, `et`→`ət`,
`ens`→`əns`), que apareixen com a 2n pronom rere consonant: el quadre les
dona escrites, no transcrites. La resta són els fragments de `FONEMA`, que
ja estaven validats contra el diccionari amb 1 pronom.

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

`python3 pronoms/generar_tot_2_pronoms.py` → **69 fitxers, 2.779.550
línies, 234 MB.**

| Comprovació | Resultat |
|---|---|
| 10 camps per línia, codi de 10 caràcters | ✅ 0 excepcions |
| un sol accent primari per forma | ✅ 0 excepcions |
| `col_3` = tot el que va darrere l'accent, `col_4` = les seves vocals | ✅ 0 excepcions |
| col·lisions amb el diccionari base (`col_0.txt`) | ✅ 0 |
| files duplicades exactes | ✅ 0 |
| límit verb\|pronom idèntic al que dona el camí d'1 pronom | ✅ a les 2.779.550 |
| cua fonètica esperada per a cada parella | ⚠️ la comprovació no veia l'error de `li`+`la`: comparava contra una cua calculada igual de malament |
| casos de prova coneguts (`porta-l'hi`, `treu-l'en`, `renta-te-la`, `avisa'ns-hi`/`digues-nos-hi`, `anem-nos-en`, `ves-te'n`, `penedir-se'n`, `endur-se'l`) | ✅ tots coincideixen amb el Quadre 8.9 |

Repartiment per forma verbal: 521.079 infinitius, 516.761 gerundis,
1.741.710 imperatius. **1.489.825 combinacions descartades** per la
heurística d'unió o la concordança de persona. Són 373 codis diferents.

Per comparació: el diccionari actual (1 pronom inclòs) fa uns 90 MB en
columnes; aquests 234 MB nous confirmen que segueix fent falta un
**dataset separat, carregat sota demanda** (mateixa decisió de `pla.md`
§4.3).

---

## 4. Pendent

- **Integració al rimador** (Fase 3 de `pla.md`): segueix sense començar,
  tant per a 1 com per a 2 pronoms. És l'únic que queda.

---

## 5. Els pronominals inherents: l'excepció a la unió

La heurística d'unió, tal com està formulada a §0, no serveix per als 392
verbs **inherentment pronominals**: amb 1 pronom no n'admeten cap tret del
reflexiu (`penedir-ne` ❌, és correcte), i si demanem que el verb admeti
cada membre per separat, cap parella no hi passa mai. El resultat seria que
`penedir-se'n` no existiria — precisament la forma que `pla_un_pronom.md`
§2.2 posava com a exemple del que aquesta fase havia de recuperar, i que
§4 d'aquell mateix document ja donava codificada (`WN0002ESNE`).

La regla que hi aplica `_parella_inherent()`:

| | |
|---|---|
| 1r pronom | el **reflexiu** i prou. A l'imperatiu, el que concorda amb el subjecte (`REFLEXIU_EXACTE`, com amb 1 pronom): `penedeix-te'n` sí, `*penedeix-se'n` no |
| 2n pronom | el que admetria un intransitiu: datius, `hi` i `en` (`adonar-se'n`, `abalançar-s'hi`, `queixar-se-li`) |
| 2n pronom acusatiu | només si el DIEC dona alguna construcció `v. tr. pron.` — són **13** dels 392 (`endur-se'l`, `empassar-se-la`). Els altres 379 són `v. intr. pron.` i no tenen CD: `*penedir-se-la` |
| concordança | la matriu general (`MATRIU_PERSONA`) s'aplica al 2n pronom, que és un datiu, no el reflexiu: `*penedim-nos-em` |

Ho decideix `admet_cd(lema)`, que mira si alguna construcció del DIEC és
transitiva encara que sigui pronominal. Compte amb el detall: `"intr"`
conté `"tr"` com a substring, i per això la comprovació es fa sobre la
primera paraula de la construcció, no amb un `in`.

Aporta **27.628 formes** que abans no hi eren.
