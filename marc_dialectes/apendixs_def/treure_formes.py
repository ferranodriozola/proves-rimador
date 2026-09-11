"""
Treure les columnes del softcatala.txt de cada dialecte, per separat.

    python3 marc_dialectes/apendixs_def/treure_formes.py

    {dialecte}/softcatala.txt  ->  {dialecte}/col_1_{dialecte}.txt   (lema)
                                   {dialecte}/col_2_{dialecte}.txt   (codi)

Una carpeta per dialecte, i dins de cada una el seu softcatala.txt de tres
columnes (forma, lema, codi). Es va carpeta per carpeta i se'n treuen la
segona i la tercera columna, cadascuna al seu fitxer, en el mateix ordre i amb
les mateixes repeticions que l'origen: aixi les tres columnes es podran tornar
a enganxar fila per fila.
"""

import os
import sys

CARPETA = os.path.dirname(os.path.abspath(__file__))
DIALECTES = ["ca", "nw", "ba", "va"]

# Quina columna va a quin fitxer: col_1 el lema, col_2 el codi.
COLUMNES = {1: "col_1", 2: "col_2"}


def main():
    for dialecte in DIALECTES:
        carpeta = os.path.join(CARPETA, dialecte)
        entrada = os.path.join(carpeta, "softcatala.txt")
        if not os.path.exists(entrada):
            sys.exit("no hi ha %s." % entrada)

        # Newline LF a posta, com als altres fitxers: som a Windows i el Python,
        # sense dir-ho, escriuria CRLF.
        sortides = {}
        for columna, prefix in COLUMNES.items():
            cami = os.path.join(carpeta, "%s_%s.txt" % (prefix, dialecte))
            sortides[columna] = open(cami, "w", encoding="utf-8", newline="\n")

        files = 0
        try:
            with open(entrada, encoding="utf-8") as origen:
                for numero, linia in enumerate(origen, 1):
                    camps = linia.split()
                    if not camps:
                        continue
                    if len(camps) != 3:
                        sys.exit("%s/softcatala.txt, linia %d: hi ha %d camps i n'hi "
                                 "ha d'haver 3 (forma, lema, codi)."
                                 % (dialecte, numero, len(camps)))
                    for columna, fitxer in sortides.items():
                        fitxer.write(camps[columna] + "\n")
                    files += 1
        finally:
            for fitxer in sortides.values():
                fitxer.close()

        print("{:<6} {:>10,} files  ->  {}".format(
            dialecte, files,
            ", ".join("%s_%s.txt" % (COLUMNES[c], dialecte) for c in sorted(COLUMNES))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
