import os

# Aquest script viu a diccionaris/pythons/ però escriu a diccionaris/. Les rutes
# es calculen des d'on és el fitxer i no des d'on s'executa: abans eren relatives
# a la carpeta de treball, i com que aquest script SOBREESCRIU el diccionari
# base, una carpeta de treball equivocada volia dir escriure'l en un lloc que no
# toca.
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DICCIONARI = os.path.join(BASE, "diccionari.5.2.3.txt")
COL_10 = os.path.join(BASE, "separat", "col_10 (canvis aquí)", "col_10provisional.txt")

# Els quatre camps que la columna 10 NO porta: síl·labes i els tres enllaços.
# Surten del diccionari que ja hi ha, fila per fila.
CAMPS_DEL_DICCIONARI = (5, 6, 7, 8)

# ------------------------------------------------------------------
# Aquest script NO escriu cap col_N.txt.
#
# Abans en deixava sis a separat/ i tot seguit les tornava a llegir (amb les
# quatre que no toca) per remuntar el diccionari. Aquelles columnes eren un pas
# intermedi que no servia per a res més: les que es baixa el navegador les fa el
# generar_columnes_publicades.py a partir del diccionari que digui config.py,
# que pot no ser aquest.
#
# I mentre separat/ contingués les columnes PUBLICADES, llegir-ne els camps 5 a
# 8 hauria estat un desastre silenciós: el diccionari publicat té quatre milions
# de files i la columna 10 en té sis-centes mil, o sigui que cada paraula hauria
# heretat les síl·labes i els enllaços d'una altra. Ara aquests quatre camps
# surten del diccionari base, que va fila per fila amb la columna 10.
# ------------------------------------------------------------------

with open(COL_10, "r", encoding="utf-8") as doc:
    linies = [linia.strip() for linia in doc if "€" in linia]

paraules = []
donve = []
codis = []
transcripcions = []

for linia in linies:
    parts = linia.split(" € ")
    if len(parts) >= 4:
        paraules.append(parts[0])
        donve.append(parts[1])
        codis.append(parts[2])
        transcripcions.append(parts[3])
    else:
        print("Línia amb format incorrecte:", linia)

# La rima es calcula IGUAL que al "separar_arxiu (per canvis a diccionari_txt).py",
# a posta: són les dues vies d'entrar canvis al diccionari i no poden divergir.
rimes_consonants = []
rimes_assonants = []
for transcripcio in transcripcions:
    consonant = transcripcio.split(" € ")[-1].split("ˈ")[-1]
    rimes_consonants.append(consonant)
    rimes_assonants.append("".join(l for l in consonant if l in "ɔəaeiou@Eɛˈ"))

print("Fet! (rima creada)")

print("Es comença a fer diccionari")

with open(DICCIONARI, "r", encoding="utf-8") as doc:
    velles = [linia.rstrip("\n").split("$") for linia in doc if linia.strip()]

# Xarxa de seguretat. Aquest script no regenera les síl·labes ni els enllaços:
# els pren del diccionari d'abans, fila per fila. Si a la columna 10 s'hi ha
# afegit o tret cap línia, tot el que ve de sota es desplaça i cada paraula
# hereta les síl·labes d'una altra, sense que res no se'n queixi.
#
# Abans qui ho enxampava era el generar_versions.py, perquè les columnes
# quedaven de mides diferents. Ara totes surten d'un sol fitxer i sempre van a
# l'una, o sigui que la comprovació ha de ser aquí.
if len(velles) != len(paraules):
    raise SystemExit(
        f"La columna 10 té {len(paraules)} files i el diccionari en té {len(velles)}.\n"
        "Aquest script no regenera les síl·labes ni els enllaços (camps 5 a 8):\n"
        "els pren del diccionari fila per fila, i així quedarien desplaçats.\n"
        "Si hi has afegit o tret paraules, cal passar pel diccionari general."
    )

with open(DICCIONARI, "w", encoding="utf-8") as f:
    for i in range(len(paraules)):
        f.write("$".join([
            paraules[i],              # 0 paraula
            donve[i],                 # 1 d'on ve
            codis[i],                 # 2 codi
            rimes_consonants[i],      # 3 rima consonant
            rimes_assonants[i],       # 4 rima assonant
            *(velles[i][c] for c in CAMPS_DEL_DICCIONARI),   # 5-8 síl·labes i enllaços
            transcripcions[i],        # 9 transcripció
        ]) + "\n")

print(f"Fet! (diccionari creat, {len(paraules)} files)")
