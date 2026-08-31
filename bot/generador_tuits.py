"""D'on surten els tuits: quines rimes queden per dir i què hi diu cadascun.

Ho fa servir el programador manual (programador/servidor.py), que és l'única
manera com es publica ara. Abans hi havia dos bots que ho penjaven sols amb
l'API de Twitter (bot/script_normal.py i bot/script_naufragues.py, amb els
seus dos workflows): l'API val diners, la web de X deixa programar tuits de
franc, i es van esborrar. Al git hi són, si mai calen.

Això és a part del servidor a posta: aquí no hi ha res de HTTP ni de navegador,
només el diccionari i el text dels tuits, que és el que un dia es voldrà tornar
a llegir o a canviar.
"""

import json
import os
import random
import urllib.parse
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Les dues columnes d'on surten les rimes. Van fila per fila: la fila que fa
# 40 de la col_0 és una paraula i la que fa 40 de la col_3 és com rima. Les
# mateixes que llegeix rimes_amb_una_sola_paraula() a
# llistes/generar_naufragues.py.
FITXER_PARAULES = os.path.join(BASE_DIR, '..', 'diccionaris', 'separat', 'col_0.txt')
# La del CENTRAL: ara cada dialecte té la seva rima (i la seva llista de
# nàufragues, a llistes/), i això publica en central, com tota la resta.
FITXER_RIMACONS = os.path.join(BASE_DIR, '..', 'dialectes_col', 'ca', 'col_3_rimacons_ca.txt')
FITXER_NAUFRAGUES = os.path.join(BASE_DIR, '..', 'llistes', 'paraules_naufragues_ca.json')
FITXER_PUBLICADES_NORMAL = os.path.join(BASE_DIR, 'publicades_normal.json')
FITXER_PUBLICADES_NAUFRAGUES = os.path.join(BASE_DIR, 'publicades_naufragues.json')

PARAULES_PER_TUIT = 4


def carregar_json(nom_fitxer, per_defecte):
    """El fitxer que no hi és, o que és buit o malmès, compta com a per_defecte.

    Els publicades_*.json comencen buits i el JSON no en sap res, d'un fitxer
    de zero bytes: sense aquest coixí, el primer tuit de tots petaria.
    """
    if not os.path.exists(nom_fitxer):
        return per_defecte

    with open(nom_fitxer, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.decoder.JSONDecodeError:
            return per_defecte


def guardar_json(dades, nom_fitxer):
    with open(nom_fitxer, 'w', encoding='utf-8') as f:
        json.dump(dades, f, indent=4, ensure_ascii=False)


def carregar_rimes():
    """{rima: [totes les paraules que hi rimen]}, aplegat de les dues columnes.

    Abans això era un fitxer fet i comitejat, bot/resultat_ordenat_cons.json,
    de 17 MB, que generava bot/generador_rimes_cons.py des d'aquestes mateixes
    dues columnes. Se n'havia de pujar una còpia sencera a cada canvi del
    diccionari (30 versions a la història del repositori) i, com que la seva
    generació estava aturada, podia dir una cosa diferent del diccionari que
    serveix el lloc. Fer-ho aquí costa 1 s i 59 MB, i no pot quedar endarrerit.

    Sí que es guarda totes les paraules de cada rima, i per això els 59 MB: en
    necessita quatre a l'atzar i no en sap quines fins que tria la rima. Si un
    dia es publica el diccionari amb les formes amb pronom (quatre milions de
    files en comptes de 620.000), això s'haurà de repensar; vegeu l'avís de
    rimes_amb_una_sola_paraula() a llistes/generar_naufragues.py, que ja el va
    haver de tenir en compte.
    """
    rimes = {}

    try:
        with open(FITXER_RIMACONS, 'r', encoding='utf-8') as fitxer_rimes, \
             open(FITXER_PARAULES, 'r', encoding='utf-8') as fitxer_paraules:

            for linia_rima, linia_paraula in zip(fitxer_rimes, fitxer_paraules):
                rima = linia_rima.strip()
                if rima:
                    rimes.setdefault(rima, []).append(linia_paraula.strip())
    except FileNotFoundError:
        return {}

    return rimes


def data_curta(moment=None):
    """La data tal com surt al tuit: 5/9/26, sense zeros al davant."""
    moment = moment or datetime.now()
    return f"{moment.day}/{moment.month}/{moment.strftime('%y')}"


def rimes_de_naufragues(dades_naufragues):
    """Les rimes que ja té el bot de la tarda i que el de matí no ha de tocar."""
    return {item.get("rimacons") for item in dades_naufragues if item.get("rimacons")}


def rimes_disponibles(dades_rimes, publicades, dades_naufragues):
    fora = set(publicades) | rimes_de_naufragues(dades_naufragues)
    return [rima for rima in dades_rimes if rima not in fora]


def naufragues_disponibles(dades_naufragues, publicades):
    fora = set(publicades)
    return [item for item in dades_naufragues if item.get("rimacons") not in fora]


def tuit_normal(rima, paraules, data=None):
    """El tuit del matí: una rima i quatre paraules que hi rimen."""
    frequencia = len(paraules)

    # set() abans de triar: la llista de la rima ve del diccionari sencer i hi
    # surt una entrada per forma, o sigui que "abacallaneu" hi és tres vegades
    # (tres formes verbals que s'escriuen igual). Sense això, el random.sample
    # pot repetir paraula dins del mateix tuit. La freqüència sí que compta les
    # repeticions: és la que fa servir el lloc.
    llista_paraules = sorted(set(paraules))
    quantitat_a_triar = min(PARAULES_PER_TUIT, len(llista_paraules))
    paraules_escollides = sorted(random.sample(llista_paraules, quantitat_a_triar))

    tuit = f"Rima del dia ({data or data_curta()}): /{rima}/ ({frequencia} paraules hi rimen)\n\n"
    for paraula in paraules_escollides:
        tuit += f"- {paraula}\n"
    tuit += "\nConsulta totes les rimes a https://rimador.cat"

    return tuit


def tuit_naufraga(item, data=None):
    """El tuit de la tarda: una paraula que no rima amb res."""
    paraula_escollida = item.get("paraula")
    rima_escollida = item.get("rimacons")
    lema = item.get("infinitiu")
    codi = item.get("codi")
    es_diec = item.get("diec") == "Diec"
    es_VIQ = item.get("viq") == "Viq"
    es_VICC = item.get("vicc") == "Vicc"

    tuit = f"Paraula nàufraga del dia ({data or data_curta()}): {paraula_escollida} (/{rima_escollida}/)\n\n"
    if codi.startswith("NP"):
        tuit += "Aquest nom propi no rima amb cap altra paraula del diccionari.\n\n"
    else:
        tuit += "Aquesta paraula no rima amb cap paraula del diccionari, per això és una paraula nàufraga.\n\n"

    paraula_url = urllib.parse.quote(lema)

    if es_diec:
        tuit += f"📖 DIEC: https://dlc.iec.cat/Results?DecEntradaText={paraula_url}\n"

    else:
        if codi.startswith("NP"):
            if es_VIQ:
                tuit += f"📖 Viquipèdia: https://ca.wikipedia.org/wiki/{paraula_url}\n"
            else:
                tuit += f"📖 Viccionari: https://ca.wiktionary.org/wiki/{paraula_url}\n"
        else:
            if es_VICC:
                tuit += f"📖 Viccionari: https://ca.wiktionary.org/wiki/{paraula_url}\n"
            else:
                tuit += f"📖 Viquipèdia: https://ca.wikipedia.org/wiki/{paraula_url}\n"

    tuit += "\nConsulta totes les paraules nàufragues a https://rimador.cat/llistes/llista_naufragues.html"

    return tuit
