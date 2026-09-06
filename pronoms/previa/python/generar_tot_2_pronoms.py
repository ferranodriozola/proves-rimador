"""
Genera totes les combinacions verb + 2 pronoms febles, en el format de
diccionari.5.2.3.txt (10 camps separats per '$').

    python3 generar_tot_2_pronoms.py             # les 69 parelles vàlides
    python3 generar_tot_2_pronoms.py li:el es:hi  # només aquestes ("p1:p2")

NO toca el diccionari de producció: escriu el seu propi fitxer.

Mateix repartiment de feina que generar_tot_1_pronom.py, del qual reaprofita
la lectura del diccionari base (FORMES, llegir_columnes, comprovar_base):
    llicencies.py  -> quines parelles existeixen (Quadre 8.9) i quin verb
                      les admet (heurística d'unió, pla_dos_pronoms.md)
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

# La lectura del diccionari base és exactament la mateixa que amb 1 pronom:
# s'importa, no es copia, perquè les dues sortides no puguin divergir mai
# (és la raó de ser de l'arquitectura de mòduls, pla_un_pronom.md §5).
from generar_tot_1_pronom import (FORMES, NOM_FORMA, comprovar_base,
                                  llegir_columnes)

# Un fitxer per parella: verb_pronom_li_el.txt, verb_pronom_es_hi.txt...
# .parent perquè aquest fitxer viu a pronoms/python/ i txt_fets/ és a pronoms/.
DIR_SORTIDA = os.path.join(os.path.dirname(BASE_DIR), "txt_fets", "2_pronoms")
PATRO_SORTIDA = "verb_pronom_{p1}_{p2}.txt"

PARELLES = llicencies.PARELLES_VALIDES


def generar(parelles=PARELLES, dir_sortida=DIR_SORTIDA):
    # La carpeta de sortida és .gitignore: en un clon net (o al runner
    # del workflow) pot no existir, i l'open() de més avall petaria.
    os.makedirs(dir_sortida, exist_ok=True)
    col = llegir_columnes()
    comprovar_base(col)

    linies = {par: [] for par in parelles}
    per_forma = Counter()
    descartades = Counter()

    for i in range(len(col[0])):
        info = FORMES.get(col[2][i])
        if info is None:
            continue
        forma_verbal, persona = info
        forma, lema, silabes, transcripcio = col[0][i], col[1][i], col[5][i], col[9][i]

        for (p1, p2) in parelles:
            if not llicencies.permet_parella(lema, p1, p2, persona):
                descartades["no permès"] += 1
                continue

            r = enclisi.generar_forma(forma, transcripcio, silabes,
                                      [p1, p2], forma_verbal, persona)
            linies[(p1, p2)].append("$".join([
                r["paraula"],
                lema,
                r["codi"],
                r["rima_consonant"],
                r["rima_assonant"],
                str(r["silabes"]),
                col[6][i],
                col[7][i],
                col[8][i],
                r["transcripcio"],
            ]))
            per_forma[forma_verbal] += 1

    fitxers = {}
    for par in parelles:
        p1, p2 = par
        ruta = os.path.join(dir_sortida, PATRO_SORTIDA.format(p1=p1, p2=p2))
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("\n".join(linies[par]) + "\n" if linies[par] else "")
        fitxers[par] = ruta

    return linies, fitxers, per_forma, descartades


def _parse_parella(text):
    if ":" not in text:
        raise SystemExit(f"Parella mal escrita: {text!r} (format p1:p2, p. ex. li:el)")
    p1, p2 = text.split(":", 1)
    if (p1, p2) not in PARELLES:
        raise SystemExit(f"Parella desconeguda: {p1}:{p2}\n"
                         f"Disponibles: {', '.join(f'{a}:{b}' for a, b in PARELLES)}")
    return (p1, p2)


def main():
    args = sys.argv[1:]
    parelles = tuple(_parse_parella(a) for a in args) if args else PARELLES

    linies, fitxers, per_forma, descartades = generar(parelles)

    total = sum(len(v) for v in linies.values())
    print(f"Fet! {total:,} línies en {len(fitxers)} fitxers\n")
    print(f"  {'fitxer':32s} {'línies':>9s} {'mida':>8s}")
    for par in parelles:
        mida = os.path.getsize(fitxers[par]) / 1e6
        print(f"  {os.path.basename(fitxers[par]):32s} {len(linies[par]):9,} {mida:7.1f} MB")

    print("\n  per forma verbal:")
    for f in ("N", "G", "M"):
        if per_forma[f]:
            print(f"    {NOM_FORMA[f]:11s} {per_forma[f]:9,}")

    print(f"\n  descartades: {sum(descartades.values()):,}")


if __name__ == "__main__":
    main()
