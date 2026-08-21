"""
Partir les dues fonts en les columnes d'una línia per fila.

    python3 diccionaris/python/columnes.py

    el diccionari que digui config.py  ->  separat/col_0,1,2,5,6,7,8
    dialectes_col/<codi>/col_9         ->  col_3 (rima consonant) i col_4 (assonant)

LA REGLA DE LA RIMA ÉS AQUÍ I NOMÉS AQUÍ:

    rima consonant = tot el que va darrere de l'ÚLTIM accent primari
    rima assonant  = les vocals de la consonant

La rima no s'edita mai enlloc: el que s'edita és la transcripció, a la col_10.
Aquest càlcul havia estat escrit dues vegades, en dos scripts diferents, amb un
comentari a cada banda demanant que no divergissin mai.

Els números de columna són els de sempre i hi ha forats (el 3, el 4 i el 9 no
surten del diccionari): el navegador, les llistes i el joc les demanen pel nom
del fitxer.

El diccionari es llegeix línia per línia, sense carregar-se'l a la memòria: el
v.6 en fa 324 MB.
"""

import os
import sys

DIR_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if DIR_SCRIPTS not in sys.path:
    sys.path.insert(0, DIR_SCRIPTS)

import avisos
import camins
import config

ACCENT = "ˈ"

# Les vocals que es queden a la rima assonant. És la llista de sempre.
VOCALS = "ɔəaeiou@Eɛˈ"

# Tot el que pot sortir en una transcripció. Surt de l'inventari real de les
# quatre que hi ha. No és cap caprici de purista: un símbol que no hi sigui és
# un símbol que el filtre de la rima assonant no sap si és vocal o no, i que
# per tant es menjaria en silenci.
INVENTARI = set(" abdefijklmnoprstuvwzðŋɔəɛɡɣɱɲɾʃʎʒˈˌβθχ")


def calcular_rimes(transcripcio):
    consonant = transcripcio.split(ACCENT)[-1]
    assonant = "".join(lletra for lletra in consonant if lletra in VOCALS)
    return consonant, assonant


def partir_diccionari():
    """Escriu una col_N.txt per cada camp del diccionari publicat."""
    if not os.path.exists(config.CAMI_PUBLICAT):
        avisos.plegar(
            f"no hi ha {config.DICCIONARI_PUBLICAT}, que és el que config.py diu que "
            "s'ha de publicar. Si és el v.6, el genera pronoms/ajuntar_diccionari_6.py.")

    sortides = [open(camins.cami_columna(n), "w", encoding="utf-8")
                for n in camins.COLUMNES_DEL_DICCIONARI]
    files = 0
    try:
        with open(config.CAMI_PUBLICAT, encoding="utf-8") as entrada:
            for linia in entrada:
                linia = linia.rstrip("\n")
                if not linia:
                    continue
                camps = linia.split("$")
                if len(camps) != camins.CAMPS:
                    avisos.plegar(
                        f"{config.DICCIONARI_PUBLICAT}, línia {files + 1}: hi ha "
                        f"{len(camps)} camps i n'hi ha d'haver {camins.CAMPS}. Ni la "
                        f"rima ni la transcripció no van al diccionari: són a "
                        f"dialectes_col/.")
                for sortida, camp in zip(sortides, camps):
                    if files:
                        sortida.write("\n")
                    sortida.write(camp)
                files += 1
    finally:
        for sortida in sortides:
            sortida.close()

    if not files:
        avisos.plegar(f"{config.DICCIONARI_PUBLICAT} és buit: no s'ha generat cap columna.")

    noms = ", ".join(f"col_{n}" for n in camins.COLUMNES_DEL_DICCIONARI)
    avisos.nota(f"{config.DICCIONARI_PUBLICAT} -> separat/{{{noms}}}: "
                f"{camins.mil(files)} files")
    return files


def partir_dialecte(codi, files_esperades):
    """De la transcripció d'un dialecte, la seva rima consonant i l'assonant."""
    cami = camins.cami_dialecte(codi, 9)
    if not os.path.exists(cami):
        avisos.plegar(f"falta {os.path.relpath(cami, camins.ARREL)}, que és la "
                      f"transcripció del dialecte '{codi}' i d'on surt tota la seva rima.")

    transcripcions = camins.llegir_columna(cami)

    # Van fila per fila amb el diccionari i no porten cap paraula a dins: si no
    # tenen la mateixa mida, cada paraula hereta la pronúncia d'una altra.
    if len(transcripcions) != files_esperades:
        avisos.plegar(
            f"el dialecte '{codi}' té {camins.mil(len(transcripcions))} files i el "
            f"diccionari publicat en té {camins.mil(files_esperades)}."
            + ("\nEl v.6 i els dialectes encara no conviuen: les formes amb pronom "
               "haurien de portar la seva transcripció a cada dialecte."
               if config.CAL_V6 else ""))

    consonants, assonants = [], []
    sospitoses = []
    for i, transcripcio in enumerate(transcripcions):
        if not transcripcio.strip():
            avisos.plegar(f"el dialecte '{codi}', fila {i + 1}: transcripció buida. "
                          "Una paraula sense transcripció no té rima.")
        consonant, assonant = calcular_rimes(transcripcio)
        consonants.append(consonant)
        assonants.append(assonant)

        # No aturen res (no desquadren cap columna i el web funciona igual): el
        # que fan és donar una rima que no és, i això ho ha de mirar algú.
        motius = []
        if ACCENT not in transcripcio:
            motius.append("sense accent primari")
        if not assonant:
            motius.append("rima assonant buida")
        estranys = set(transcripcio) - INVENTARI
        if estranys:
            motius.append("símbols estranys: " + " ".join(sorted(estranys)))
        if motius:
            sospitoses.append((i + 1, transcripcio, "; ".join(motius)))

    camins.escriure_columna(camins.cami_dialecte(codi, 3), consonants)
    camins.escriure_columna(camins.cami_dialecte(codi, 4), assonants)

    avisos.nota(f"  {codi}: {len(set(consonants)):>6} rimes consonants, "
                f"{len(set(assonants)):>4} assonants")
    return sospitoses


def main():
    files = partir_diccionari()

    codis = camins.dialectes()
    if not codis:
        avisos.plegar(f"no hi ha cap dialecte a {os.path.relpath(camins.DIALECTES_COL, camins.ARREL)}.")

    avisos.nota(f"\nLa rima de cada dialecte:")
    sospitoses = []
    for codi in codis:
        sospitoses.extend((codi, *fila) for fila in partir_dialecte(codi, files))

    if sospitoses:
        avisos.avis(f"{len(sospitoses)} transcripcions donen una rima que no és "
                    f"(mira el resum de l'execució i dialectes_col/a_revisar.txt)")
        avisos.taula("Transcripcions per revisar",
                     ["dialecte", "fila", "transcripció", "què hi passa"], sospitoses)

    # A un fitxer comitejat, i no només al registre: així la llista surt al diff
    # quan canvia i no fa soroll quan no.
    cami_revisar = os.path.join(camins.DIALECTES_COL, "a_revisar.txt")
    with open(cami_revisar, "w", encoding="utf-8") as fitxer:
        fitxer.write("# Transcripcions que donen una rima que no és.\n")
        fitxer.write("# El genera diccionaris/python/columnes.py a cada passada.\n")
        fitxer.write("# dialecte | fila | transcripció | què hi passa\n")
        for fila in sospitoses:
            fitxer.write(" | ".join(str(tros) for tros in fila) + "\n")

    avisos.nota("\nFet!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
