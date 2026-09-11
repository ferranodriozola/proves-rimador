"""
Els mots que fan un vers de glosa sencer ells sols.

    python3 llistes/generar_mots_de7_glosa.py  ->  mots_de7_glosa.json

Un vers de set síl·labes es compta fins a l'última tònica: per tant hi valen
les agudes de 7, les planes de 8 i les esdrúixoles de 9. On és la tònica ho
diu la transcripció, i per això aquesta llista sí que depèn de com es parli.

ÉS LA LLISTA DEL CENTRAL, i n'hi ha una de sola, com la de
generar_mots_de7_real.py. Compte que la glosa és mallorquina i que la llista
del balear no seria aquesta: hi ha paraules que en central són planes i en
balear no, i el balear té a més les seves formes pròpies. Mentre la pàgina no
tingui tira de dialectes, es fa la del central; el dia que en tingui, això és
un bucle per fonts.dialectes().

Hi entren les DUES meitats del central: el diccionari i les paraules pròpies
d'aquell dialecte. D'on surt cada columna ho diu fonts.py.
"""

import os
import json
import re

import fonts
from versions import actualitzar_versio

# Vegeu la capçalera: mentre n'hi hagi una de sola, és la del central.
DIALECTE = 'ca'

# paraula, infinitiu, codi, rima consonant, síl·labes, Vicc, Viq, DIEC i la
# transcripció, que és d'on surt on cau la tònica.
COLUMNES = (0, 1, 2, 3, 5, 6, 7, 8, 9)

# Quantes síl·labes ha de tenir la paraula per a cada mena d'accent.
CAP_A_SET = {'aguda': 7, 'plana': 8, 'esdruixola': 9}

VOCALS = re.compile(r'[aɛeioɔuə]')


def obtenir_accent_fonetic(transcripcio):
    accents = [m.start() for m in re.finditer(r'ˈ', transcripcio)]

    if not accents:
        return 'aguda'

    pos_accent = accents[-1]
    quantes_vocals = len(VOCALS.findall(transcripcio[pos_accent:]))

    if quantes_vocals == 1:
        return 'aguda'
    elif quantes_vocals == 2:
        return 'plana'
    else:
        return 'esdruixola'


def generar_llista():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fitxer_sortida = os.path.join(base_dir, 'mots_de7_glosa.json')

    try:
        parts = fonts.parts_del_dialecte(DIALECTE, COLUMNES)
    except FileNotFoundError as e:
        print(f"Error: falten arxius essencials. {e}")
        return

    mots_filtrats = []
    de_lapendix = 0

    for don_ve, rutes in parts:
        for fila in fonts.files_de(rutes):
            paraula, infinitiu, codi, rima, sil, vicc, viq, diec, transcripcio = fila

            if not sil.isdigit() or not paraula or not transcripcio:
                continue

            accent = obtenir_accent_fonetic(transcripcio)
            if CAP_A_SET.get(accent) != int(sil):
                continue

            mots_filtrats.append({
                'paraula': paraula,
                'infinitiu': infinitiu,
                'codi': codi,
                'rimacons': rima,
                'sil': sil,
                'accent': accent,
                'fonetica': transcripcio,
                'vicc': vicc,
                'viq': viq,
                'diec': diec,
            })
            if don_ve == 'apendix':
                de_lapendix += 1

    with open(fitxer_sortida, 'w', encoding='utf-8') as f:
        json.dump(mots_filtrats, f, ensure_ascii=False, indent=2)

    print(f"Generació completada: {len(mots_filtrats)} paraules guardades a "
          f"{fitxer_sortida}"
          + (f" ({de_lapendix} de l'apendix del '{DIALECTE}')" if de_lapendix else ""))

    actualitzar_versio('mots_de7_glosa.json', fitxer_sortida)


if __name__ == '__main__':
    generar_llista()
