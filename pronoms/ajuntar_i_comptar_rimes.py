"""
Ajunta tots els .txt de txt_fets/ en un sol fitxer i compta quantes rimes
consonants diferents hi ha en tot el conjunt.

    python3 ajuntar_i_comptar_rimes.py                  # -> txt_fets/tot.txt
    python3 ajuntar_i_comptar_rimes.py /altre/lloc.txt  # un altre destí

Agafa els .txt de les SUBCARPETES de txt_fets/ (1_pronom/ i 2_pronoms/), o
sigui que el fitxer ajuntat, que va a txt_fets/ mateix, no s'hi torna a
incloure encara que es repeteixi la crida.

La rima consonant és el camp 3 dels 10 que té cada línia (tot el que va
darrere de l'últim accent primari de la transcripció); comptar-ne els valors
diferents és comptar les CLASSES DE RIMA que aporten aquestes formes.
"""

import os
import sys
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_TXT = os.path.join(BASE_DIR, "txt_fets")
FITXER_TOT = os.path.join(DIR_TXT, "tot.txt")

CAMPS = 10
COL_RIMA_CONSONANT = 3


def fitxers_font(sortida):
    """Els .txt de les subcarpetes de txt_fets/, en ordre i sense la sortida."""
    trobats = []
    for arrel, _, noms in os.walk(DIR_TXT):
        for nom in noms:
            ruta = os.path.join(arrel, nom)
            if nom.endswith(".txt") and os.path.abspath(ruta) != os.path.abspath(sortida):
                trobats.append(ruta)
    if not trobats:
        raise SystemExit(f"No hi ha cap .txt a {DIR_TXT}")
    return sorted(trobats)


def ajuntar(fitxers, sortida):
    """
    Copia els fitxers un darrere l'altre, en binari i a trossos (són 280 MB:
    no cal tenir-los mai tots a la memòria). Retorna el nombre de línies.

    Si un fitxer no acaba en salt de línia, l'hi afegeix: si no, l'última
    línia d'un i la primera del següent quedarien enganxades.
    """
    linies = 0
    with open(sortida, "wb") as sortint:
        for ruta in fitxers:
            ultim = b"\n"
            with open(ruta, "rb") as entrant:
                while tros := entrant.read(1 << 20):
                    linies += tros.count(b"\n")
                    sortint.write(tros)
                    ultim = tros[-1:]
            if ultim != b"\n":
                sortint.write(b"\n")
                linies += 1
    return linies


def comptar_rimes(ruta):
    """
    Recompte de la columna de rima consonant del fitxer ajuntat.

    Retorna (total de línies, Counter de rimes, paraula on surt cada rima per
    primer cop, línies mal formades). El Counter conserva l'ordre d'aparició,
    o sigui que recórrer-lo és recórrer el fitxer.
    """
    rimes = Counter()
    exemple = {}
    dolentes = 0
    total = 0
    with open(ruta, "r", encoding="utf-8") as f:
        for linia in f:
            total += 1
            camps = linia.rstrip("\n").split("$")
            if len(camps) != CAMPS:
                dolentes += 1
                continue
            rima = camps[COL_RIMA_CONSONANT]
            rimes[rima] += 1
            if rima not in exemple:
                exemple[rima] = camps[0]
    return total, rimes, exemple, dolentes


def main():
    sortida = sys.argv[1] if len(sys.argv) > 1 else FITXER_TOT

    fitxers = fitxers_font(sortida)
    linies = ajuntar(fitxers, sortida)
    mida = os.path.getsize(sortida) / 1e6
    print(f"Ajuntats {len(fitxers)} fitxers -> {sortida}")
    print(f"  {linies:,} línies, {mida:,.0f} MB\n")

    total, rimes, exemple, dolentes = comptar_rimes(sortida)
    uniques = [r for r, n in rimes.items() if n == 1]

    print("RIMA CONSONANT (camp 3)")
    print(f"  línies llegides          {total:11,}")
    print(f"  rimes DIFERENTS          {len(rimes):11,}")
    print(f"  que només surten un cop  {len(uniques):11,}")
    if dolentes:
        print(f"  ⚠️  línies sense {CAMPS} camps  {dolentes:11,}")

    print("\n  les 10 rimes més poblades:")
    for rima, n in rimes.most_common(10):
        print(f"    {rima:16s} {n:9,}   p. ex. {exemple[rima]}")

    # Rima única = una sola forma en tot el fitxer: no rima amb cap altra
    # d'aquestes 3,4 M (amb el diccionari base sí que hi pot rimar).
    print(f"\n  les 10 primeres rimes que només surten un cop"
          f" (en ordre d'aparició):")
    for rima in uniques[:10]:
        print(f"    {rima:16s} {exemple[rima]}")


if __name__ == "__main__":
    main()
