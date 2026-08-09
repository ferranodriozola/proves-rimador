"""Escriu diccionaris/versions.json amb una versió per columna.

La versió de cada columna és un resum (hash) del seu contingut. Això vol dir
que el navegador es torna a baixar EXACTAMENT les columnes que han canviat:

  - Si toques el diccionari general (separar_arxiu...py), es reescriuen les deu
    columnes i totes deu canvien de versió.
  - Si toques la columna 10 (creador_rima...py), només canvien de versió les
    columnes que aquell script ha reescrit de debò (paraula, d'on ve, codi,
    rima consonant, rima assonant i transcripció) i, d'aquestes, només les que
    hagin quedat diferents. Les síl·labes, el Vicc, la Viquipèdia i el DIEC no
    es tornen a baixar.

Abans hi havia dos comptadors a mà, "general" i "transcripcions", i calia
recordar quin script escrivia quina columna. No coincidia: el pipeline del
diccionari reescrivia les columnes de rimes i transcripció però només pujava
el comptador general, i els navegadors es quedaven aquelles tres columnes
d'una generació anterior. Amb el diccionari desplaçat una fila, la rima que
es llegia era la de la paraula del costat, i una cerca de 'dona' arribava a
treure 'arjau' o 'Arp'. Amb un resum del contingut això no pot passar: si el
fitxer canvia, la versió canvia.

També comprova que les deu columnes tinguin el mateix nombre de files. Si no
el tenen, no són el mateix diccionari i el programa acaba amb error perquè el
workflow s'aturi abans de publicar res.
"""

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
    """Hash curt del contingut del fitxer."""
    calculador = hashlib.sha256()
    with open(cami, "rb") as fitxer:
        for tros in iter(lambda: fitxer.read(1024 * 1024), b""):
            calculador.update(tros)
    return calculador.hexdigest()[:12]


def nombre_de_files(cami):
    """Files del fitxer, tant si acaba amb salt de línia com si no."""
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
