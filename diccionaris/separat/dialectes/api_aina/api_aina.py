from gradio_client import Client
from tqdm import tqdm

# 1. Connectar amb el servidor de l'API
client = Client("https://projecte-aina-transcripcio-fonetica-catala.hf.space/")

nom_fitxer_entrada = "../../col_0.txt" 
dialectes = ["Central", "Valencia", "Occidental", "Balear", "Alguerès", "Rosellonès"]

# 2. Llegir totes les línies mantenint l'ordre original
with open(nom_fitxer_entrada, "r", encoding="utf-8") as f_entrada:
    linies_originals = [linia.strip() for linia in f_entrada if linia.strip()]

# 3. Extraure només les línies úniques per estalviar temps i evitar errors
linies_uniques = list(set(linies_originals))

# 4. Bucle per processar cada dialecte
for dialecte in dialectes:
    # EL CANVI ÉS AQUÍ: El nom de l'arxiu ja no porta "api/" al davant
    nom_fitxer_sortida = f"transcripcions_{dialecte.lower()}.txt"
    
    print(f"\nProcessant el dialecte: {dialecte}")
    
    # Creem un diccionari per memoritzar les transcripcions d'aquest dialecte
    memoria_transcripcions = {}
    
    # Preguntem a l'API NOMÉS per les línies úniques
    for text_unic in tqdm(linies_uniques, desc=f"Consultant API ({dialecte})"):
        resultat = client.predict(
            input_=text_unic,
            dialect=dialecte,
            api_name="/get-results"
        )
        memoria_transcripcions[text_unic] = resultat
        
    # 5. Escriure l'arxiu final recuperant l'ordre exacte
    with open(nom_fitxer_sortida, "w", encoding="utf-8") as f_sortida:
        for linia in linies_originals:
            transcripcio = memoria_transcripcions[linia]
            f_sortida.write(transcripcio + "\n")

print("\nProcés finalitzat! Els fitxers s'han desat correctament al mateix directori.")