"""
Parteix el diccionari que es publica en les deu columnes del web.

    python3 generar_columnes_publicades.py

Quin diccionari es publica ho diu config.py, que és l'interruptor. Per defecte
és el diccionari.6.txt (amb les formes amb pronom).

ÉS L'ÚNIC QUE ESCRIU LES col_0..col_9. Abans les feien també el separar_arxiu
i el creador_rima, a partir del diccionari base, i tot seguit aquest les
reescrivia: 42 MB escrits per no res. Ara aquells dos només fan el que només
poden fer ells:

    separar_arxiu.py     diccionari BASE     -> col_10 (canvis aquí)
    creador_rima.py      col_10              -> diccionari BASE
    aquest               diccionari PUBLICAT -> col_0..col_9

La columna 10 és la font que s'edita a mà i ha de continuar sortint del
diccionari BASE. Si la fes el publicat, es convertiria en quatre milions de
línies repartides en cinc-cents fitxers i deixaria de servir per a res.

Llegeix i escriu línia per línia, sense carregar-se el diccionari a la
memòria: el v.6 fa 324 MB i el separar_arxiu, que sí que se'l carrega sencer,
hi necessitaria uns quants gigabytes.
"""

import os
import sys

DIR_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if DIR_SCRIPTS not in sys.path:
    sys.path.insert(0, DIR_SCRIPTS)

import config

DIRECTORI_COLUMNES = os.path.join(config.BASE, "separat")

CAMPS = 10


def mil(n):
    """4025866 -> '4.025.866', com els números de la documentació."""
    return f"{n:,}".replace(",", ".")


def partir(cami_diccionari, directori_sortida):
    """
    Escriu col_0.txt .. col_9.txt a partir d'un diccionari de deu camps.

    Les columnes se separen amb salts de línia però NO acaben amb salt de
    línia, exactament com les deixa el separar_arxiu. No és cap caprici: el
    navegador fa contingut.split('\\n') sense filtrar res (js/script.js:426),
    i un salt final li afegiria una fila buida al final de la columna, que
    quedaria desquadrada amb les altres nou.
    """
    os.makedirs(directori_sortida, exist_ok=True)

    sortides = [open(os.path.join(directori_sortida, f"col_{i}.txt"),
                     "w", encoding="utf-8") for i in range(CAMPS)]
    linies = 0
    try:
        with open(cami_diccionari, "r", encoding="utf-8") as entrada:
            for linia in entrada:
                camps = linia.rstrip("\n").split("$")
                if len(camps) != CAMPS:
                    raise SystemExit(
                        f"{cami_diccionari}, línia {linies + 1}: hi ha "
                        f"{len(camps)} camps i n'hi ha d'haver {CAMPS}.\n"
                        f"  {linia[:120]!r}"
                    )
                for i, camp in enumerate(camps):
                    if linies:
                        sortides[i].write("\n")
                    sortides[i].write(camp)
                linies += 1
    finally:
        for sortida in sortides:
            sortida.close()

    if not linies:
        raise SystemExit(f"{cami_diccionari} és buit: no s'ha generat cap columna.")
    return linies


def main():
    if not os.path.exists(config.CAMI_PUBLICAT):
        raise SystemExit(
            f"No hi ha {config.CAMI_PUBLICAT}.\n"
            "És el diccionari que diu config.py que s'ha de publicar. Si és el "
            "v.6, el genera pronoms/ajuntar_diccionari_6.py."
        )

    print(f"Publicant {config.DICCIONARI_PUBLICAT} a separat/col_0..col_9")
    linies = partir(config.CAMI_PUBLICAT, DIRECTORI_COLUMNES)
    print(f"Fet! {mil(linies)} files a cada una de les {CAMPS} columnes")
    print("     (la columna 10 no s'hi toca: surt del diccionari base)")


if __name__ == "__main__":
    main()
