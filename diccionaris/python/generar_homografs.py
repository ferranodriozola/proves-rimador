"""
Les transcripcions que el navegador necessita de debò: només les de les
paraules que s'escriuen igual però NO sonen igual.

    python3 generar_homografs.py    ->  diccionaris/separat/homografs.txt

PER QUÈ EXISTEIX AIXÒ

Quan cerques una paraula que surt més d'un cop al diccionari, el web ha de
decidir si les entrades es pronuncien totes igual (i llavors tant se val quina
agafi) o no (i llavors t'ho ha de preguntar amb el diàleg d'homògrafs).

Per saber-ho es baixava la col_9 SENCERA. Amb el diccionari base ja eren 9,8 MB
per respondre un sí o un no; amb el publicat d'ara són 72,9 MB i quatre milions
de cadenes de text, i el navegador es queda penjat amb el loader. I la immensa
majoria de vegades la resposta és "totes sonen igual", o sigui que tota aquella
feina no servia per a res.

Aquí es desa només el 2,37 % de les files que pot canviar la resposta: les de
les paraules que tenen dues transcripcions diferents o més. Són 1,7 MB.

    paraula que no surt al fitxer  ->  totes les seves entrades sonen igual
    paraula que hi surt           ->  hi ha les transcripcions de cada fila

La lògica del navegador no canvia gens: allà on abans mirava array9[fila], ara
mira aquest mapa. Per a les paraules que sonen totes igual no en treu res, i un
conjunt de "res" té una sola entrada, que és exactament la resposta bona.

FORMAT: una línia per fila, "número_de_fila$transcripció". El número és la fila
del diccionari publicat, comptant des de 0, la mateixa que fan servir les
columnes.
"""

import os
import sys

DIR_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if DIR_SCRIPTS not in sys.path:
    sys.path.insert(0, DIR_SCRIPTS)

import config

DIRECTORI_COLUMNES = os.path.join(config.BASE, "separat")
FITXER_SORTIDA = os.path.join(DIRECTORI_COLUMNES, "homografs.txt")

COL_PARAULES = os.path.join(DIRECTORI_COLUMNES, "col_0.txt")
COL_TRANSCRIPCIONS = os.path.join(DIRECTORI_COLUMNES, "col_9.txt")


def mil(n):
    """95255 -> '95.255', com els números de la documentació."""
    return f"{n:,}".replace(",", ".")


def llegir(cami):
    """Les línies d'una columna, sense el salt final (que no és cap fila)."""
    with open(cami, "r", encoding="utf-8") as f:
        dades = f.read()
    if dades.endswith("\n"):
        dades = dades[:-1]
    return dades.split("\n")


def paraules_discrepants(paraules, transcripcions):
    """
    Les paraules que tenen dues transcripcions diferents o més.

    Es guarda la primera transcripció de cada paraula i prou, no pas totes:
    n'hi ha prou de veure'n una que no hi encaixi per saber que la paraula
    discrepa. Amb quatre milions de files, desar-les totes serien centenars de
    megabytes per a res.
    """
    primera = {}
    discrepants = set()
    for paraula, transcripcio in zip(paraules, transcripcions):
        anterior = primera.get(paraula)
        if anterior is None:
            primera[paraula] = transcripcio
        elif anterior != transcripcio:
            discrepants.add(paraula)
    return discrepants


def generar():
    paraules = llegir(COL_PARAULES)
    transcripcions = llegir(COL_TRANSCRIPCIONS)
    if len(paraules) != len(transcripcions):
        raise SystemExit(
            f"col_0.txt té {mil(len(paraules))} files i col_9.txt "
            f"{mil(len(transcripcions))}: no van a l'una."
        )

    discrepants = paraules_discrepants(paraules, transcripcions)

    linies = [f"{fila}${transcripcions[fila]}"
              for fila, paraula in enumerate(paraules)
              if paraula in discrepants]

    # Sense salt de línia al final, com les col_N.txt: el navegador munta la
    # llista comptant salts i una fila buida al final el faria ensopegar.
    with open(FITXER_SORTIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(linies))

    return len(paraules), len(discrepants), len(linies)


def main():
    total, paraules, files = generar()
    mida = os.path.getsize(FITXER_SORTIDA) / 1e6
    sencera = os.path.getsize(COL_TRANSCRIPCIONS) / 1e6
    print(f"Fet! {os.path.relpath(FITXER_SORTIDA, config.BASE)}")
    print(f"  {mil(paraules)} paraules que s'escriuen igual i sonen diferent")
    print(f"  {mil(files)} files de {mil(total)} ({files / total * 100:.2f} %)")
    print(f"  {mida:.2f} MB, en comptes dels {sencera:.1f} MB de la col_9 sencera")


if __name__ == "__main__":
    main()
