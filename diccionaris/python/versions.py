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

Hi entren els fitxers de TOTS els dialectes, apendixs inclosos, encara que una
visita només se'n baixi els d'un: el navegador baixa el dialecte que serveix i
no en demana cap altre fins que algú el tria (vegeu carregarDialecte a
js/script.js), i llavors ha de poder-ne saber la versió sense tornar a demanar
res.

La col_0 d'un apendix, a més, hi fa d'interruptor: el navegador dedueix que un
dialecte té apendix perquè aquella clau hi és (vegeu-hi teApendix). O sigui que
això no és només una llista de resums, també és qui diu quins dialectes en
tenen; per això aquí s'hi posa quan la carpeta hi és de debò i no altrament.

DUES LLARGADES I NO UNA. Les columnes del diccionari i les del trans_dicc de
cada dialecte han de tenir totes les files del diccionari; les d'un apendix, les
d'aquell apendix. Per això aquí hi ha dues comprovacions germanes,
comprovar_la_base() i comprovar_lapendix(), i cap de les dues no fa servir el
nombre de l'altra.
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
import col_10 as modul_col_10
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


def comprovar_lapendix(codi):
    """
    Que les columnes d'un apendix quadrin entre elles i amb la seva col_10.

    És la germana de comprovar_la_base(), i hi és pel mateix motiu: les col_0,
    1 i 2 d'un apendix són la referència amb què el sincronitzar.py decideix
    quina fila era quina paraula quan la col_10 en dona una d'alta o de baixa.
    Si deixen de ser-ho —una execució que peta a mitges, un commit a mà—, les
    síl·labes i els enllaços s'arrosseguen cap a la fila que no toca EN SILENCI.

    Torna quantes files té aquest apendix.
    """
    numeros = sorted(set(camins.COLUMNES_APENDIX) | set(camins.COLUMNES_DE_DIALECTE) | {9})
    valors = {}
    for numero in numeros:
        cami = camins.cami_apendix(codi, numero)
        if not os.path.exists(cami):
            avisos.plegar(f"falta {camins.relatiu(cami)}. Passa el columnes.py (la "
                          f"col_3 i la col_4) o el sincronitzar.py (la resta).")
        valors[numero] = camins.llegir_columna(cami)

    quantes = {numero: len(fila) for numero, fila in valors.items()}
    if len(set(quantes.values())) > 1:
        detall = ", ".join(f"col_{n}: {camins.mil(q)}" for n, q in sorted(quantes.items()))
        avisos.plegar(f"les columnes de l'apendix del '{codi}' no tenen el mateix "
                      f"nombre de files ({detall}).")
    total = quantes[0]

    cami_c10 = camins.cami_col_10_apendix(codi)
    if not os.path.exists(cami_c10):
        avisos.plegar(f"falta {camins.relatiu(cami_c10)}, que és el que s'edita per "
                      f"dir quines paraules té l'apendix del '{codi}'. Passa el "
                      f"sincronitzar.py.")

    identitats, transcripcions = modul_col_10.llegir(cami_c10)
    if len(identitats) != total:
        avisos.plegar(f"la col_10 de l'apendix del '{codi}' té "
                      f"{camins.mil(len(identitats))} línies i les seves columnes en "
                      f"tenen {camins.mil(total)}. Passa el sincronitzar.py.")

    for i, fila in enumerate(identitats):
        for camp, numero in enumerate(camins.APENDIX_DE_LA_COL_10):
            if valors[numero][i] != fila[camp]:
                avisos.plegar(
                    f"l'apendix del '{codi}', col_{numero}, fila {i + 1}, diu "
                    f"{valors[numero][i]!r} i la seva col_10 diu {fila[camp]!r}. Les "
                    f"col_0, 1 i 2 d'un apendix són sortides de la seva col_10: si no "
                    f"les diuen igual, el sincronitzar.py arrossegaria les síl·labes "
                    f"cap a la fila que no toca. Passa el sincronitzar.py.")

    if transcripcions.get(codi) != valors[9]:
        avisos.plegar(f"la col_9 de l'apendix del '{codi}' no diu el mateix que la seva "
                      f"col_10. Passa el sincronitzar.py.")

    return total


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

    # Els apendixs. Cadascun té la seva llargada i es comprova contra ella
    # mateixa: aquí no hi pot entrar el total_files de sobre.
    files_apendix = {}
    for codi in codis:
        if not camins.te_apendix(codi):
            continue
        quantes = comprovar_lapendix(codi)
        files_apendix[codi] = quantes

        # La col_0 plana també: les paraules no s'internen (el 85 % són úniques)
        # i és el fitxer que el navegador es baixarà tal com és, com la col_0
        # del diccionari.
        cami_0 = camins.cami_apendix(codi, 0)
        versions[os.path.basename(cami_0)] = resum(cami_0)

        for n in camins.INTERNADES_APENDIX:
            parella_internada(versions, f"col_{n}_{codi} de l'apendix",
                              camins.cami_internat_apendix(codi, n, "taula"),
                              camins.cami_internat_apendix(codi, n, "idx"), quantes)
        avisos.nota(f"  apendix del '{codi}': {camins.mil(quantes)} paraules pròpies")

    contingut = {
        "generat": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "files": total_files,
        "dialectes": codis,
        # Quantes paraules pròpies té cada dialecte. Va a part de "files" a
        # posta: aquell nombre és el del diccionari i val per a tothom, i
        # aquests són un per dialecte i no s'assemblen entre ells.
        "files_apendix": files_apendix,
        "columnes": versions,
    }
    with open(camins.VERSIONS, "w", encoding="utf-8") as fitxer:
        json.dump(contingut, fitxer, ensure_ascii=False, indent=2)
        fitxer.write("\n")

    avisos.nota(f"versions.json: {len(versions)} fitxers, {camins.mil(total_files)} files, "
                f"dialectes {', '.join(codis)}"
                + (f" (amb apendix: {', '.join(sorted(files_apendix))})"
                   if files_apendix else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
