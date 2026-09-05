"""
Les paraules que no rimen amb res, una llista per dialecte.

    python3 llistes/generar_naufragues.py

    diccionaris/separat/col_*            ─┐
    <codi>/trans_dicc/col_3_rimacons_*    │ -> paraules_naufragues_<codi>.json
    <codi>/apendix/col_*_<codi>          ─┘

LES DUES MEITATS D'UN DIALECTE COMPTEN, i han de comptar juntes: una paraula
del diccionari pot deixar de ser nàufraga perquè li rima una forma pròpia del
dialecte, i una forma pròpia pot ser nàufraga o no segons què hi hagi al
diccionari. Comptar-les per separat donaria dues llistes que no són cap de les
dues. D'on surt cada columna ho diu fonts.py.
"""

import os
import json

import fonts
from versions import actualitzar_versio

# Les vuit columnes que necessita la llista, en l'ordre en què es desempaqueten.
# La col_3 (rima) va al mig i no al seu lloc numèric: és l'ordre de sempre del
# JSON de sortida i el que llegeix llistes/llista_naufragues.html.
COLUMNES = (0, 1, 2, 3, 5, 6, 7, 8)


def rimes_amb_una_sola_paraula(parts):
    """
    Les rimes que només tenen UNA paraula diferent: les nàufragues.

    Abans això sortia d'un fitxer que es generava a part i que ja no existeix,
    el bot/resultat_ordenat_cons.json. Era el mateix recompte, però el del dia
    que s'hagués generat aquell fitxer: buscar les nàufragues d'un diccionari
    en un altre, i sortien paraules que sí que rimen amb alguna cosa.
    Comptant-ho aquí, es compta sobre les columnes d'aquesta passada.

    "Una sola paraula DIFERENT" i no pas "una sola fila", igual que abans: una
    rima amb tres files de la mateixa paraula (homògrafes de codi diferent)
    també és nàufraga, perquè no rima amb res que no sigui ella mateixa.

    Es compta amb un diccionari de rimes i prou (85.914 entrades), i no pas
    guardant totes les paraules de cada rima: sobre el diccionari publicat
    això últim voldria dir tenir-ne quatre milions a la memòria. Per això
    també es llegeixen només les dues columnes que diuen qui rima amb qui.
    """
    on_es_la_paraula = COLUMNES.index(0)
    on_es_la_rima = COLUMNES.index(3)

    primera = {}
    amb_mes_duna = set()

    for _, rutes in parts:
        for paraula, rima in fonts.files_de([rutes[on_es_la_paraula],
                                             rutes[on_es_la_rima]]):
            if not rima:
                continue
            if rima not in primera:
                primera[rima] = paraula
            elif primera[rima] != paraula:
                amb_mes_duna.add(rima)

    return set(primera) - amb_mes_duna


def generar_dialecte(base_dir, codi):
    """Les nàufragues d'UN dialecte.

    Ser nàufraga depèn de com es parli: qui no rima amb ningú en central pot
    rimar amb algú en valencià, on la a i la e àtones finals no es confonen. I
    depèn també de quines paraules hi ha, que tampoc no són les mateixes.

    El codi va DINS del nom del fitxer de sortida i no només en una carpeta, per
    la mateixa raó que a les columnes de rima (vegeu camins.py): la memòria cau
    del navegador s'indexa pel nom del fitxer sol —llegirFitxerAmbIndexedDB de
    js/script.js fa rutaFitxer.split("/").pop()— i quatre
    paraules_naufragues.json serien la mateixa entrada.
    """
    nom_sortida = f'paraules_naufragues_{codi}.json'
    fitxer_sortida = os.path.join(base_dir, nom_sortida)

    parts = fonts.parts_del_dialecte(codi, COLUMNES)
    rimes_naufragues = rimes_amb_una_sola_paraula(parts)

    paraules_orfes = []
    de_lapendix = 0

    for don_ve, rutes in parts:
        for fila in fonts.files_de(rutes):
            paraula, infinitiu, codi_gramatical, rima, sil, vicc, viq, diec = fila
            if rima not in rimes_naufragues:
                continue
            paraules_orfes.append({
                'paraula': paraula,
                'infinitiu': infinitiu,
                'codi': codi_gramatical,
                'rimacons': rima,
                'sil': sil,
                'vicc': vicc,
                'viq': viq,
                'diec': diec,
            })
            if don_ve == 'apendix':
                de_lapendix += 1

    with open(fitxer_sortida, 'w', encoding='utf-8') as f:
        json.dump(paraules_orfes, f, ensure_ascii=False, indent=2)

    actualitzar_versio(nom_sortida, fitxer_sortida)

    return nom_sortida, len(paraules_orfes), de_lapendix


def generar_llista():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    codis = fonts.dialectes()
    if not codis:
        print("Error: no hi ha cap dialecte a dialectes_col/.")
        return

    for codi in codis:
        try:
            nom, quantes, de_lapendix = generar_dialecte(base_dir, codi)
        except FileNotFoundError as e:
            # Un dialecte a mitges (carpeta feta, rima encara no generada) no ha
            # de tombar els altres: es diu i es continua.
            print(f"  {codi}: falta algun arxiu, es deixa per a la propera. {e}")
            continue
        except Exception as e:
            print(f"  {codi}: error inesperat processant els arxius: {e}")
            continue

        print(f"  {codi}: {quantes} paraules nàufragues guardades a {nom}"
              + (f" ({de_lapendix} de l'apendix)" if de_lapendix else ""))

    print("Generació completada.")


if __name__ == "__main__":
    generar_llista()
