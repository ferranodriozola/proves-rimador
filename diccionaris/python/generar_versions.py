import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# .parent.parent perquè aquest fitxer viu a diccionaris/python/ i tot el que
# toca és a diccionaris/. Es calcula des de __file__ i no des d'on s'executa
# l'script, perquè així funciona tant des dels workflows com si l'obres a mà
# des de qualsevol carpeta.
BASE = Path(__file__).resolve().parent.parent
DIRECTORI_COLUMNES = BASE / "separat"
FITXER_VERSIONS = BASE / "versions.json"
DIRECTORI_INTERNAT = DIRECTORI_COLUMNES / "internat"
# La col_3, la col_4 i la col_9 no hi són: depenen del dialecte i viuen a
# dialectes_col/<codi>/, amb les seves internades al costat. Encara no entren al
# versions.json perquè el navegador encara no les demana; quan les demani,
# s'hi hauran d'afegir (els noms ja duen el codi del dialecte a dins, o sigui
# que no xocaran entre ells).
COLUMNES = [f"col_{i}.txt" for i in (0, 1, 2, 5, 6, 7, 8)]

# Les columnes que generar_columnes_internades.py desa a separat/internat/, en
# parelles: un fitxer amb els valors diferents i un altre amb un número per
# fila que hi apunta.
COLUMNES_INTERNADES = [1, 2, 5, 6, 7, 8]


def resum(cami):
    calculador = hashlib.sha256()
    with open(cami, "rb") as fitxer:
        for tros in iter(lambda: fitxer.read(1024 * 1024), b""):
            calculador.update(tros)
    return calculador.hexdigest()[:12]


def nombre_de_files(cami):
    with open(cami, "rb") as fitxer:
        contingut = fitxer.read()
    if not contingut:
        return 0
    return len(contingut.rstrip(b"\n").split(b"\n"))


def main():
    versions = {}
    files = {}

    for columna in COLUMNES:
        cami = DIRECTORI_COLUMNES / columna
        if not cami.exists():
            print(f"ERROR: falta {cami}")
            return 1
        versions[columna] = resum(cami)
        files[columna] = nombre_de_files(cami)

    diferents = set(files.values())
    if len(diferents) > 1:
        print("ERROR: les columnes no tenen el mateix nombre de files.")
        print("Són un sol diccionari partit en deu fitxers i han d'anar totes a l'una:")
        for columna in COLUMNES:
            print(f"  {columna}: {files[columna]} files")
        print("\nSi véns de tocar la columna 10, recorda que aquell script no")
        print("regenera les síl·labes ni els enllaços (col_5 a col_8): si hi has")
        print("afegit o tret cap línia, cal passar pel diccionari general.")
        return 1

    total_files = files[COLUMNES[0]]

    # --- les columnes internades ---
    #
    # Van a la mateixa llista "columnes" i no pas a un apartat seu perquè el
    # navegador les busca pel nom del fitxer tot sol, sense la carpeta (vegeu
    # llegirFitxerAmbIndexedDB a js/script.js). Com que col_2.idx.txt i
    # col_2.txt no es diuen igual, no es trepitgen, i així la memòria cau del
    # navegador els tracta a tots igual sense haver de tocar res.
    for i in COLUMNES_INTERNADES:
        cami_taula = DIRECTORI_INTERNAT / f"col_{i}.taula.txt"
        cami_idx = DIRECTORI_INTERNAT / f"col_{i}.idx.txt"

        for cami in (cami_taula, cami_idx):
            if not cami.exists():
                print(f"ERROR: falta {cami}")
                print("       Passa el generar_columnes_internades.py.")
                return 1

        # L'índex ha de tenir una fila per paraula, com les columnes d'origen.
        # Si no en té, és que les internades són d'una generació anterior del
        # diccionari i el navegador llegiria la fila equivocada de cada paraula.
        files_idx = nombre_de_files(cami_idx)
        if files_idx != total_files:
            print(f"ERROR: {cami_idx.name} té {files_idx} files i les columnes en tenen {total_files}.")
            print("       Les columnes internades s'han quedat endarrerides:")
            print("       passa el generar_columnes_internades.py.")
            return 1

        # I cap número pot assenyalar fora de la seva taula.
        entrades_taula = nombre_de_files(cami_taula)
        with open(cami_idx, "rb") as fitxer:
            major = max(int(n) for n in fitxer.read().split(b"\n"))
        if major >= entrades_taula:
            print(f"ERROR: col_{i}.idx.txt arriba fins al {major} i la seva taula només té {entrades_taula} entrades.")
            print("       La parella no es correspon: passa el generar_columnes_internades.py.")
            return 1

        versions[cami_taula.name] = resum(cami_taula)
        versions[cami_idx.name] = resum(cami_idx)

    contingut = {
        "generat": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "files": total_files,
        "columnes": versions,
    }

    with open(FITXER_VERSIONS, "w", encoding="utf-8") as fitxer:
        json.dump(contingut, fitxer, ensure_ascii=False, indent=2)
        fitxer.write("\n")

    print(f"versions.json actualitzat ({contingut['files']} files per columna):")
    for columna in COLUMNES:
        print(f"  {columna}: {versions[columna]}")
    print("  internat/")
    for i in COLUMNES_INTERNADES:
        print(f"    col_{i}.taula.txt: {versions[f'col_{i}.taula.txt']}"
              f"   col_{i}.idx.txt: {versions[f'col_{i}.idx.txt']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
