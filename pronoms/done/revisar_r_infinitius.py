"""
Revisa quins infinitius (VMN00000) tenen la transcripció fonètica acabada en 'r'.

La -r final dels infinitius normalment no es transcriu (cantar -> kəntˈa). Els casos
que sí que la porten solen ser contaminació d'un homògraf no verbal ('militar' nom,
'prémer'...) i són els que generar_infinitius_hi_en.py ha d'anar arreglant.

Ús:
    python3 revisar_r_infinitius.py            # llegeix diccionaris/separat/col_*.txt
    python3 revisar_r_infinitius.py fitxer.txt # llegeix un .txt de 10 camps amb '$'
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_SEPARAT = os.path.join(BASE_DIR, "..", "diccionaris", "separat")

CODI_INFINITIU = "VMN00000"

COL_FORMA = 0
COL_CODI = 2
COL_TRANSCRIPCIO = 9

# Ròtiques de l'AFI: la 'r' llatina no hi hauria de sortir mai, però també
# comprovem [ɾ] i [r] per si alguna entrada porta la vibrant ben transcrita.
ROTIQUES = ("r", "ɾ")


def llegir_separat():
    """Retorna (forma, codi, transcripcio) de diccionaris/separat/col_*.txt."""
    columnes = {}
    for n in (COL_FORMA, COL_CODI, COL_TRANSCRIPCIO):
        ruta = os.path.join(DIR_SEPARAT, f"col_{n}.txt")
        with open(ruta, "r", encoding="utf-8") as f:
            columnes[n] = f.read().splitlines()

    llargades = {len(v) for v in columnes.values()}
    if len(llargades) != 1:
        raise SystemExit(
            f"Les columnes no tenen el mateix nombre de línies: {llargades}"
        )

    return list(zip(columnes[COL_FORMA], columnes[COL_CODI], columnes[COL_TRANSCRIPCIO]))


def llegir_txt(ruta):
    """Retorna (forma, codi, transcripcio) d'un .txt de 10 camps separats per '$'."""
    files = []
    with open(ruta, "r", encoding="utf-8") as f:
        for num, linia in enumerate(f, 1):
            linia = linia.rstrip("\n")
            if not linia:
                continue
            camps = linia.split("$")
            if len(camps) <= COL_TRANSCRIPCIO:
                print(f"  avís: línia {num} amb {len(camps)} camps, saltada")
                continue
            files.append((camps[COL_FORMA], camps[COL_CODI], camps[COL_TRANSCRIPCIO]))
    return files


def revisar(files):
    infinitius = 0
    sense_transcripcio = []
    amb_r = []

    for forma, codi, transcripcio in files:
        if codi != CODI_INFINITIU:
            continue
        infinitius += 1
        if not transcripcio:
            sense_transcripcio.append(forma)
            continue
        if transcripcio.endswith(ROTIQUES):
            amb_r.append((forma, transcripcio))

    print(f"Infinitius revisats: {infinitius}")
    print(f"Sense transcripció: {len(sense_transcripcio)}")
    print(f"Amb transcripció acabada en ròtica: {len(amb_r)}")

    if sense_transcripcio:
        print("\nSense transcripció:")
        for forma in sense_transcripcio:
            print(f"  {forma}")

    if amb_r:
        amplada = max(len(f) for f, _ in amb_r)
        print("\nTranscripció acabada en 'r' / 'ɾ':")
        for forma, transcripcio in sorted(amb_r):
            print(f"  {forma:<{amplada}}  {transcripcio}")
    else:
        print("\nCap infinitiu amb la -r transcrita.")

    return amb_r


def main():
    if len(sys.argv) > 2:
        raise SystemExit("Ús: python3 revisar_r_infinitius.py [fitxer.txt]")

    if len(sys.argv) == 2:
        ruta = sys.argv[1]
        print(f"Font: {ruta}")
        files = llegir_txt(ruta)
    else:
        print(f"Font: {os.path.normpath(DIR_SEPARAT)}/col_*.txt")
        files = llegir_separat()

    amb_r = revisar(files)
    return 1 if amb_r else 0


if __name__ == "__main__":
    sys.exit(main())
