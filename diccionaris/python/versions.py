"""
Comprovar que tot quadri i escriure el versions.json.

    python3 diccionaris/python/versions.py

És l'últim pas i el que decideix si es publica: si aquí res no quadra, peta, el
commit no arriba a fer-se i les columnes velles es queden servint-se.

La versió de cada fitxer és un resum del seu contingut. Es refresca exactament
quan el fitxer ha canviat: ni abans (com passava quan una columna reescrita
mantenia el número vell i es barrejaven generacions del diccionari) ni de més.

Les claus són NOMS DE FITXER, sense la carpeta, perquè així els busca el
navegador (vegeu llegirFitxerAmbIndexedDB a js/script.js, que fa
rutaFitxer.split("/").pop()). Per això els fitxers dels dialectes duen el codi
al nom: si no, els quatre col_3.idx.txt serien la mateixa entrada.

Hi entren els fitxers de TOTS els dialectes, no només els del que el web
serveix ara: es generen igualment, i tenir-ne la versió és el que permetrà al
navegador desar-los a la memòria cau el dia que es pugui triar el dialecte.
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

DIR_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if DIR_SCRIPTS not in sys.path:
    sys.path.insert(0, DIR_SCRIPTS)

import avisos
import camins
import config


def resum(cami):
    calculador = hashlib.sha256()
    with open(cami, "rb") as fitxer:
        for tros in iter(lambda: fitxer.read(1024 * 1024), b""):
            calculador.update(tros)
    return calculador.hexdigest()[:12]


def files_de(cami):
    with open(cami, "rb") as fitxer:
        dades = fitxer.read()
    if not dades:
        return 0
    return len(dades.rstrip(b"\n").split(b"\n"))


def comprovar_la_base():
    """
    Que col_0, col_1 i col_2 siguin de debò la identitat del diccionari.

    NO és una comprovació de més: aquelles tres columnes són la referència amb
    què el sincronitzar.py decideix, fila per fila, qui ha canviat una paraula
    (si el diccionari o la col_10). Si una execució peta a mitges i algú
    comiteja a mà, deixen de ser-ho, i llavors el repartiment de culpes
    atribueix els canvis al costat que no toca, EN SILENCI. Val més que peti
    aquí.
    """
    columnes = [camins.llegir_columna(camins.cami_columna(n)) for n in (0, 1, 2)]
    files = camins.llegir_diccionari(config.CAMI_PUBLICAT)

    if len(columnes[0]) != len(files):
        avisos.plegar(
            f"la col_0 té {camins.mil(len(columnes[0]))} files i "
            f"{config.DICCIONARI_PUBLICAT} en té {camins.mil(len(files))}. "
            "Passa el columnes.py.")

    for i, fila in enumerate(files):
        for n, columna in zip((0, 1, 2), columnes):
            if columna[i] != fila[n]:
                avisos.plegar(
                    f"la col_{n}, fila {i + 1}, diu {columna[i]!r} i el diccionari diu "
                    f"{fila[n]!r}. Les columnes 0, 1 i 2 són la referència amb què es "
                    "reconcilien el diccionari i la col_10: si no són les seves, el "
                    "sincronitzar.py atribuiria els canvis al costat que no toca. "
                    "Passa el columnes.py.")
    return len(files)


def parella_internada(versions, nom, cami_taula, cami_idx, total_files):
    for cami in (cami_taula, cami_idx):
        if not os.path.exists(cami):
            avisos.plegar(f"falta {os.path.relpath(cami, camins.ARREL)}. Passa l'internar.py.")

    # L'índex ha de tenir una fila per paraula, com les columnes d'origen. Si
    # no en té, és que les internades són d'una generació anterior i el
    # navegador llegiria la fila equivocada de cada paraula.
    files_idx = files_de(cami_idx)
    if files_idx != total_files:
        avisos.plegar(f"{os.path.basename(cami_idx)} té {camins.mil(files_idx)} files i "
                      f"les columnes en tenen {camins.mil(total_files)}. Passa l'internar.py.")

    # I cap número pot assenyalar fora de la seva taula.
    entrades = files_de(cami_taula)
    with open(cami_idx, "rb") as fitxer:
        major = max(int(n) for n in fitxer.read().split(b"\n"))
    if major >= entrades:
        avisos.plegar(f"{os.path.basename(cami_idx)} arriba fins al {major} i la seva "
                      f"taula només té {entrades} entrades. Passa l'internar.py.")

    versions[os.path.basename(cami_taula)] = resum(cami_taula)
    versions[os.path.basename(cami_idx)] = resum(cami_idx)


def main():
    total_files = comprovar_la_base()
    avisos.nota(f"La base quadra: col_0, col_1 i col_2 són la identitat del diccionari "
                f"({camins.mil(total_files)} files)")

    versions = {}
    files = {}
    for n in camins.COLUMNES_DEL_DICCIONARI:
        cami = camins.cami_columna(n)
        if not os.path.exists(cami):
            avisos.plegar(f"falta {os.path.relpath(cami, camins.ARREL)}. Passa el columnes.py.")
        versions[os.path.basename(cami)] = resum(cami)
        files[f"col_{n}"] = files_de(cami)

    # Són un sol diccionari partit en columnes i han d'anar totes a l'una.
    if len(set(files.values())) > 1:
        detall = ", ".join(f"{nom}: {camins.mil(q)}" for nom, q in files.items())
        avisos.plegar(f"les columnes no tenen el mateix nombre de files ({detall}).")

    for n in camins.INTERNADES_DEL_DICCIONARI:
        parella_internada(versions, f"col_{n}", camins.cami_internat(n, "taula"),
                          camins.cami_internat(n, "idx"), total_files)

    codis = camins.dialectes()
    for codi in codis:
        for n in camins.COLUMNES_DE_DIALECTE:
            parella_internada(versions, f"col_{n}_{codi}",
                              camins.cami_internat_dialecte(codi, n, "taula"),
                              camins.cami_internat_dialecte(codi, n, "idx"), total_files)

    contingut = {
        "generat": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "files": total_files,
        "dialectes": codis,
        "columnes": versions,
    }
    with open(camins.VERSIONS, "w", encoding="utf-8") as fitxer:
        json.dump(contingut, fitxer, ensure_ascii=False, indent=2)
        fitxer.write("\n")

    avisos.nota(f"versions.json: {len(versions)} fitxers, {camins.mil(total_files)} files, "
                f"dialectes {', '.join(codis)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
