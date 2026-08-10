import os
import sys
import subprocess

nom_document = "diccionari.5.2.3.txt"
directori_destinacio = os.path.join("..", "diccionaris", "separat")
directori_extra = os.path.join("..", "diccionaris", "separat", "col_10 (canvis aquí)")
os.makedirs(directori_destinacio, exist_ok=True)
os.makedirs(directori_extra, exist_ok=True)

try:
    with open(nom_document, "r", encoding="utf-8") as file:
        linies = file.readlines()
except FileNotFoundError:
    print(f"El fitxer '{nom_document}' no s'ha trobat.")
    sys.exit()

columnes = [linia.strip().split("$") for linia in linies]
max_columnes = max(len(col) for col in columnes)
columnes = [col + [""] * (max_columnes - len(col)) for col in columnes]

# ------------------------------------------------------------------
# Refer la rima consonant (col_3) i assonant (col_4) a partir de la
# transcripció (col_9). NOMÉS aquestes dues columnes: totes les altres
# es deixen exactament com venen del diccionari.
#
# Cal fer-ho aquí perquè aquest script és l'únic que s'executa quan
# s'edita diccionari.5.2.3.txt a mà. Si no, una transcripció corregida
# a mà es propaga a les columnes amb la rima VELLA, i el web serveix
# una rima que no correspon a la transcripció (p. ex. 'Cook' amb
# transcripció /kˈɔk/ i rima 'uk'). Qui les recalculava fins ara era
# "creador_rima", que va a l'altre workflow i no s'encadena amb aquest.
#
# El càlcul ha de ser IDÈNTIC al de "creador_rima + dicc (a partir de
# col_10).py" perquè les dues vies no divergeixin mai.
# ------------------------------------------------------------------
COL_RIMA_CONSONANT = 3
COL_RIMA_ASSONANT = 4
COL_TRANSCRIPCIO = 9


def calcular_rimes(transcripcio):
    consonant = transcripcio.split("ˈ")[-1]
    assonant = "".join(lletra for lletra in consonant if lletra in "ɔəaeiou@Eɛˈ")
    return consonant, assonant


rimes_refetes = 0
rimes_saltades = 0
for fila in columnes:
    # Si la línia no té prou columnes, no hi toquem res: val més deixar-la
    # com està que no inventar-hi una rima buida.
    if len(fila) <= COL_TRANSCRIPCIO or not fila[COL_TRANSCRIPCIO]:
        rimes_saltades += 1
        continue
    consonant, assonant = calcular_rimes(fila[COL_TRANSCRIPCIO])
    if fila[COL_RIMA_CONSONANT] != consonant or fila[COL_RIMA_ASSONANT] != assonant:
        rimes_refetes += 1
    fila[COL_RIMA_CONSONANT] = consonant
    fila[COL_RIMA_ASSONANT] = assonant

print(f"Rimes recalculades a partir de la transcripció: {rimes_refetes} files corregides"
      f"{f', {rimes_saltades} saltades (sense transcripció)' if rimes_saltades else ''}")

columnes_transposades = list(zip(*columnes))

for i, columna in enumerate(columnes_transposades):
    nou_nom_fitxer = f"col_{i}.txt"
    nom_fitxer = os.path.join(directori_destinacio, nou_nom_fitxer)
    
    with open(nom_fitxer, "w", encoding="utf-8") as sortida:
        sortida.write("\n".join(columna))

    nombre_linees = len(columna)
    print(f"Generat: {nou_nom_fitxer} amb {nombre_linees} línies")

extra_linies = []
for line_parts in columnes:
    if len(line_parts) > 9:
        extra_column = f"{line_parts[0]} € {line_parts[1]} € {line_parts[2]} € {line_parts[9]}"
    else:
        extra_column = ""
    extra_linies.append(extra_column)

nom_fitxer_extra = os.path.join(directori_extra, "col_10provisional.txt")
with open(nom_fitxer_extra, "w", encoding="utf-8") as sortida_extra:
    sortida_extra.write("\n".join(extra_linies))

print(f"Generat: {nom_fitxer_extra} amb {len(extra_linies)} línies al directori: {directori_extra}")

# Tornem la rima corregida al diccionari, perquè no es quedi amb la vella i
# torni a propagar-la la pròxima vegada. Només s'hi reescriuen col_3 i col_4;
# la resta de camps són els mateixos que hi havia.
if rimes_refetes:
    with open(nom_document, "w", encoding="utf-8") as sortida_dicc:
        sortida_dicc.write("\n".join("$".join(fila) for fila in columnes) + "\n")
    print(f"Actualitzat: {nom_document} amb les {rimes_refetes} rimes corregides")

print(f"Funció acabada! {max_columnes} fitxers generats al directori: {directori_destinacio}")

subprocess.run(["python3", "post_proces.py"])

print("Post-procés finalitzat. Els fitxers han estat dividits i guardats correctament.")
