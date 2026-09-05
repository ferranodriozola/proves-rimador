"""
Els mots de set síl·labes: un vers sencer en una paraula.

    python3 llistes/generar_mots_de7_real.py  ->  mots_de7_real.json

ÉS LA LLISTA DEL CENTRAL, i n'hi ha una de sola. Les síl·labes són un
recompte ORTOGRÀFIC i per tant no depenen de com es parli, però la rima que
s'ensenya al costat de cada paraula sí, i les paraules pròpies de cada
dialecte tampoc no són les mateixes. Mentre la pàgina no tingui tira de
dialectes (llistes/llista_mots_de7.html), es fa la del central i prou; el dia
que en tingui, això és un bucle per fonts.dialectes() i un fitxer per codi,
com a generar_naufragues.py.

Hi entren les DUES meitats del central: el diccionari i les paraules pròpies
d'aquell dialecte. D'on surt cada columna ho diu fonts.py.
"""

import os
import json

import fonts
from versions import actualitzar_versio

# El dialecte del qual es fa la llista. Vegeu la capçalera: mentre n'hi hagi
# una de sola, és el central.
DIALECTE = 'ca'

# paraula, infinitiu, codi, rima consonant, síl·labes, Vicc, Viq, DIEC.
COLUMNES = (0, 1, 2, 3, 5, 6, 7, 8)

SILABES = 7


def generar_llista():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fitxer_sortida = os.path.join(base_dir, 'mots_de7_real.json')

    try:
        parts = fonts.parts_del_dialecte(DIALECTE, COLUMNES)
    except FileNotFoundError as e:
        print(f"Error: No s'han trobat els arxius necessaris. {e}")
        return

    mots_de7 = []
    de_lapendix = 0

    try:
        for don_ve, rutes in parts:
            for fila in fonts.files_de(rutes):
                paraula, infinitiu, codi, rima, sil, vicc, viq, diec = fila
                if sil != str(SILABES):
                    continue
                mots_de7.append({
                    'paraula': paraula,
                    'infinitiu': infinitiu,
                    'codi': codi,
                    'rimacons': rima,
                    'sil': sil,
                    'vicc': vicc,
                    'viq': viq,
                    'diec': diec,
                })
                if don_ve == 'apendix':
                    de_lapendix += 1
    except Exception as e:
        print(f"Error inesperat processant els arxius: {e}")
        return

    with open(fitxer_sortida, 'w', encoding='utf-8') as f:
        json.dump(mots_de7, f, ensure_ascii=False, indent=2)

    print(f"Generació completada: {len(mots_de7)} paraules de {SILABES} síl·labes "
          f"guardades a {fitxer_sortida}"
          + (f" ({de_lapendix} de l'apendix del '{DIALECTE}')" if de_lapendix else ""))

    actualitzar_versio('mots_de7_real.json', fitxer_sortida)


if __name__ == "__main__":
    generar_llista()
