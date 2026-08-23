import os
import random

import tweepy

# El text del tuit, els camins dels fitxers i el filtre del que encara no s'ha
# dit són a generador_tuits.py, compartits amb el programador manual
# (programador/servidor.py). Aquí només hi queda el que és propi de publicar
# tot sol: triar a l'atzar, parlar amb Twitter i apuntar-ho.
import generador_tuits as generador


def principal():
    print("Iniciant el bot")

    dades_rimes = generador.carregar_json(generador.FITXER_RIMES, {})
    utilitzats = generador.carregar_json(generador.FITXER_PUBLICADES_NORMAL, [])
    dades_naufragues = generador.carregar_json(generador.FITXER_NAUFRAGUES, [])

    if not dades_rimes:
        print("El fitxer de rimes està buit o no s'ha trobat.")
        return

    if not dades_naufragues:
        print("El fitxer de paraules nàufragues està buit o no s'ha trobat.")
        return

    rimes_disponibles = generador.rimes_disponibles(dades_rimes, utilitzats, dades_naufragues)

    if not rimes_disponibles:
        print("Ja s'han utilitzat totes les rimes del fitxer!")
        return

    rima_escollida = random.choice(rimes_disponibles)
    tuit = generador.tuit_normal(rima_escollida, dades_rimes[rima_escollida])

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
    generador.guardar_json(utilitzats, generador.FITXER_PUBLICADES_NORMAL)
    print(f"Rima '{rima_escollida}' afegida a '{generador.FITXER_PUBLICADES_NORMAL}'.")


if __name__ == '__main__':
    principal()
