"""
Genera totes les combinacions verb + 1 pronom feble, en el format de
diccionari.5.2.3.txt (10 camps separats per '$').

    python3 generar_tot_1_pronom.py            # els 13 pronoms
    python3 generar_tot_1_pronom.py hi en ho   # només aquests
    python3 generar_tot_1_pronom.py --tots     # els 13, explícit (equival a no passar res)

NO toca el diccionari de producció: escriu el seu propi fitxer.

Reparteix la feina entre dos mòduls:
    llicencies.py  -> quins verbs admeten quin pronom, i quines persones
    enclisi.py     -> com s'escriu, com sona, quantes síl·labes i quina rima fa
"""

import os
import sys
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import enclisi
import llicencies

# El nom del diccionari base surt de config.py, que és l'únic lloc del
# repositori que diu quin diccionari és quin.
# .parent perquè aquest fitxer viu a pronoms/python/.
PRONOMS_DIR = os.path.dirname(BASE_DIR)
sys.path.insert(0, os.path.join(PRONOMS_DIR, "..", "diccionaris", "python"))
import config

CAMPS = 10

# Un fitxer per pronom: verb_pronom_hi.txt, verb_pronom_en.txt...
DIR_SORTIDA = os.path.join(PRONOMS_DIR, "txt_fets", "1_pronom")
PATRO_SORTIDA = "verb_pronom_{pronom}.txt"

# Per defecte, els 13 pronoms (enclisi.ORDRE_PRONOMS). La validació contra els
# scripts vells (pla_un_pronom.md, pas 4) ja es va fer i és a done/1a versio/.
PRONOMS = enclisi.ORDRE_PRONOMS

# Codi EAGLES del diccionari -> (forma verbal, persona)
# Les 14 etiquetes d'imperatiu es fonen en 5 persones; el sufix 'Y' només marca
# homografia amb una altra cel·la del paradigma i la 'X' marca 1a conjugació:
# cap de les dues no canvia la persona (pla_un_pronom.md §3.2).
#
# La 2a lletra és el TIPUS de verb, no la forma: M principal, S semiauxiliar
# (ser/ésser) i A auxiliar (haver). L'imperatiu ja duia les tres files 'VSM…',
# però l'infinitiu i el gerundi només tenien la principal, i per això 'ser',
# 'ésser', 'sent', 'essent', 'haver' i 'havent' no generaven res: hi faltaven
# 'haver-hi' i 'ser-hi', que són de les formes amb pronom més freqüents que hi ha.
FORMES = {
    "VMN00000": ("N", None), "VSN00000": ("N", None), "VAN00000": ("N", None),
    "VMG00000": ("G", None), "VSG00000": ("G", None), "VAG00000": ("G", None),
    "VMM02S00": ("M", "02S"), "VMM02S0Y": ("M", "02S"), "VSM02S00": ("M", "02S"),
    "VMM01P00": ("M", "01P"), "VSM01P00": ("M", "01P"),
    "VMM02P0X": ("M", "02P"), "VMM02P00": ("M", "02P"), "VSM02P00": ("M", "02P"),
    "VMM03S0Y": ("M", "03S"), "VMM03S00": ("M", "03S"), "VSM03S0Y": ("M", "03S"),
    "VMM03P0Y": ("M", "03P"), "VMM03P00": ("M", "03P"), "VSM03P0Y": ("M", "03P"),
}

NOM_FORMA = {"N": "infinitiu", "G": "gerundi", "M": "imperatiu"}


def llegir_columnes():
    """
    Els deu camps del diccionari BASE, cada un en una llista.

    Es llegeix del diccionari i no pas de diccionaris/separat/col_*.txt, que és
    d'on sortien abans. Les columnes de separat/ són les del diccionari
    PUBLICAT, que pot ser el v.6: partir-ne seria fer pronoms de formes que ja
    en duen. I les columnes del base ja no existeixen enlloc, perquè eren un
    pas intermedi que no servia per a res més que això.
    """
    col = {n: [] for n in range(CAMPS)}
    with open(config.CAMI_BASE, "r", encoding="utf-8") as f:
        for numero, linia in enumerate(f, 1):
            linia = linia.rstrip("\n")
            if not linia:
                continue
            camps = linia.split("$")
            if len(camps) != CAMPS:
                raise SystemExit(
                    f"{config.DICCIONARI_BASE}, línia {numero}: hi ha "
                    f"{len(camps)} camps i n'hi ha d'haver {CAMPS}."
                )
            for n in range(CAMPS):
                col[n].append(camps[n])
    if not col[0]:
        raise SystemExit(f"{config.CAMI_BASE} és buit.")
    return col


def comprovar_base(col):
    """
    El càlcul de la rima agafa tot el que va DARRERE de l'últim accent primari.
    Si una forma base en porta dos (contaminació de la transcripció, com la que
    hi havia a 'desment' o 'prement'), la rima surt malament i en silenci.
    Els compostos amb guionet propi ('pèl-mudar') en poden portar dos de bons.
    """
    dolents = []
    for i in range(len(col[0])):
        if col[2][i] not in FORMES:
            continue
        if not col[0][i] or not col[9][i] or not col[5][i].isdigit():
            dolents.append((col[0][i], "camp buit o síl·labes no numèriques"))
        elif col[9][i].count("ˈ") > 1 and "-" not in col[0][i]:
            dolents.append((col[0][i], f"{col[9][i]} té 2 accents primaris"))
    if dolents:
        mostra = ", ".join(f"{f} ({m})" for f, m in dolents[:6])
        raise SystemExit(
            f"Hi ha {len(dolents)} formes base amb la transcripció sospitosa: {mostra}"
            f"{'...' if len(dolents) > 6 else ''}\n"
            "Corregeix-les a col_10 abans de generar res."
        )


def generar(pronoms=PRONOMS, dir_sortida=DIR_SORTIDA):
    # La carpeta de sortida és .gitignore: en un clon net (o al runner
    # del workflow) pot no existir, i l'open() de més avall petaria.
    os.makedirs(dir_sortida, exist_ok=True)
    col = llegir_columnes()
    comprovar_base(col)

    linies = {pronom: [] for pronom in pronoms}
    per_forma = Counter()
    descartades = Counter()

    for i in range(len(col[0])):
        info = FORMES.get(col[2][i])
        if info is None:
            continue
        forma_verbal, persona = info
        forma, lema, silabes, transcripcio = col[0][i], col[1][i], col[5][i], col[9][i]

        for pronom in pronoms:
            if not llicencies.permet(lema, pronom, persona):
                if pronom in llicencies.pronoms_permesos(lema):
                    descartades["concordança"] += 1        # el verb l'admet, la persona no
                else:
                    descartades[llicencies.classe(lema)] += 1
                continue

            r = enclisi.generar_forma(forma, transcripcio, silabes,
                                      [pronom], forma_verbal, persona)
            linies[pronom].append("$".join([
                r["paraula"],            # 0 paraula
                lema,                    # 1 d'on ve (el lema del verb)
                r["codi"],               # 2 codi
                r["rima_consonant"],     # 3 rima consonant
                r["rima_assonant"],      # 4 rima assonant
                str(r["silabes"]),       # 5 síl·labes
                col[6][i],               # 6 Vicc   ) hereten els del verb: els
                col[7][i],               # 7 Viq    ) enllaços de la UI apunten
                col[8][i],               # 8 Diec   ) al lema (col_1)
                r["transcripcio"],       # 9 transcripció
            ]))
            per_forma[forma_verbal] += 1

    fitxers = {}
    for pronom in pronoms:
        ruta = os.path.join(dir_sortida, PATRO_SORTIDA.format(pronom=pronom))
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("\n".join(linies[pronom]) + "\n" if linies[pronom] else "")
        fitxers[pronom] = ruta

    return linies, fitxers, per_forma, descartades


def main():
    args = [a for a in sys.argv[1:] if a != "--tots"]
    if args:
        desconeguts = [a for a in args if a not in enclisi.ENCLISI]
        if desconeguts:
            raise SystemExit(f"Pronoms desconeguts: {', '.join(desconeguts)}\n"
                             f"Disponibles: {', '.join(enclisi.ORDRE_PRONOMS)}")
        pronoms = tuple(a for a in enclisi.ORDRE_PRONOMS if a in args)
    else:
        pronoms = tuple(PRONOMS)

    linies, fitxers, per_forma, descartades = generar(pronoms)

    total = sum(len(v) for v in linies.values())
    print(f"Fet! {total:,} línies en {len(fitxers)} fitxers\n")
    print(f"  {'fitxer':28s} {'línies':>9s} {'mida':>8s}")
    for p in pronoms:
        mida = os.path.getsize(fitxers[p]) / 1e6
        print(f"  {os.path.basename(fitxers[p]):28s} {len(linies[p]):9,} {mida:7.1f} MB")

    print("\n  per forma verbal:")
    for f in ("N", "G", "M"):
        if per_forma[f]:
            print(f"    {NOM_FORMA[f]:11s} {per_forma[f]:9,}")

    print(f"\n  descartades: {sum(descartades.values()):,}")
    for motiu, n in descartades.most_common():
        print(f"    {motiu:14s} {n:9,}")


if __name__ == "__main__":
    main()
