import concurrent.futures
from gradio_client import Client
from tqdm import tqdm

nom_fitxer_entrada = "../../col_0.txt" 
dialectes = ["Central", "Valencia", "Occidental", "Balear", "Alguerès", "Rosellonès"]

# 1. Llegir l'arxiu i extreure línies úniques
with open(nom_fitxer_entrada, "r", encoding="utf-8") as f_entrada:
    linies_originals = [linia.strip() for linia in f_entrada if linia.strip()]
linies_uniques = list(set(linies_originals))

# 2. Funció aïllada per a cada dialecte
def processar_dialecte(dialecte):
    # Creem un client PROPI per a aquest fil per evitar interferències
    client_local = Client("https://projecte-aina-transcripcio-fonetica-catala.hf.space/", verbose=False)
    memoria_transcripcions = {}
    
    # Fem les peticions de forma autònoma per a aquest dialecte
    for text_unic in tqdm(linies_uniques, desc=f"{dialecte}", position=dialectes.index(dialecte)):
        resultat = client_local.predict(
            input_=text_unic,
            dialect=dialecte,
            api_name="/get-results"
        )
        memoria_transcripcions[text_unic] = resultat
        
    # Guardem l'arxiu final respectant l'ordre
    nom_fitxer_sortida = f"col_0_{dialecte.lower()}.txt"
    with open(nom_fitxer_sortida, "w", encoding="utf-8") as f_sortida:
        for linia in linies_originals:
            f_sortida.write(memoria_transcripcions[linia] + "\n")

print("Iniciant descàrrega simultània per a tots els dialectes...")

# 3. Executem els 6 dialectes SIMULTÀNIAMENT (Multithreading)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
    executor.map(processar_dialecte, dialectes)

print("\nProcés finalitzat a màxima velocitat!")