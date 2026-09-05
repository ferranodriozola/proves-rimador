"""
Treure la primera columna dels tres apendixs, per passar-la al transcriptor.

    python3 marc_dialectes/apendixs_def/treure_formes.py

    ca.txt, ba.txt, va.txt  ->  ca_x_transc.txt, ba_x_transc.txt, va_x_transc.txt

Una forma per linia, en el mateix ordre i amb les mateixes repeticions que
l'apendix: aixi la sortida del transcriptor es podra tornar a enganxar fila per
fila amb el lema i el codi.
"""

import os
import sys

CARPETA = os.path.dirname(os.path.abspath(__file__))
DOCUMENTS = ["ca", "ba", "va"]


def main():
    for doc in DOCUMENTS:
        entrada = os.path.join(CARPETA, doc + ".txt")
        sortida = os.path.join(CARPETA, doc + "_x_transc.txt")
        if not os.path.exists(entrada):
            sys.exit("no hi ha %s: fes anar abans ajuntar_apendixs.py." % entrada)

        files = 0
        # Newline LF a posta, com als altres fitxers: som a Windows i el Python,
        # sense dir-ho, escriuria CRLF.
        with open(entrada, encoding="utf-8") as origen, \
                open(sortida, "w", encoding="utf-8", newline="\n") as desti:
            for linia in origen:
                camps = linia.split()
                if not camps:
                    continue
                desti.write(camps[0] + "\n")
                files += 1

        print("{:<8} {:>10,} formes  ->  {}".format(doc, files, os.path.basename(sortida)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
