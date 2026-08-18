import os
import json
from contextlib import ExitStack

def rimes_amb_una_sola_paraula(ruta_paraules, ruta_rimes):
    """
    Les rimes que només tenen UNA paraula diferent: les nàufragues.

    Abans això sortia de bot/resultat_ordenat_cons.json, que és el mateix
    recompte fet pel generador_rimes_cons.py. Es compta aquí perquè aquell
    fitxer ja no es genera a cada passada, i fer servir el que hi hagués
    quedat voldria dir buscar les nàufragues d'un diccionari en un altre:
    sortirien paraules que sí que rimen amb alguna cosa.

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


def generar_llista():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dir_diccionaris = os.path.join(base_dir, '..', 'diccionaris')
    dir_separat = os.path.join(dir_diccionaris, 'separat')
    
    fitxer_sortida = os.path.join(base_dir, 'paraules_naufragues.json')
    ruta_versions = os.path.join(base_dir, 'versions_llistes.json')

    noms_fitxers = [
        'col_0.txt', 'col_1.txt', 'col_2.txt', 'col_3.txt', 'col_5.txt', 'col_6.txt', 'col_7.txt', 'col_8.txt'
    ]
    rutes_txt = [os.path.join(dir_separat, nom) for nom in noms_fitxers]

    paraules_orfes = []

    try:
        rimes_naufragues = rimes_amb_una_sola_paraula(
            os.path.join(dir_separat, 'col_0.txt'),
            os.path.join(dir_separat, 'col_3.txt'),
        )

        with ExitStack() as stack:
            fitxers_oberts = [stack.enter_context(open(ruta, 'r', encoding='utf-8')) for ruta in rutes_txt]
            
            for linies in zip(*fitxers_oberts):
                paraula, infinitiu, codi, rima, sil, vicc, viq, diec = [linia.strip() for linia in linies]

                if rima in rimes_naufragues:
                    paraules_orfes.append({
                        'paraula': paraula,
                        'infinitiu': infinitiu,
                        'codi': codi,
                        'rimacons': rima,
                        'sil': sil,
                        'vicc': vicc,
                        'viq': viq,
                        'diec': diec,
                    })

    except FileNotFoundError as e:
        print(f"Error: No s'han trobat els arxius necessaris. {e}")
        return
    except Exception as e:
        print(f"Error inesperat processant els arxius: {e}")
        return

    with open(fitxer_sortida, 'w', encoding='utf-8') as f:
        json.dump(paraules_orfes, f, ensure_ascii=False, indent=2)

    print(f"Generació completada: {len(paraules_orfes)} paraules nàufragues guardades a {fitxer_sortida}")

    try:
        with open(ruta_versions, 'r', encoding='utf-8') as fitxer:
            dades = json.load(fitxer)
            
        dades['versio_naufragues'] += 1
        
        with open(ruta_versions, 'w', encoding='utf-8') as fitxer:
            json.dump(dades, fitxer, indent=2)
            
    except FileNotFoundError:
        print(f"Avís: No s'ha trobat l'arxiu {ruta_versions}. Versió no actualitzada.")
    except Exception as e:
        print(f"Avís: Error en intentar actualitzar la versió: {e}")

if __name__ == "__main__":
    generar_llista()