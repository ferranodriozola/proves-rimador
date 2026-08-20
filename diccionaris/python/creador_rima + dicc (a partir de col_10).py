"""
De la "col_10 (canvis aquí)" al diccionari base i a la transcripció del central.

    col_10provisional.txt   paraula € lema € codi € transcripció
                                        ▼
    diccionari.5.2.3.txt                   paraula $ lema $ codi $ síl·labes $ ...
    dialectes_col/ca/col_9_transcripcio_ca.txt    la transcripció, una per fila

EL DICCIONARI SÓN SET CAMPS, NO DEU. Ni la rima consonant, ni l'assonant, ni la
transcripció no hi són: depenen del dialecte i viuen a dialectes_col/.

    camp     0        1      2      3          4      5     6
             paraula  lema   codi   síl·labes  Vicc   Viq   Diec
    columna  col_0    col_1  col_2  col_5      col_6  col_7  col_8

Els números de columna són els de sempre i hi ha forats (3, 4 i 9): el
navegador, les llistes i el joc les demanen pel nom del fitxer, i renumerar-les
voldria dir tocar-ho tot per no guanyar res.

JA NO CREA CAP RIMA, tot i el nom del fitxer (que es queda perquè és el que
criden els workflows). La rima la fa el generar_dialectes.py a partir de la
transcripció de cada dialecte, un sol cop i per a tots. Abans el càlcul era
escrit aquí i al "separar_arxiu", amb un comentari a cada banda demanant que no
divergissin.

Aquest script NO escriu cap col_N.txt: les que es baixa el navegador les fa el
generar_columnes_publicades.py a partir del diccionari que digui config.py, que
pot no ser aquest.
"""

import os
import sys

# Aquest script viu a diccionaris/python/ però escriu a diccionaris/. Les rutes
# es calculen des d'on és el fitxer i no des d'on s'executa: abans eren relatives
# a la carpeta de treball, i com que aquest script SOBREESCRIU el diccionari
# base, una carpeta de treball equivocada volia dir escriure'l en un lloc que no
# toca.
DIR_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if DIR_SCRIPTS not in sys.path:
    sys.path.insert(0, DIR_SCRIPTS)

# D'aquí surt on és la transcripció del central i com es diu.
from generar_dialectes import CENTRAL, cami as cami_dialecte

BASE = os.path.dirname(DIR_SCRIPTS)

DICCIONARI = os.path.join(BASE, "diccionari.5.2.3.txt")
COL_10 = os.path.join(BASE, "separat", "col_10 (canvis aquí)", "col_10provisional.txt")
TRANSCRIPCIO = cami_dialecte(CENTRAL, 9)

# Els camps que la columna 10 NO porta: síl·labes i els tres enllaços. Surten
# del diccionari que ja hi ha, fila per fila.
CAMPS_DEL_DICCIONARI = (3, 4, 5, 6)

with open(COL_10, "r", encoding="utf-8") as doc:
    linies = [linia.strip() for linia in doc if "€" in linia]

paraules = []
donve = []
codis = []
transcripcions = []

for linia in linies:
    parts = linia.split(" € ")
    if len(parts) >= 4:
        paraules.append(parts[0])
        donve.append(parts[1])
        codis.append(parts[2])
        transcripcions.append(parts[3])
    else:
        print("Línia amb format incorrecte:", linia)

print("Es comença a fer diccionari")

with open(DICCIONARI, "r", encoding="utf-8") as doc:
    velles = [linia.rstrip("\n").split("$") for linia in doc if linia.strip()]

# Xarxa de seguretat. Aquest script no regenera les síl·labes ni els enllaços:
# els pren del diccionari d'abans, fila per fila. Si a la columna 10 s'hi ha
# afegit o tret cap línia, tot el que ve de sota es desplaça i cada paraula
# hereta les síl·labes d'una altra, sense que res no se'n queixi.
#
# Abans qui ho enxampava era el generar_versions.py, perquè les columnes
# quedaven de mides diferents. Ara totes surten d'un sol fitxer i sempre van a
# l'una, o sigui que la comprovació ha de ser aquí.
if len(velles) != len(paraules):
    raise SystemExit(
        f"La columna 10 té {len(paraules)} files i el diccionari en té {len(velles)}.\n"
        "Aquest script no regenera les síl·labes ni els enllaços (camps 3 a 6):\n"
        "els pren del diccionari fila per fila, i així quedarien desplaçats.\n"
        "Si hi has afegit o tret paraules, cal passar pel diccionari general."
    )

with open(DICCIONARI, "w", encoding="utf-8") as f:
    for i in range(len(paraules)):
        f.write("$".join([
            paraules[i],              # 0 paraula
            donve[i],                 # 1 d'on ve
            codis[i],                 # 2 codi
            *(velles[i][c] for c in CAMPS_DEL_DICCIONARI),   # 3-6 síl·labes i enllaços
        ]) + "\n")

print(f"Fet! (diccionari creat, {len(paraules)} files)")

# La transcripció editada se'n va al dialecte central, que és d'on la torna a
# treure el separar_arxiu per refer la columna 10 i d'on el generar_dialectes.py
# en fa la rima. Sense salt de línia al final, com totes les columnes.
#
# Si no s'escrivís aquí, una transcripció corregida per la columna 10 es
# perdria: al diccionari ja no hi ha cap camp on desar-la.
with open(TRANSCRIPCIO, "w", encoding="utf-8") as f:
    f.write("\n".join(transcripcions))

print(f"Fet! (transcripció del central desada a {os.path.relpath(TRANSCRIPCIO, os.path.dirname(BASE))})")
