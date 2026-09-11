"""
Quin diccionari es publica. Aquest fitxer és L'INTERRUPTOR.

D'aquí surt de quin diccionari es fan les columnes que es baixa el navegador:
separat/col_0..col_9, separat/internat/ i versions.json.

    DICCIONARI_PUBLICAT = "diccionari.6.txt"       el diccionari amb les formes
                                                   amb pronom (el d'ara)
    DICCIONARI_PUBLICAT = DICCIONARI_BASE          el diccionari de sempre,
                                                   sense formes amb pronom

Canviant aquesta línia i prou ja està: si el que es publica és el diccionari
base, el workflow se salta la generació dels pronoms i del v.6, perquè les
columnes ja les hi haurà deixat fetes qui ha separat el diccionari. No cal
tocar cap altre fitxer ni cap workflow.

EL DICCIONARI BASE NO ES TOCA MAI amb aquest interruptor. És el que s'edita a
mà, del qual surt la columna 10 i del qual parteixen les formes
amb pronom. Publicar-ne un altre no el fa desaparèixer: continua sent l'origen
de tot.
"""

import os
import sys

DIR_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if DIR_SCRIPTS not in sys.path:
    sys.path.insert(0, DIR_SCRIPTS)

import camins

# El diccionari que s'edita a mà. L'origen de tot.
DICCIONARI_BASE = "diccionari.5.2.3.txt"

# El diccionari que es publica: d'aquest en surten les columnes del web.
DICCIONARI_PUBLICAT = DICCIONARI_BASE

# Tots dos viuen a diccionaris/. El camí surt de camins.py perquè n'hi hagi un
# de sol per a tothom.
BASE = camins.BASE

CAMI_BASE = os.path.join(BASE, DICCIONARI_BASE)
CAMI_PUBLICAT = os.path.join(BASE, DICCIONARI_PUBLICAT)

# Cal generar les formes amb pronom i ajuntar el v.6? Només si el que es
# publica no és ja el diccionari base.
CAL_V6 = DICCIONARI_PUBLICAT != DICCIONARI_BASE


def main():
    """
    Escriu l'interruptor en el format de sortides de GitHub Actions, perquè el
    workflow sàpiga quins passos se salta sense haver de repetir enlloc més
    quin diccionari es publica.

        python diccionaris/python/config.py >> "$GITHUB_OUTPUT"
    """
    print(f"base={DICCIONARI_BASE}")
    print(f"publicat={DICCIONARI_PUBLICAT}")
    print(f"cal_v6={'true' if CAL_V6 else 'false'}")


if __name__ == "__main__":
    main()
