import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
DIRECTORI_COLUMNES = BASE / "separat"
FITXER_VERSIONS = BASE / "versions.json"
COLUMNES = [f"col_{i}.txt" for i in range(10)]


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

    contingut = {
        "generat": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "files": files[COLUMNES[0]],
        "columnes": versions,
    }

    with open(FITXER_VERSIONS, "w", encoding="utf-8") as fitxer:
        json.dump(contingut, fitxer, ensure_ascii=False, indent=2)
        fitxer.write("\n")

    print(f"versions.json actualitzat ({contingut['files']} files per columna):")
    for columna in COLUMNES:
        print(f"  {columna}: {versions[columna]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
