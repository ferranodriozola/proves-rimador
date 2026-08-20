"""
Del diccionari base a la "col_10 (canvis aquí)", que és el que s'edita a mà.

S'executa quan s'edita diccionari.5.2.3.txt a mà: refà la columna 10 perquè el
que hi ha per editar sigui el que hi ha de debò al diccionari.

    diccionari.5.2.3.txt                          paraula € lema € codi
    dialectes_col/ca/col_9_transcripcio_ca.txt                       € transcripció
                                        ▼
                    col_10 (canvis aquí)/col_10provisional.txt

La transcripció ja no és al diccionari (són set camps, no deu: vegeu
"creador_rima + dicc"), o sigui que el quart camp de la columna 10 es va a
buscar al dialecte central.

AQUEST SCRIPT JA NO CALCULA CAP RIMA. Abans en refeia la consonant i l'assonant
a partir de la transcripció, perquè era l'únic pas que corria quan s'editava el
diccionari a mà, i el mateix càlcul era escrit igual al "creador_rima" amb un
comentari a cada banda demanant que no divergissin. Ara la rima no és al
diccionari: la fa generar_dialectes.py, un sol cop i per a tots els dialectes.

Tampoc no escriu cap col_N.txt: les del web les fa el
generar_columnes_publicades.py a partir del diccionari que digui config.py, que
pot no ser aquest. L'única cosa que ha de sortir d'aquí és la columna 10, que és
la que s'edita a mà i que NOMÉS pot sortir del diccionari base.
"""

import os
import sys
import subprocess

# Aquest script viu a diccionaris/python/ i escriu a diccionaris/separat/.
# Les rutes surten d'on és el fitxer i no d'on s'executa: abans eren relatives a
# la carpeta de treball, i com que aquí baix hi ha un os.makedirs, una carpeta
# equivocada no donava cap error, sinó que es fabricava un arbre de carpetes nou
# i hi deixava el diccionari, ben lluny d'on el va a buscar tothom.
DIR_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if DIR_SCRIPTS not in sys.path:
    sys.path.insert(0, DIR_SCRIPTS)

from generar_dialectes import CENTRAL, cami as cami_dialecte, llegir_columna

BASE = os.path.dirname(DIR_SCRIPTS)

nom_document = os.path.join(BASE, "diccionari.5.2.3.txt")
directori_extra = os.path.join(BASE, "separat", "col_10 (canvis aquí)")
os.makedirs(directori_extra, exist_ok=True)

TRANSCRIPCIO = cami_dialecte(CENTRAL, 9)

CAMPS = 7  # paraula, lema, codi, síl·labes, Vicc, Viq, Diec

try:
    with open(nom_document, "r", encoding="utf-8") as file:
        linies = file.readlines()
except FileNotFoundError:
    print(f"El fitxer '{nom_document}' no s'ha trobat.")
    sys.exit()

columnes = []
for numero, linia in enumerate(linies, 1):
    linia = linia.rstrip("\n")
    if not linia:
        continue
    camps = linia.split("$")
    if len(camps) != CAMPS:
        raise SystemExit(
            f"{nom_document}, línia {numero}: hi ha {len(camps)} camps i n'hi "
            f"ha d'haver {CAMPS}.\n"
            "El diccionari ja no porta ni la rima ni la transcripció: són a "
            "dialectes_col/.\n"
            f"  {linia[:120]!r}"
        )
    columnes.append(camps)

try:
    transcripcions = llegir_columna(TRANSCRIPCIO)
except FileNotFoundError:
    raise SystemExit(
        f"No hi ha {TRANSCRIPCIO}.\n"
        "És la transcripció del central, i és el quart camp de la columna 10."
    )

# Van fila per fila amb el diccionari i no porten cap paraula a dins: si no
# tenen la mateixa mida, cada paraula heretaria la pronúncia d'una altra i la
# columna 10 sortiria plena de disbarats sense que res se'n queixés.
if len(transcripcions) != len(columnes):
    raise SystemExit(
        f"El diccionari té {len(columnes)} files i {os.path.basename(TRANSCRIPCIO)} "
        f"en té {len(transcripcions)}.\n"
        "Van fila per fila. Si al diccionari hi ha entrades noves, primer cal "
        "transcriure-les."
    )

extra_linies = [
    f"{fila[0]} € {fila[1]} € {fila[2]} € {transcripcions[i]}"
    for i, fila in enumerate(columnes)
]

nom_fitxer_extra = os.path.join(directori_extra, "col_10provisional.txt")
with open(nom_fitxer_extra, "w", encoding="utf-8") as sortida_extra:
    sortida_extra.write("\n".join(extra_linies))

print(f"Generat: {nom_fitxer_extra} amb {len(extra_linies)} línies al directori: {directori_extra}")
print(f"Funció acabada! Columna 10 generada a partir de {len(columnes)} files.")

# El post_procés és aquí al costat, no pas a la carpeta de treball. I es crida
# amb el mateix python que ens executa a nosaltres, que és l'únic que sabem
# segur que existeix (als workflows, "python3" no té per què ser el que ha
# preparat el setup-python).
subprocess.run([sys.executable, os.path.join(DIR_SCRIPTS, "post_proces.py")])

print("Post-procés finalitzat. Els fitxers han estat dividits i guardats correctament.")
