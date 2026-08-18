import glob
import os

# Des d'aquest fitxer (diccionaris/python/) fins a diccionaris/separat/. Abans
# la ruta era relativa a la carpeta des d'on s'executés l'script, i en moure els
# pythons a la seva pròpia carpeta això va deixar de trobar res.
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ruta_dicc_separats = os.path.join(BASE, "separat", "col_10 (canvis aquí)")
arxiu_temporal = os.path.join(ruta_dicc_separats, "col_10provisional.txt")

print("Iniciant el pre-procés: unint arxius col_10_*.txt...")

patro = os.path.join(ruta_dicc_separats, "col_10_*.txt")

def extreure_numero(ruta):
    nom_arxiu = os.path.basename(ruta)
    parts = nom_arxiu.split('_')
    return int(parts[2])

fitxers_petits = sorted(glob.glob(patro), key=extreure_numero)

dades_completes = []
for fitxer in fitxers_petits:
    with open(fitxer, 'r', encoding='utf-8') as f:
        dades_completes.extend(f.read().splitlines())

with open(arxiu_temporal, 'w', encoding='utf-8') as f:
    f.write("\n".join(dades_completes) + "\n")

print(f"S'han unit {len(fitxers_petits)} fitxers petits.")
print(f"S'ha creat l'arxiu temporal {arxiu_temporal} amb {len(dades_completes)} paraules.")