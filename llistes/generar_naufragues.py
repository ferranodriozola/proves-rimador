import os
import json
from contextlib import ExitStack

from versions import actualitzar_versio

# Els codis de dialecte són les subcarpetes de dialectes_col/, la mateixa regla
# que fa servir dialectes() a diccionaris/python/camins.py: un dialecte nou és
# una carpeta amb la seva rima a dins i no es declara enlloc. Aquí no s'importa
# aquell mòdul a posta —els scripts de llistes/ van sols i no depenen del
# paquet del diccionari—, però la regla ha de ser la mateixa.
def dialectes(dir_dialectes):
    return sorted(
        nom for nom in os.listdir(dir_dialectes)
        if os.path.isdir(os.path.join(dir_dialectes, nom)) and not nom.startswith('.')
    )


def rimes_amb_una_sola_paraula(ruta_paraules, ruta_rimes):
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
    això últim voldria dir tenir-ne quatre milions a la memòria.
    """
    primera = {}
    amb_mes_duna = set()
    with open(ruta_paraules, 'r', encoding='utf-8') as fp, \
         open(ruta_rimes, 'r', encoding='utf-8') as fr:
        for linia_paraula, linia_rima in zip(fp, fr):
            rima = linia_rima.strip()
            if not rima:
                continue
            paraula = linia_paraula.strip()
            if rima not in primera:
                primera[rima] = paraula
            elif primera[rima] != paraula:
                amb_mes_duna.add(rima)
    return set(primera) - amb_mes_duna


def generar_dialecte(base_dir, dir_separat, dir_dialectes, codi):
    """Les nàufragues d'UN dialecte.

    Ser nàufraga depèn de com es parli: qui no rima amb ningú en central pot
    rimar amb algú en valencià, on la a i la e àtones finals no es
    confonen. L'única cosa que canvia d'un dialecte a l'altre és la columna de
    rima; la paraula, el lema, el codi, les síl·labes i els enllaços són els
    mateixos i continuen sortint de separat/.

    El codi va DINS del nom del fitxer de sortida i no només en una carpeta, per
    la mateixa raó que a les columnes de rima (vegeu camins.py): la memòria cau
    del navegador s'indexa pel nom del fitxer sol —llegirFitxerAmbIndexedDB de
    js/script.js fa rutaFitxer.split("/").pop()— i quatre
    paraules_naufragues.json serien la mateixa entrada.
    """
    nom_sortida = f'paraules_naufragues_{codi}.json'
    fitxer_sortida = os.path.join(base_dir, nom_sortida)
    ruta_rima = os.path.join(dir_dialectes, codi, f'col_3_rimacons_{codi}.txt')

    noms_fitxers = ['col_0.txt', 'col_1.txt', 'col_2.txt', 'col_5.txt', 'col_6.txt', 'col_7.txt', 'col_8.txt']
    rutes_txt = [os.path.join(dir_separat, nom) for nom in noms_fitxers]
    rutes_txt.insert(3, ruta_rima)   # va on anava la col_3, que és l'ordre en què es desempaqueten

    paraules_orfes = []

    rimes_naufragues = rimes_amb_una_sola_paraula(
        os.path.join(dir_separat, 'col_0.txt'),
        ruta_rima,
    )

    with ExitStack() as stack:
        fitxers_oberts = [stack.enter_context(open(ruta, 'r', encoding='utf-8')) for ruta in rutes_txt]

        for linies in zip(*fitxers_oberts):
            paraula, infinitiu, codi_gramatical, rima, sil, vicc, viq, diec = [linia.strip() for linia in linies]

            if rima in rimes_naufragues:
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

    with open(fitxer_sortida, 'w', encoding='utf-8') as f:
        json.dump(paraules_orfes, f, ensure_ascii=False, indent=2)

    actualitzar_versio(nom_sortida, fitxer_sortida)

    return nom_sortida, len(paraules_orfes)


def generar_llista():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dir_diccionaris = os.path.join(base_dir, '..', 'diccionaris')
    dir_separat = os.path.join(dir_diccionaris, 'separat')
    dir_dialectes = os.path.join(base_dir, '..', 'dialectes_col')

    try:
        codis = dialectes(dir_dialectes)
    except FileNotFoundError as e:
        print(f"Error: no s'ha trobat la carpeta dels dialectes. {e}")
        return

    if not codis:
        print("Error: no hi ha cap dialecte a dialectes_col/.")
        return

    for codi in codis:
        try:
            nom, quantes = generar_dialecte(base_dir, dir_separat, dir_dialectes, codi)
        except FileNotFoundError as e:
            # Un dialecte a mitges (carpeta feta, rima encara no generada) no ha
            # de tombar els altres: es diu i es continua.
            print(f"  {codi}: falta algun arxiu, es deixa per a la propera. {e}")
            continue
        except Exception as e:
            print(f"  {codi}: error inesperat processant els arxius: {e}")
            continue

        print(f"  {codi}: {quantes} paraules nàufragues guardades a {nom}")

    print("Generació completada.")


if __name__ == "__main__":
    generar_llista()
