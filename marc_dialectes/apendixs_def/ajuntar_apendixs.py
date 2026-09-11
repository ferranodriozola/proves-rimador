"""
Ajuntar els fitxers de marques de marc_dialectes en els tres apendixs
dialectals.

    python3 marc_dialectes/apendixs_def/ajuntar_apendixs.py

    C, V, B, X, Y, Z, 1..7  ->  ca.txt, ba.txt, va.txt

Cada fitxer d'entrada va sencer a un document, a dos o als tres: es el que diu
el diccionari CRITERIS, i es l'unic que s'ha de tocar per canviar el repartiment.
Un fitxer pot anar a mes d'un document (X.txt, per exemple, es de tothom menys
del balear) i llavors les seves files es copien a tots dos.

ELS DIGITS 1-7 NO SON AREES sino els set paradigmes de l'imperfet de subjuntiu
(cantes, cantessis, cantara, cantassis, cantesses, cantasses, cantas). Es aqui,
en ajuntar, que es decideix quin paradigma va a quin dialecte; per aixo surten
a CRITERIS sense assignar fins que no es digui.

Nomes es llegeix de marc_dialectes i nomes s'escriu en aquesta carpeta.
"""

import os
import sys

CARPETA = os.path.dirname(os.path.abspath(__file__))
ORIGEN = os.path.dirname(CARPETA)

DOCUMENTS = ["ca", "ba", "va"]

# ---------------------------------------------------------------- els criteris
# A quins documents va cada fitxer. Les sis marques d'area ja venen posades
# perque el seu significat es fix (el diu la capcalera de particio_dialectal.py);
# els set paradigmes de l'imperfet de subjuntiu estan buits i s'han d'omplir.
# Deixar un fitxer amb [] vol dir "encara no decidit" i atura el programa; per
# descartar-lo a posta, posar-hi None.
CRITERIS = {
    "C": ["ca"],                    # central + nord-occidental: canto, perdo
    "V": ["va"],                    # valencia: cante, servisc, faca
    "B": ["ba"],                    # balear: cant, cantam, tenc
    "X": ["ca", "va"],              # totes menys balear: canteu
    "Y": ["ca", "ba"],              # totes menys valencia: canti, cantis
    "Z": ["ba", "va"],              # totes menys central: perd, dorm, servesc
    "1": ["ca", "va", "ba"],        # cantes
    "2": ["ca", "va", "ba"],        # cantessis
    "3": ["va"],                    # cantara
    "4": ["ba"],                    # cantassis
    "5": ["va"],                    # cantesses
    "6": ["va", "ba"],              # cantasses
    "7": ["va", "ba"],              # cantas
    "top_V": None,                  # toponims valencians, forma catalana
    "top_O": None,                  # toponims valencians, forma oficial
}

# Ordenar les files de cada document. Els fitxers d'entrada ja venen ordenats
# cadascun pel seu compte, i en ajuntar-ne uns quants les llistes s'entrellacen;
# amb aixo la sortida torna a quedar seguida.
ORDENAR = True


def llegir(nom):
    """Les files d'un fitxer d'entrada: (forma, lema, codi).

    Es treuen els retorns de carro perque aquest clon es de Windows, i es
    comprova que cada linia tingui els tres camps.
    """
    cami = os.path.join(ORIGEN, nom + ".txt")
    if not os.path.exists(cami):
        sys.exit("no hi ha %s." % cami)
    files = []
    with open(cami, encoding="utf-8") as fitxer:
        for numero, linia in enumerate(fitxer, 1):
            camps = linia.replace("\r", "").split()
            if not camps:
                continue
            if len(camps) != 3:
                sys.exit("%s.txt, linia %d: hi ha %d camps i n'hi ha d'haver 3 "
                         "(forma, lema, codi)." % (nom, numero, len(camps)))
            files.append(tuple(camps))
    return files


def escriure(document, files):
    """Un apendix, en el mateix format que l'entrada.

    Amb newline LF a posta: som a Windows i, sense dir-ho, el Python escriuria
    CRLF i els fitxers no serien comparables amb els d'origen.
    """
    cami = os.path.join(CARPETA, document + ".txt")
    with open(cami, "w", encoding="utf-8", newline="\n") as fitxer:
        for fila in files:
            fitxer.write(" ".join(fila) + "\n")
    return cami


def main():
    pendents = [nom for nom, docs in CRITERIS.items() if docs == []]
    if pendents:
        sys.exit("falta dir on van aquests fitxers: %s\n"
                 "Omple'ls a CRITERIS (o posa-hi None per descartar-los)."
                 % ", ".join(sorted(pendents) ))

    desconeguts = set()
    for nom, docs in CRITERIS.items():
        for doc in docs or []:
            if doc not in DOCUMENTS:
                desconeguts.add(doc)
    if desconeguts:
        sys.exit("CRITERIS parla de documents que no existeixen: %s"
                 % ", ".join(sorted(desconeguts)))

    documents = dict((doc, []) for doc in DOCUMENTS)
    origen = {}          # nom del fitxer -> quantes files tenia

    print("Llegint els fitxers de marques...")
    for nom in sorted(CRITERIS):
        docs = CRITERIS[nom]
        if docs is None:
            print("  {:<8} descartat".format(nom))
            continue
        files = llegir(nom)
        origen[nom] = len(files)
        for doc in docs:
            documents[doc].extend(files)
        print("  {:<8} {:>10,} files  ->  {}".format(nom, len(files), ", ".join(docs)))

    # --- escriure ---
    print("\nEscrivint els apendixs...")
    resum = []
    for doc in DOCUMENTS:
        files = documents[doc]
        repetides = len(files) - len(set(files))
        if repetides:
            # No hauria de passar: cada fila surt a un sol fitxer de marca. Si
            # passa, es que dos fitxers d'entrada es trepitgen.
            print("  ATENCIO: %s.txt te %d files repetides; es treuen." % (doc, repetides))
            vistes = set()
            netes = []
            for fila in files:
                if fila not in vistes:
                    vistes.add(fila)
                    netes.append(fila)
            files = netes
        if ORDENAR:
            files.sort()
        cami = escriure(doc, files)
        resum.append((doc, files))
        print("  {:<8} {:>10,} files  ->  {}".format(doc, len(files), os.path.basename(cami)))

    # ------------------------------------------------------------ comprovacions
    print("\nComprovant...")
    problemes = []

    # 1. Cap fila perduda: la suma dels apendixs ha de ser la suma dels fitxers
    #    d'entrada comptats tantes vegades com documents els reben.
    esperades = sum(origen[nom] * len(CRITERIS[nom]) for nom in origen)
    escrites = sum(len(files) for _, files in resum)
    if escrites != esperades:
        problemes.append("s'esperaven {:,} files i se n'han escrit {:,}"
                         .format(esperades, escrites))

    # 2. Cap document buit: si un apendix es queda sense files, el repartiment
    #    esta mal posat i val mes saber-ho ara que no pas al rimador.
    for doc, files in resum:
        if not files:
            problemes.append("%s.txt no te cap fila" % doc)

    if problemes:
        print("\nHi ha problemes:")
        for p in problemes:
            print("  - " + p)
        return 1
    print("  tot quadra: no s'ha perdut cap fila pel cami.")

    # ------------------------------------------------------------------ resum
    print("\n{:<10}{:>12}{:>12}{:>12}".format("apendix", "files", "formes", "lemes"))
    for doc, files in resum:
        formes = len(set(f[0] for f in files))
        lemes = len(set(f[1] for f in files))
        print("{:<10}{:>12,}{:>12,}{:>12,}".format(doc, len(files), formes, lemes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
