import os
import json
import re

from versions import actualitzar_versio

def obtenir_accent_fonetic(transcripcio):
    accents = [m.start() for m in re.finditer(r'ˈ', transcripcio)]
    
    if not accents:
        return 'aguda'
        
    pos_accent = accents[-1]
    
    vocals = r'[aɛeioɔuə]'
    vocals_finals = re.findall(vocals, transcripcio[pos_accent:])
    
    quanti_vocals = len(vocals_finals)
    
    if quanti_vocals == 1:
        return 'aguda'
    elif quanti_vocals == 2:
        return 'plana'
    else:
        return 'esdruixola'

def generar_llista():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    rutes = {
        'paraula': os.path.join(base_dir, '..', 'diccionaris', 'separat', 'col_0.txt'),
        'infinitiu': os.path.join(base_dir, '..', 'diccionaris', 'separat', 'col_1.txt'),
        'codi': os.path.join(base_dir, '..', 'diccionaris', 'separat', 'col_2.txt'),
        # La rima i la transcripció ja no són a separat/: depenen del dialecte
        # i viuen a dialectes_col/<codi>/. Aquesta llista és la del CENTRAL.
        'rimacons': os.path.join(base_dir, '..', 'dialectes_col', 'ca', 'col_3_rimacons_ca.txt'),
        'sil': os.path.join(base_dir, '..', 'diccionaris', 'separat', 'col_5.txt'),
        'vicc': os.path.join(base_dir, '..', 'diccionaris', 'separat', 'col_6.txt'),
        'viq': os.path.join(base_dir, '..', 'diccionaris', 'separat', 'col_7.txt'),
        'diec': os.path.join(base_dir, '..', 'diccionaris', 'separat', 'col_8.txt'),
        'transcripcio': os.path.join(base_dir, '..', 'dialectes_col', 'ca', 'col_9_transcripcio_ca.txt')
    }
    
    fitxer_sortida = os.path.join(base_dir, 'mots_de7_glosa.json')
    mots_filtrats = []

    def llegir_linies(ruta):
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return f.read().splitlines()
        except FileNotFoundError:
            return []

    dades = {clau: llegir_linies(ruta) for clau, ruta in rutes.items()}
    
    if not dades['sil'] or not dades['paraula'] or not dades['transcripcio']:
        print("Error: Faltes arxius essencials (col_0, col_5 o col_9).")
        return

    def valor_per_index(llista, index):
        return llista[index] if index < len(llista) else None

    for i, sil in enumerate(dades['sil']):
        sil_str = sil.strip()
        if not sil_str.isdigit():
            continue
            
        sil_num = int(sil_str)
        paraula_actual = valor_per_index(dades['paraula'], i)
        transcripcio_actual = valor_per_index(dades['transcripcio'], i)
        
        if not paraula_actual or not transcripcio_actual:
            continue
            
        accent = obtenir_accent_fonetic(transcripcio_actual)
        
        if (sil_num == 7 and accent == 'aguda') or \
           (sil_num == 8 and accent == 'plana') or \
           (sil_num == 9 and accent == 'esdruixola'):
           
            mots_filtrats.append({
                'paraula': paraula_actual,
                'infinitiu': valor_per_index(dades['infinitiu'], i),
                'codi': valor_per_index(dades['codi'], i),
                'rimacons': valor_per_index(dades['rimacons'], i),
                'sil': sil_str,
                'accent': accent,
                'fonetica': transcripcio_actual.strip(),
                'vicc': valor_per_index(dades['vicc'], i),
                'viq': valor_per_index(dades['viq'], i),
                'diec': valor_per_index(dades['diec'], i),
            })

    with open(fitxer_sortida, 'w', encoding='utf-8') as f:
        json.dump(mots_filtrats, f, ensure_ascii=False, indent=2)

    print(f"Generació completada: {len(mots_filtrats)} paraules guardades a {fitxer_sortida}")

    actualitzar_versio('mots_de7_glosa.json', fitxer_sortida)


if __name__ == '__main__':
    generar_llista()