import json
import random
import os
from numpy import sort
import tweepy
from datetime import datetime

base_dir = os.path.dirname(os.path.abspath(__file__))

FITXER_RIMES = os.path.join(base_dir, 'resultat_ordenat_cons.json')
# El del CENTRAL: ara cada dialecte té la seva llista de nàufragues
# (llistes/generar_naufragues.py) i el bot publica en central, com tota
# la resta del que genera (vegeu bot/generador_rimes_cons.py).
FITXER_NAUFRAGUES = os.path.join(base_dir, '..', 'llistes', 'paraules_naufragues_ca.json')
FITXER_UTILITZATS = os.path.join(base_dir, 'publicades_normal.json')

def carregar_json(nom_fitxer):
    if not os.path.exists(nom_fitxer):
        return [] if nom_fitxer in (FITXER_UTILITZATS, FITXER_NAUFRAGUES) else {}

    with open(nom_fitxer, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.decoder.JSONDecodeError:
            return [] if nom_fitxer in (FITXER_UTILITZATS, FITXER_NAUFRAGUES) else {}

def guardar_json(dades, nom_fitxer):
    with open(nom_fitxer, 'w', encoding='utf-8') as f:
        json.dump(dades, f, indent=4, ensure_ascii=False)

def principal():
    print("Iniciant el bot")
    
    dades_rimes = carregar_json(FITXER_RIMES)
    utilitzats = carregar_json(FITXER_UTILITZATS)
    dades_naufragues = carregar_json(FITXER_NAUFRAGUES)

    if not dades_rimes:
        print("El fitxer de rimes està buit o no s'ha trobat.")
        return

    if not dades_naufragues:
        print("El fitxer de paraules nàufragues està buit o no s'ha trobat.")
        return

    rimes_naufragues = set()
    for item in dades_naufragues:
        rima = item.get("rimacons")
        if rima:
            rimes_naufragues.add(rima)

    rimes_disponibles = [rima for rima in dades_rimes.keys() if rima not in utilitzats and rima not in rimes_naufragues]

    if not rimes_disponibles:
        print("Ja s'han utilitzat totes les rimes del fitxer!")
        return

    rima_escollida = random.choice(rimes_disponibles)
    
    info_rima = dades_rimes[rima_escollida]
    frequencia = info_rima.get("frequencia", 0)
    llista_paraules = info_rima.get("paraules", [])

    quantitat_a_triar = min(4, len(llista_paraules))
    paraules_random = random.sample(llista_paraules, quantitat_a_triar)
    paraules_escollides = sort(paraules_random)

    avui = datetime.now()
    data_formatada = f"{avui.day}/{avui.month}/{avui.strftime('%y')}"

    tuit = f"Rima del dia ({data_formatada}): /{rima_escollida}/ ({frequencia} paraules hi rimen)\n\n"
    for paraula in paraules_escollides:
        tuit += f"- {paraula}\n"
    tuit += "\nConsulta totes les rimes a https://rimador.cat"

    print("-" * 50)
    print(tuit)
    print("-" * 50)

    api_key = os.environ.get("API_KEY")
    api_secret = os.environ.get("API_SECRET")
    access_token = os.environ.get("ACCESS_TOKEN")
    access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET")

    if api_key and api_secret and access_token and access_token_secret:
        try:
            print("Connectant amb l'API de Twitter")
            client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )
            client.create_tweet(text=tuit)
            print("Tuit publicat amb èxit!")
        except Exception as e:
            print(f"Error en publicar el tuit: {e}")
            return
    else:
        print("Mode simulació: No s'han trobat les credencials de Twitter (API keys).")

    utilitzats.append(rima_escollida)
    guardar_json(utilitzats, FITXER_UTILITZATS)
    print(f"Rima '{rima_escollida}' afegida a '{FITXER_UTILITZATS}'.")

if __name__ == '__main__':
    principal()