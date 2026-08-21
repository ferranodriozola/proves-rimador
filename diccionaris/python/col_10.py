"""
El format de la columna 10. Aquest fitxer no és cap pas del workflow: és el
mòdul que sap llegir-la i escriure-la, i el fa servir el sincronitzar.py.

    diccionaris/col_10.txt

    paraula € lema € codi €$ca$ transcripció €$nw$ transcripció €$va$ ...
    a € a € NCFS000 €$ba$ ˈə €$ca$ ˈa €$nw$ ˈa €$va$ ˈa

ÉS UN DELS DOS ÚNICS LLOCS ON ES FAN CANVIS (l'altre és el diccionari). No el
llegeix ningú més: ni el web, ni les llistes, ni el joc. Serveix per a poder
mirar i corregir com sona una paraula als quatre dialectes alhora, en una sola
línia, en comptes d'anar per número de fila per quatre fitxers que no porten
cap paraula a dins.

Els tres primers camps són els mateixos que els del diccionari, i s'hi poden
corregir: qui reconcilia les dues bandes és el sincronitzar.py.

QUANT PESA. Un sol fitxer amb els quatre dialectes són 76 MB. GitHub avisa a
partir de 50 MB i bloqueja a 100: hi cap, però amb el marge just. El dia que
vagi estret, partir-lo per dialectes (uns 20 MB cadascun) no demana tocar res
més que les dues funcions d'aquí sota.

    python3 diccionaris/python/col_10.py

Executat a mà, la refà del diccionari i de les transcripcions que hi ha. És
una reparació (o la primera vegada), no un pas de la cadena.
"""

import os
import re
import sys

DIR_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if DIR_SCRIPTS not in sys.path:
    sys.path.insert(0, DIR_SCRIPTS)

import avisos
import camins

CAMI = camins.COL_10
SEPARADOR = " € "


def marca(codi):
    """ €$va$ , el que va davant de cada transcripció. El codi del dialecte va
    escrit a cada tros a posta: així la línia diu de qui és cada transcripció i
    no depèn de l'ordre ni del nombre de dialectes que hi hagi."""
    return f" €${codi}$ "


# L'espai final és opcional en llegir: hi ha editors que escapcen els espais de
# final de línia, i seria una llàstima que una línia deixés de valdre per això.
# Una transcripció mai no en duu, ni al davant ni al darrere.
TROS = re.compile(r" €\$([^$]*)\$ ?")


def existeix():
    return os.path.exists(CAMI)


def llegir(cami=None):
    """Torna (identitats, transcripcions):

        identitats     [[paraula, lema, codi], ...]
        transcripcions {codi: [transcripció, ...]}
    """
    cami = cami or CAMI
    relatiu = os.path.relpath(cami, camins.ARREL)
    identitats = []
    transcripcions = {}
    ordre = None

    for numero, linia in enumerate(camins.llegir_columna(cami), 1):
        trossos = TROS.split(linia)
        cap = trossos[0].split(SEPARADOR)
        if len(cap) != camins.CAMPS_IDENTITAT:
            avisos.plegar(
                f"col_10.txt, línia {numero}: hi ha {len(cap)} camps abans del primer "
                f"dialecte i n'hi ha d'haver {camins.CAMPS_IDENTITAT} "
                f"(paraula € lema € codi).", relatiu, numero)

        parells = list(zip(trossos[1::2], trossos[2::2]))
        codis = [codi for codi, _ in parells]
        if not codis:
            avisos.plegar(
                f"col_10.txt, línia {numero}: no hi ha cap dialecte. Les línies han "
                f"de ser: paraula € lema € codi €$ca$ transcripció €$va$ ...",
                relatiu, numero)

        # Tots els dialectes a totes les línies i sempre en el mateix ordre: si
        # una línia se'n deixés un, la seva columna quedaria més curta que les
        # altres i totes les paraules de sota heretarien la pronúncia d'una altra.
        if ordre is None:
            ordre = codis
            transcripcions = {codi: [] for codi in ordre}
        elif codis != ordre:
            avisos.plegar(
                f"col_10.txt, línia {numero}: porta els dialectes {', '.join(codis)} i "
                f"les línies d'abans en porten {', '.join(ordre)}. Han de ser els "
                f"mateixos i en el mateix ordre a totes les línies.", relatiu, numero)

        identitats.append(cap)
        for codi, valor in parells:
            if not valor.strip():
                avisos.plegar(
                    f"col_10.txt, línia {numero}: la transcripció de '{codi}' és buida. "
                    f"Una paraula sense transcripció no té rima i no es pot publicar.",
                    relatiu, numero)
            transcripcions[codi].append(valor)

    return identitats, transcripcions


def escriure(identitats, transcripcions, cami=None):
    """Determinista: si no ha canviat res, surt el mateix fitxer i el git no hi
    veu cap diferència."""
    codis = sorted(transcripcions)
    for codi in codis:
        if len(transcripcions[codi]) != len(identitats):
            avisos.plegar(
                f"el dialecte '{codi}' té {camins.mil(len(transcripcions[codi]))} files i "
                f"la col_10 n'ha de tenir {camins.mil(len(identitats))}.")

    linies = []
    for i, identitat in enumerate(identitats):
        linia = SEPARADOR.join(identitat)
        for codi in codis:
            linia += marca(codi) + transcripcions[codi][i]
        linies.append(linia)

    camins.escriure_columna(cami or CAMI, linies)
    return linies


def main():
    """Refer la col_10 del diccionari i de les transcripcions que hi ha ara."""
    files = camins.llegir_diccionari()
    identitats = [fila[:camins.CAMPS_IDENTITAT] for fila in files]

    transcripcions = {}
    for codi in camins.dialectes():
        cami = camins.cami_dialecte(codi, 9)
        if not os.path.exists(cami):
            avisos.plegar(f"falta {os.path.relpath(cami, camins.ARREL)}.")
        transcripcions[codi] = camins.llegir_columna(cami)

    linies = escriure(identitats, transcripcions)
    mida = os.path.getsize(CAMI)
    avisos.nota(f"col_10.txt: {camins.mil(len(linies))} línies, {mida/1048576:.1f} MB, "
                f"dialectes {', '.join(sorted(transcripcions))}")
    if mida > 50 * 1024 * 1024:
        avisos.nota("   (per sobre dels 50 MB: GitHub avisarà a cada push. Bloqueja als 100.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
