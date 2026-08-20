"""
Parteix el diccionari que es publica en les deu columnes del web.

    python3 generar_columnes_publicades.py

Quin diccionari es publica ho diu config.py, que és l'interruptor. Per defecte
és el diccionari.6.txt (amb les formes amb pronom).

EL DICCIONARI JA NO PORTA NI RIMA NI TRANSCRIPCIÓ. Són set camps, no deu: la
rima consonant, l'assonant i la transcripció depenen del dialecte i viuen a
dialectes_col/<codi>/. Aquí només se'n fan les columnes que són iguals es parli
com es parli.

    camp del fitxer   0        1      2       3          4       5      6
    columna del web   col_0    col_1  col_2   col_5      col_6   col_7  col_8
                      paraula  lema   codi    síl·labes  Vicc    Viq    Diec

Els números de columna són els de sempre i hi ha forats (3, 4 i 9): el
navegador, les llistes i el joc les demanen pel nom del fitxer, i renumerar-les
voldria dir tocar-ho tot per no guanyar res.

    sincronitzar_dialectes.py  diccionari (editat a mà) -> els col_9 el segueixen
    aplicar_col_10.py          col_10.txt               -> dialectes_col/*/col_9
    aquest                     diccionari PUBLICAT      -> col_0,1,2,5,6,7,8
    generar_dialectes.py       dialectes_col/*/col_9    -> col_3 i col_4

La columna 10 és la font que s'edita a mà i ha de continuar sortint del
diccionari BASE. Si la fes el publicat, es convertiria en quatre milions de
línies repartides en cinc-cents fitxers i deixaria de servir per a res.

Llegeix i escriu línia per línia, sense carregar-se el diccionari a la
memòria: el v.6 fa 324 MB, i carregar-se'l sencer voldria dir uns quants
gigabytes.
"""

import os
import sys

DIR_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if DIR_SCRIPTS not in sys.path:
    sys.path.insert(0, DIR_SCRIPTS)

import config

DIRECTORI_COLUMNES = os.path.join(config.BASE, "separat")

# Quin camp del diccionari va a quina columna del web. L'ordre és el del
# fitxer; el número, el nom de la columna que en surt.
COLUMNES = (0, 1, 2, 5, 6, 7, 8)
CAMPS = len(COLUMNES)


def mil(n):
    """4025866 -> '4.025.866', com els números de la documentació."""
    return f"{n:,}".replace(",", ".")


def partir(cami_diccionari, directori_sortida):
    """
    Escriu una col_N.txt per cada camp del diccionari, amb els números de
    COLUMNES.

    Les columnes se separen amb salts de línia però NO acaben amb salt de
    línia. No és cap caprici: el
    navegador fa contingut.split('\\n') sense filtrar res (js/script.js:426),
    i un salt final li afegiria una fila buida al final de la columna, que
    quedaria desquadrada amb les altres nou.
    """
    os.makedirs(directori_sortida, exist_ok=True)

    sortides = [open(os.path.join(directori_sortida, f"col_{n}.txt"),
                     "w", encoding="utf-8") for n in COLUMNES]
    linies = 0
    try:
        with open(cami_diccionari, "r", encoding="utf-8") as entrada:
            for linia in entrada:
                camps = linia.rstrip("\n").split("$")
                if len(camps) != CAMPS:
                    raise SystemExit(
                        f"{cami_diccionari}, línia {linies + 1}: hi ha "
                        f"{len(camps)} camps i n'hi ha d'haver {CAMPS}.\n"
                        "  (el diccionari ja no porta ni la rima ni la "
                        "transcripció: són a dialectes_col/)\n"
                        f"  {linia[:120]!r}"
                    )
                for sortida, camp in zip(sortides, camps):
                    if linies:
                        sortida.write("\n")
                    sortida.write(camp)
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

    noms = ", ".join(f"col_{n}" for n in COLUMNES)
    print(f"Publicant {config.DICCIONARI_PUBLICAT} a separat/{{{noms}}}")
    linies = partir(config.CAMI_PUBLICAT, DIRECTORI_COLUMNES)
    print(f"Fet! {mil(linies)} files a cada una de les {CAMPS} columnes")
    print("     (la col_3, la col_4 i la col_9 les fa el generar_dialectes.py;")
    print("      la columna 10 no s'hi toca: surt del diccionari base)")


if __name__ == "__main__":
    main()
