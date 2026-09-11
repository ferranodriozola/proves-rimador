"""
D'on surten les columnes que llegeixen les llistes.

Un dialecte són DUES llistes de paraules i les llistes han de beure de totes
dues:

    el trans_dicc   el diccionari sencer, dit en aquell dialecte. La paraula,
                    el lema, el codi, les síl·labes i els enllaços surten de
                    diccionaris/separat/ (són els mateixos per a tothom); la
                    rima i la transcripció, de dialectes_col/<codi>/trans_dicc/
    l'apendix       les paraules que només es diuen allà ("cante", "servisc",
                    "tenc"). Totes les columnes són seves i viuen a
                    dialectes_col/<codi>/apendix/

Cada meitat té la seva llargada i no es poden concatenar columna a columna:
el que es concatena són les FILES, i per això aquí es torna una llista de
parts i no pas una llista de rutes.

AIXÒ NO ÉS diccionaris/python/camins.py, i és a posta: els scripts de llistes/
van sols i no depenen del paquet del diccionari (el workflow els corre des
d'aquesta carpeta). Però la regla és la mateixa i han de dir el mateix; si un
dia les columnes es tornen a moure, s'han de moure aquí i allà.
"""

import os

ARREL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEPARAT = os.path.join(ARREL, 'diccionaris', 'separat')
DIALECTES_COL = os.path.join(ARREL, 'dialectes_col')

# El nom que duu cada columna de dialecte dins del trans_dicc. A l'apendix no
# el duen: allà tots els fitxers es diuen col_<n>_<codi>.txt i prou.
NOMS = {3: 'rimacons', 4: 'rimaass', 9: 'transcripcio'}

# Les que surten del diccionari i són iguals a tots els dialectes.
DEL_DICCIONARI = (0, 1, 2, 5, 6, 7, 8)


def dialectes():
    """Els codis, que són les subcarpetes de dialectes_col/, la mateixa regla
    que fa servir dialectes() a diccionaris/python/camins.py: un dialecte nou
    és una carpeta amb la seva rima a dins i no es declara enlloc."""
    if not os.path.isdir(DIALECTES_COL):
        return []
    return sorted(
        nom for nom in os.listdir(DIALECTES_COL)
        if os.path.isdir(os.path.join(DIALECTES_COL, nom)) and not nom.startswith('.')
    )


def te_apendix(codi):
    return os.path.isdir(os.path.join(DIALECTES_COL, codi, 'apendix'))


def _ruta_del_trans_dicc(codi, numero):
    if numero in DEL_DICCIONARI:
        return os.path.join(SEPARAT, f'col_{numero}.txt')
    return os.path.join(DIALECTES_COL, codi, 'trans_dicc',
                        f'col_{numero}_{NOMS[numero]}_{codi}.txt')


def _ruta_de_lapendix(codi, numero):
    return os.path.join(DIALECTES_COL, codi, 'apendix', f'col_{numero}_{codi}.txt')


def parts_del_dialecte(codi, columnes):
    """Les rutes de les columnes demanades, per a cada meitat del dialecte.

    Torna [(nom, [ruta, ...]), ...] amb les rutes en l'ordre de "columnes". Un
    dialecte sense apendix en torna una de sola, i la llista li surt igual: no
    tots els dialectes tenen paraules pròpies.

    Peta si en falta cap: una llista feta a mitges és pitjor que cap llista,
    perquè no es nota.
    """
    parts = [('diccionari', [_ruta_del_trans_dicc(codi, n) for n in columnes])]
    if te_apendix(codi):
        parts.append(('apendix', [_ruta_de_lapendix(codi, n) for n in columnes]))

    for _, rutes in parts:
        for ruta in rutes:
            if not os.path.exists(ruta):
                raise FileNotFoundError(ruta)
    return parts


def files_de(rutes):
    """Les files d'un grup de columnes, ja partides i sense espais.

    El zip() para a la columna més curta: si una anés desquadrada, les files de
    més no es mirarien. Que quadrin ho comprova diccionaris/python/versions.py,
    que és qui pot aturar la publicació.
    """
    from contextlib import ExitStack
    with ExitStack() as pila:
        oberts = [pila.enter_context(open(ruta, 'r', encoding='utf-8')) for ruta in rutes]
        for linies in zip(*oberts):
            yield [linia.strip() for linia in linies]


def files_del_dialecte(codi, columnes):
    """Totes les files d'un dialecte, les del diccionari i les de l'apendix
    seguides. Torna (d'on ve la fila, [valors]) perquè qui compti pugui dir-ho."""
    for nom, rutes in parts_del_dialecte(codi, columnes):
        for fila in files_de(rutes):
            yield nom, fila
