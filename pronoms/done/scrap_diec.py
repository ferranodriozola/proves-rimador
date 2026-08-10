import json
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from tqdm import tqdm

FITXER_ENTRADA = 'verbs.json'
FITXER_SORTIDA = 'verbs_anotats.json'
URL_CERCA = 'https://dlc.iec.cat/Results?EntradaText=' 
URL_API_DEFINICIO = 'https://dlc.iec.cat/Results/Accepcio'

patro_categories = re.compile(r'\bv\..*?(?=\[)')

def anotar_verbs():
    with open(FITXER_ENTRADA, 'r', encoding='utf-8') as f:
            llista_verbs = json.load(f)
    
    resultats = {}
    capcaleres = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
    }

    for verb in tqdm(llista_verbs, desc="Processant verbs", unit="verb"):
        paraula = verb.strip()
        url = f"{URL_CERCA}{paraula}"
        
        try:
            resposta_cerca = requests.get(url, headers=capcaleres, timeout=10)
            resposta_cerca.raise_for_status() 
            
            soup_cerca = BeautifulSoup(resposta_cerca.text, 'html.parser')
            
            element_resultat = soup_cerca.find('a', class_='resultAnchor')
            
            if not element_resultat or not element_resultat.has_attr('id'):
                resultats[verb] = {"categories": [], "estat": "No trobat al diccionari"}
                continue
                
            id_verb = element_resultat['id']
            
            dades_post = {'id': id_verb}
            resposta_api = requests.post(URL_API_DEFINICIO, headers=capcaleres, data=dades_post, timeout=10)
            resposta_api.raise_for_status()
            
            dades_json = resposta_api.json()
            html_definicio = dades_json.get('content', '')
            
            soup_def = BeautifulSoup(html_definicio, 'html.parser')
            text_pagina = soup_def.get_text(separator=' ')
            
            troballes = [m.group(0).strip().replace('\n', ' ') for m in patro_categories.finditer(text_pagina)]
            troballes = [re.sub(r'\s+', ' ', t) for t in troballes] 
            
            categories_trobades = sorted(list(set(troballes)))
            
            resultats[verb] = {
                "categories": categories_trobades,
                "estat": "OK" if categories_trobades else "Sense categories especificades"
            }
                        
            temps_espera = random.uniform(0.5, 3)
            time.sleep(temps_espera)  

        except Exception as e:
            resultats[verb] = {
                "categories": [],
                "estat": f"Error: {str(e)}"
            }

    with open(FITXER_SORTIDA, 'w', encoding='utf-8') as f:
        json.dump(resultats, f, ensure_ascii=False, indent=4)
        
    print(f"\nProcés acabat.")

if __name__ == "__main__":
    anotar_verbs()