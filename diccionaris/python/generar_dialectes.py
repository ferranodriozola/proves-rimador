"""
La rima de cada dialecte, a partir de la seva transcripció.

    python3 diccionaris/python/generar_dialectes.py

Per a cada subcarpeta de dialectes_col/ llegeix la transcripció i n'escriu la
rima consonant i l'assonant al costat:

    dialectes_col/va/col_9_transcripcio_va.txt     ← la font, és el que s'edita
    dialectes_col/va/col_3_rimacons_va.txt         ← se'n deriva
    dialectes_col/va/col_4_rimaass_va.txt          ← se'n deriva

    rima consonant = tot el que va darrere de l'ÚLTIM accent primari
    rima assonant  = les vocals de la consonant

LA RIMA NO S'EDITA MAI ENLLOC. El que s'edita és la transcripció; la rima és un
càlcul de dues línies que se'n deriva. Fins ara aquest càlcul era escrit DUES
vegades, al "separar_arxiu" i al "creador_rima + dicc", amb un comentari a cada
banda demanant que no divergissin mai. Ara és aquí i només aquí, i val per a
tots els dialectes alhora.

QUINS DIALECTES HI HA no es declara enlloc: són les subcarpetes de
dialectes_col/. Un dialecte nou és una carpeta amb la seva transcripció a
dins, i aquest script ja la troba.

Les columnes internades (taula + idx) NO es fan aquí: les fa el
generar_columnes_internades.py, que és qui interna totes les columnes del
repositori, les del diccionari i les dels dialectes.
"""

import os
import sys

DIR_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(DIR_SCRIPTS)          # diccionaris/
ARREL = os.path.dirname(BASE)                # el repositori

DIALECTES_COL = os.path.join(ARREL, "dialectes_col")
CAMI_PARAULES = os.path.join(BASE, "separat", "col_0.txt")

# El dialecte del qual surt la columna 10, que és la que s'edita a mà, i que
# per tant és l'únic que el separar_arxiu i el creador_rima toquen.
CENTRAL = "ca"

# Com es diuen les columnes dins de cada carpeta de dialecte. El número és el
# de sempre (el que tenien dins el diccionari) i el codi va al nom del fitxer,
# no només a la carpeta: el navegador indexa la memòria cau i el versions.json
# pel nom del fitxer sol (vegeu llegirFitxerAmbIndexedDB a js/script.js, que fa
# rutaFitxer.split("/").pop()), i quatre col_3.idx.txt es trepitjarien.
NOMS = {3: "rimacons", 4: "rimaass", 9: "transcripcio"}

# Les vocals que es queden a la rima assonant. És la llista de sempre, la
# mateixa que hi havia al separar_arxiu i al creador_rima.
VOCALS = "ɔəaeiou@Eɛˈ"

ACCENT = "ˈ"


def dialectes():
    """Els codis, que són les subcarpetes de dialectes_col/."""
    if not os.path.isdir(DIALECTES_COL):
        raise SystemExit(f"ERROR: no hi ha el directori {DIALECTES_COL}")
    codis = sorted(
        nom for nom in os.listdir(DIALECTES_COL)
        if os.path.isdir(os.path.join(DIALECTES_COL, nom)) and not nom.startswith(".")
    )
    if not codis:
        raise SystemExit(f"ERROR: no hi ha cap dialecte a {DIALECTES_COL}")
    return codis


def cami(codi, numero):
    """dialectes_col/va/col_3_rimacons_va.txt"""
    return os.path.join(DIALECTES_COL, codi, f"col_{numero}_{NOMS[numero]}_{codi}.txt")


def cami_internat(codi, numero, mena):
    """dialectes_col/va/internat/col_3_rimacons_va.idx.txt"""
    return os.path.join(DIALECTES_COL, codi, "internat",
                        f"col_{numero}_{NOMS[numero]}_{codi}.{mena}.txt")


def llegir_columna(camí):
    """Una columna és una línia per fila i NO acaba amb salt de línia."""
    with open(camí, encoding="utf-8") as fitxer:
        text = fitxer.read()
    if text.endswith("\n"):
        text = text[:-1]
    return text.split("\n")


def escriure_columna(camí, valors):
    """Sense salt de línia al final, com totes les columnes del repositori: el
    navegador munta els seus arrays partint el text per '\\n' sense filtrar res
    (vegeu processarFitxerDeText a js/script.js), i un salt final li donaria una
    fila de més que quedaria desquadrada amb la resta de columnes."""
    os.makedirs(os.path.dirname(camí), exist_ok=True)
    with open(camí, "w", encoding="utf-8") as fitxer:
        fitxer.write("\n".join(valors))


def calcular_rimes(transcripcio):
    """La rima consonant i l'assonant d'una transcripció."""
    consonant = transcripcio.split(ACCENT)[-1]
    assonant = "".join(lletra for lletra in consonant if lletra in VOCALS)
    return consonant, assonant


def mil(n):
    """619783 -> '619.783', com la resta de la documentació."""
    return f"{n:,}".replace(",", ".")


def main():
    if not os.path.exists(CAMI_PARAULES):
        raise SystemExit(f"ERROR: no hi ha {CAMI_PARAULES}")
    files = len(llegir_columna(CAMI_PARAULES))
    print(f"Diccionari: {mil(files)} files\n")

    sospitoses = 0

    for codi in dialectes():
        camí_transcripcio = cami(codi, 9)
        if not os.path.exists(camí_transcripcio):
            raise SystemExit(
                f"ERROR: falta {camí_transcripcio}.\n"
                f"       És la transcripció del dialecte '{codi}', d'on surt tota\n"
                "       la seva rima. Si la carpeta no hi hauria de ser, treu-la."
            )

        transcripcions = llegir_columna(camí_transcripcio)

        # Van fila per fila amb el diccionari i no porten cap paraula a dins:
        # si no tenen la mateixa mida, cada paraula hereta la pronúncia d'una
        # altra i no se'n queixa ningú.
        if len(transcripcions) != files:
            raise SystemExit(
                f"ERROR: {os.path.basename(camí_transcripcio)} té "
                f"{mil(len(transcripcions))} files i el diccionari en té {mil(files)}.\n"
                "       Són un sol diccionari partit en columnes i han d'anar totes\n"
                "       a l'una. Si al diccionari hi ha entrades noves, cal\n"
                "       transcriure-les abans de publicar res."
            )

        buides = [i + 1 for i, t in enumerate(transcripcions) if not t.strip()]
        if buides:
            raise SystemExit(
                f"ERROR: {os.path.basename(camí_transcripcio)} té {len(buides)} files "
                f"buides (la primera, la {buides[0]}).\n"
                "       Una fila sense transcripció no té rima i no es pot publicar."
            )

        consonants, assonants = [], []
        for transcripcio in transcripcions:
            consonant, assonant = calcular_rimes(transcripcio)
            consonants.append(consonant)
            assonants.append(assonant)

        escriure_columna(cami(codi, 3), consonants)
        escriure_columna(cami(codi, 4), assonants)

        # Sense accent primari, la "rima" és la transcripció sencera i
        # l'assonant sol quedar buida: aquelles files rimarien totes entre
        # elles. No atura res (no desquadra cap columna i el web funciona
        # igual), però és una rima que no és i algú ho ha de mirar.
        sense = [i for i, t in enumerate(transcripcions) if ACCENT not in t]
        sospitoses += len(sense)

        print(f"  {codi}: {len(set(consonants)):>6} rimes consonants, "
              f"{len(set(assonants)):>4} assonants"
              f"{f'   ⚠ {len(sense)} files sense accent primari' if sense else ''}")
        for i in sense[:5]:
            print(f"       fila {i + 1}: {transcripcions[i]!r}")
        if len(sense) > 5:
            print(f"       ... i {len(sense) - 5} més")

    if sospitoses:
        print("\n⚠ Les files sense accent primari donen una rima que no és. "
              "S'han de corregir\n  a la transcripció del seu dialecte.")
    print("\nFet! Ara toca el generar_columnes_internades.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
