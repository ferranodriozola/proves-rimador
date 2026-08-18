import json

def extreure_verbs(arxiu_entrada, arxiu_sortida):
    verbs_unics = []
    verbs_vistos = set() # Utilitzem un set per fer la comprovació de repetits molt més ràpida
    
    # Obrim l'arxiu d'entrada en mode lectura
    with open(arxiu_entrada, 'r', encoding='utf-8') as f_in:
        for linia in f_in:
            # Netegem espais en blanc i salts de línia al final, i separem per '$'
            columnes = linia.strip().split('$')
            
            # Ens assegurem que la línia té almenys 3 columnes
            if len(columnes) >= 3:
                segona_columna = columnes[1]
                codi = columnes[2]
                
                # Comprovem si el codi comença per 'V' i no tenim la paraula repetida
                if codi.startswith('V') and segona_columna not in verbs_vistos:
                    verbs_unics.append(segona_columna)
                    verbs_vistos.add(segona_columna)
                    
    # Guardem la llista resultant a l'arxiu JSON
    with open(arxiu_sortida, 'w', encoding='utf-8') as f_out:
        # ensure_ascii=False permet que els accents es guardin correctament, 
        # indent=4 li dona l'estructura tabulada i llegible que demanes
        json.dump(verbs_unics, f_out, ensure_ascii=False, indent=4)
        
    print(f"Procés acabat! S'han guardat {len(verbs_unics)} paraules a '{arxiu_sortida}'.")

# Pots executar la funció canviant els noms dels arxius pels que necessitis
if __name__ == "__main__":
    # Exemple d'ús:
    fitxer_txt = "../diccionaris/diccionari.5.2.3.txt" # El teu arxiu original
    fitxer_json = "verbs.json" # L'arxiu on vols guardar el resultat
    
    extreure_verbs(fitxer_txt, fitxer_json)