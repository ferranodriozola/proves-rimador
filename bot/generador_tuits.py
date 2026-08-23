"""El text dels tuits del bot: la part que no toca ni Twitter ni el disc.

Ho fan servir els dos scripts que publiquen sols (script_normal.py i
script_naufragues.py) i també el programador manual
(programador/servidor.py), que és el que faig servir quan els tuits es
programen a mà des de la web de X en comptes de pagar l'API.

Aquí no s'hi importa tweepy a posta: el programador ha de poder ensenyar-te
què diria el tuit sense cap credencial ni cap dependència de més. I el format
del tuit és en un sol lloc: si un dia canvia, canvia alhora per als dos
camins. Abans n'hi havia una còpia a cada script i es podien desdir l'una de
l'altra sense que ningú se n'adonés.
"""

import json
import os
import random
import urllib.parse
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FITXER_RIMES = os.path.join(BASE_DIR, 'resultat_ordenat_cons.json')
# El del CENTRAL: ara cada dialecte té la seva llista de nàufragues
# (llistes/generar_naufragues.py) i el bot publica en central, com tota
# la resta del que genera (vegeu bot/generador_rimes_cons.py).
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


def tuit_normal(rima, info_rima, data=None):
    """El tuit del matí: una rima i quatre paraules que hi rimen."""
    frequencia = info_rima.get("frequencia", 0)

    # set() abans de triar: la llista de la rima ve del diccionari sencer i hi
    # surt una entrada per forma, o sigui que "abacallaneu" hi és tres vegades
    # (tres formes verbals que s'escriuen igual). Sense això, el random.sample
    # pot repetir paraula dins del mateix tuit. La freqüència sí que compta les
    # repeticions: és la que fa servir el lloc.
    llista_paraules = sorted(set(info_rima.get("paraules", [])))
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
        tuit += "Aquest nom propi no rima amb cap paraula del diccionari, per això és una Paraula nàufraga.\n\n"
    else:
        tuit += "Aquesta paraula no rima amb cap paraula del diccionari, per això és una Paraula nàufraga.\n\n"

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
