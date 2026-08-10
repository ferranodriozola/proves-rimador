"""
Genera totes les combinacions verb + 1 pronom feble, en el format de
diccionari.5.2.3.txt (10 camps separats per '$').

    python3 generar_tot.py            # els pronoms de PRONOMS (avui: hi, en)
    python3 generar_tot.py hi en ho   # només aquests
    python3 generar_tot.py --tots     # els 13

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

DIR_SEPARAT = os.path.join(BASE_DIR, "..", "diccionaris", "separat")

# Un fitxer per pronom: verb_pronom_hi.txt, verb_pronom_en.txt...
DIR_SORTIDA = BASE_DIR
PATRO_SORTIDA = "verb_pronom_{pronom}.txt"

# Pas 4 del pla: de moment només 'hi' i 'en', per poder comparar la sortida
# amb la dels tres scripts vells abans d'obrir-ho a tot.
PRONOMS = ("hi", "en")

# Codi EAGLES del diccionari -> (forma verbal, persona)
# Les 14 etiquetes d'imperatiu es fonen en 5 persones; el sufix 'Y' només marca
# homografia amb una altra cel·la del paradigma i la 'X' marca 1a conjugació:
# cap de les dues no canvia la persona (pla_un_pronom.md §3.2).
FORMES = {
    "VMN00000": ("N", None),
    "VMG00000": ("G", None),
    "VMM02S00": ("M", "02S"), "VMM02S0Y": ("M", "02S"), "VSM02S00": ("M", "02S"),
    "VMM01P00": ("M", "01P"), "VSM01P00": ("M", "01P"),
    "VMM02P0X": ("M", "02P"), "VMM02P00": ("M", "02P"), "VSM02P00": ("M", "02P"),
    "VMM03S0Y": ("M", "03S"), "VMM03S00": ("M", "03S"), "VSM03S0Y": ("M", "03S"),
    "VMM03P0Y": ("M", "03P"), "VMM03P00": ("M", "03P"), "VSM03P0Y": ("M", "03P"),
}

NOM_FORMA = {"N": "infinitiu", "G": "gerundi", "M": "imperatiu"}


def llegir_columnes():
    col = {}
    for n in range(10):
        with open(os.path.join(DIR_SEPARAT, f"col_{n}.txt"), "r", encoding="utf-8") as f:
            col[n] = f.read().splitlines()
    mida = len(col[0])
    if any(len(col[n]) != mida for n in col):
        raise SystemExit("Les columnes no tenen el mateix nombre de línies: no es pot continuar.")
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
    args = [a for a in sys.argv[1:]]
    if args == ["--tots"]:
        pronoms = tuple(enclisi.ORDRE_PRONOMS)
    elif args:
        desconeguts = [a for a in args if a not in enclisi.ENCLISI]
        if desconeguts:
            raise SystemExit(f"Pronoms desconeguts: {', '.join(desconeguts)}\n"
                             f"Disponibles: {', '.join(enclisi.ORDRE_PRONOMS)}")
        pronoms = tuple(a for a in enclisi.ORDRE_PRONOMS if a in args)
    else:
        pronoms = PRONOMS

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
