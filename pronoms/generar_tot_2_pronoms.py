"""
Genera totes les combinacions verb + 2 pronoms febles, en el format de
diccionari.5.2.3.txt (10 camps separats per '$').

    python3 generar_tot_2_pronoms.py             # les 69 parelles vàlides
    python3 generar_tot_2_pronoms.py li:el es:hi  # només aquestes ("p1:p2")

NO toca el diccionari de producció: escriu el seu propi fitxer.

Mateix repartiment de feina que generar_tot_1_pronom.py:
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

DIR_SEPARAT = os.path.join(BASE_DIR, "..", "diccionaris", "separat")

# Un fitxer per parella: verb_pronom_li_el.txt, verb_pronom_es_hi.txt...
DIR_SORTIDA = os.path.join(BASE_DIR, "txt_fets", "2_pronoms")
PATRO_SORTIDA = "verb_pronom_{p1}_{p2}.txt"

PARELLES = llicencies.PARELLES_VALIDES

# Mateix mapa que generar_tot_1_pronom.py (pla_un_pronom.md §3.2).
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
    """Mateixa xarxa de seguretat que generar_tot_1_pronom.py."""
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


def generar(parelles=PARELLES, dir_sortida=DIR_SORTIDA):
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
