import os

# Aquest script viu a diccionaris/pythons/ però escriu a diccionaris/separat/ i
# a diccionaris/. Les rutes es calculen des d'on és el fitxer i no des d'on
# s'executa: abans eren relatives a la carpeta de treball, i com que aquest
# script SOBREESCRIU les deu columnes, una carpeta de treball equivocada volia
# dir escriure el diccionari en un lloc que no toca.
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sep(nom):
    return os.path.join(BASE, "separat", nom)


with open(sep("col_10 (canvis aquí)/col_10provisional.txt"), "r", encoding="utf-8") as doc2:
    linies = [linia.strip() for linia in doc2 if "€" in linia]

paraula = []
donve = []
codi = []
transcripcions = []

for linia in linies:
    parts = linia.split(" € ")
    if len(parts) >= 4:
        paraula.append(parts[0])
        donve.append(parts[1])
        codi.append(parts[2])
        transcripcions.append(parts[3])
    else:
        print("Línia amb format incorrecte:", linia)

with open(sep("col_0.txt"), "w", encoding="utf-8") as doc0:
    for i in paraula:
        doc0.write(i + "\n")

with open(sep("col_1.txt"), "w", encoding="utf-8") as doc1:
    for i in donve:
        doc1.write(i + "\n")
     
with open(sep("col_2.txt"), "w", encoding="utf-8") as doc2:
    for i in codi:
        doc2.write(i + "\n")

with open(sep("col_9.txt"), "w", encoding="utf-8") as doc9:
    for i in transcripcions:
        doc9.write(i + "\n")
        
with open(sep("col_3.txt"), "w", encoding="utf-8") as doc3:
    finals = []
    for linia in transcripcions:
        paraula = linia.split(" € ")[-1]
        final = paraula.split("ˈ")[-1]
        finals.append(final)
        doc3.write(final + '\n')

with open(sep("col_4.txt"), "w", encoding="utf-8") as doc4:
    vocals = []
    for linia in finals:
        vocal = ''.join([lletra for lletra in linia if lletra in "ɔəaeiou@Eɛˈ"])
        vocals.append(vocal)
        doc4.write(vocal + '\n')

print("Fet! (rima creada)")

print("Es comença a fer diccionari")
files = [sep('col_0.txt'),  #paraula
         sep('col_1.txt'),  #d'on ve
         sep('col_2.txt'),  #codi
         sep('col_3.txt'),  #rima consonant 
         sep('col_4.txt'),  #rima assonant 
         sep('col_5.txt'),  #síl·labes
         sep('col_6.txt'),  #Vicc
         sep('col_7.txt'),  #Wiki
         sep('col_8.txt'),  #Diec
         sep('col_9.txt'),  #transcripció  
]

lines_per_file = []
for file in files:
    with open(file, 'r') as f:
        lines = f.readlines()
        lines_per_file.append(lines)


output_file = os.path.join(BASE, 'diccionari.5.2.3.txt')

with open(output_file, 'w', encoding="utf-8") as f:
    for i in range(len(lines_per_file[0])):
        line_parts = [lines[i].strip() for lines in lines_per_file]
        
        line_to_write = '$'.join(line_parts)
        f.write(line_to_write + '\n')

print("Fet! (diccionari creat)")