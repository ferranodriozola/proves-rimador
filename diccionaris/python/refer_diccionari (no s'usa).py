"""
EINA DE SEGURETAT. Refer el diccionari a partir de les columnes de separat/.

    python3 diccionaris/python/refer_diccionari.py --sortida /tmp/prova.txt
    python3 diccionaris/python/refer_diccionari.py --si

    separat/col_0, col_1, col_2, col_5, col_6, col_7, col_8
                            ▼
                  diccionari.5.2.3.txt

És el camí contrari del columnes.py, i serveix per a una sola cosa: si el
diccionari es perd o es corromp, tornar-lo a tenir. Les columnes són al
repositori i el contenen sencer, camp per camp: partir-lo no en perd res.

NO ÉS UN PAS DE LA CADENA i no corre mai als workflows. El diccionari és la
font que s'edita a mà i les columnes en són derivades; això només desfà aquell
camí quan alguna cosa ha anat malament.

QUÈ NO REFÀ. La col_10, que no surt de separat/ sinó de les transcripcions de
dialectes_col/. Si també l'has perduda, després d'això passa el
sincronitzar.py, que la torna a fer si no hi és.

COMPTE AMB EL v.6. Les columnes de separat/ són les del diccionari PUBLICAT.
Mentre es publiqui el base són el mateix, però si algun dia config.py publica
el v.6, refer-hi el base voldria dir omplir-lo de quatre milions de formes amb
pronom. Per això, si l'interruptor és al v.6, això no fa res.
"""

import argparse
import os
import sys

DIR_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if DIR_SCRIPTS not in sys.path:
    sys.path.insert(0, DIR_SCRIPTS)

import avisos
import camins
import config


def llegir_les_columnes():
    columnes = []
    for n in camins.COLUMNES_DEL_DICCIONARI:
        cami = camins.cami_columna(n)
        if not os.path.exists(cami):
            avisos.plegar(f"falta {os.path.relpath(cami, camins.ARREL)}. Sense les set "
                          "columnes no es pot refer el diccionari.")
        columnes.append(camins.llegir_columna(cami))

    mides = {n: len(c) for n, c in zip(camins.COLUMNES_DEL_DICCIONARI, columnes)}
    if len(set(mides.values())) > 1:
        detall = ", ".join(f"col_{n}: {camins.mil(q)}" for n, q in mides.items())
        avisos.plegar(f"les columnes no tenen el mateix nombre de files ({detall}). "
                      "Refer el diccionari amb columnes desquadrades voldria dir donar "
                      "a cada paraula els camps d'una altra.")

    # Un '$' dins d'un camp partiria la línia en un lloc que no toca i el
    # diccionari sortiria amb vuit camps a la fila següent que el llegís.
    for n, columna in zip(camins.COLUMNES_DEL_DICCIONARI, columnes):
        dolentes = [i + 1 for i, valor in enumerate(columna) if "$" in valor]
        if dolentes:
            avisos.plegar(f"la col_{n} té un '$' a {len(dolentes)} files (la primera, la "
                          f"{dolentes[0]}), i el '$' és el que separa els camps.")

    buides = [i + 1 for i, paraula in enumerate(columnes[0]) if not paraula.strip()]
    if buides:
        avisos.plegar(f"la col_0 té {len(buides)} files sense paraula (la primera, la "
                      f"{buides[0]}).")

    return [list(fila) for fila in zip(*columnes)]


def main():
    analitzador = argparse.ArgumentParser(
        description="Refà el diccionari a partir de les columnes de separat/.")
    analitzador.add_argument("--sortida", help="on escriure'l (per defecte, el diccionari)")
    analitzador.add_argument("--si", action="store_true", help="no preguntis res")
    opcions = analitzador.parse_args()

    if config.CAL_V6:
        avisos.plegar(
            "config.py publica el v.6, o sigui que les columnes de separat/ són les "
            "seves (quatre milions de formes amb pronom) i no les del diccionari base. "
            "Refer-lo d'aquí seria omplir-lo d'allò.")

    files = llegir_les_columnes()
    desti = os.path.abspath(opcions.sortida) if opcions.sortida else camins.DICCIONARI
    relatiu = os.path.relpath(desti, camins.ARREL)
    avisos.nota(f"De les columnes en surten {camins.mil(len(files))} files de "
                f"{camins.CAMPS} camps.")

    # Si ja n'hi ha un, no se sobreescriu sense mirar-s'ho: aquesta eina és per
    # a quan alguna cosa ha anat malament, i el que hi ha pot ser el bo.
    #
    # Es llegeix com a text pelat i no com un diccionari: si el que hi ha està
    # trencat (una fila amb els camps que no toquen, per exemple), una eina de
    # reparació no es pot permetre petar justament per això.
    if os.path.exists(desti):
        actuals = camins.llegir_columna(desti)
        noves = ["$".join(fila) for fila in files]
        if actuals == noves:
            avisos.nota(f"{relatiu} ja diu exactament això: no s'hi ha tocat res.")
            return 0

        camps = sorted({linia.count("$") + 1 for linia in actuals})
        diferents = sum(1 for a, b in zip(actuals, noves) if a != b)
        avisos.nota(f"\nATENCIÓ: {relatiu} ja existeix i NO diu el mateix.")
        avisos.nota(f"  ara: {camins.mil(len(actuals))} files de "
                    f"{' o '.join(str(c) for c in camps)} camps")
        avisos.nota(f"  de les columnes: {camins.mil(len(noves))} files de "
                    f"{camins.CAMPS} camps")
        avisos.nota(f"  {camins.mil(diferents)} files diferents de les que es poden comparar")
        ensenyades = 0
        for i, (a, b) in enumerate(zip(actuals, noves)):
            if a != b:
                avisos.nota(f"    fila {i + 1}:")
                avisos.nota(f"       ara:      {a[:100]}")
                avisos.nota(f"       columnes: {b[:100]}")
                ensenyades += 1
                if ensenyades == 3:
                    break

        if not opcions.si:
            if input(f"\nSobreescric {relatiu}? [s/N] ").strip().lower() not in ("s", "si", "sí"):
                avisos.nota("No s'ha tocat res.")
                return 1

    camins.escriure_diccionari(files, desti)
    avisos.nota(f"\nFet: {relatiu}, {camins.mil(len(files))} files.")
    avisos.nota("Si també has perdut la col_10, passa ara el sincronitzar.py: la torna a "
                "fer\nde les transcripcions de dialectes_col/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
