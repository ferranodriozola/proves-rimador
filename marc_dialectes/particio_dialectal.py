"""
Partir el diccionari gros de Softcatala segons la marca dialectal de cada
etiqueta.

    python3 marc_dialectes/particio_dialectal.py

    diccionari.txt (1.289.280 files)  ->  17 fitxers, un per marca

TOTA LA INFORMACIO DIALECTAL ES A L'ULTIM CARACTER DE L'ETIQUETA, i nomes a les
etiquetes verbals de vuit caracters (les que comencen per V). Els set primers
diuen la categoria gramatical; el vuite diu en quines arees es diu la forma:

    C  central + nord-occidental      canto, perdo, serveixo
    V  valencia                       cante, servisc, faca
    B  balear                         cant, cantam, tenc
    X  totes menys balear             canteu (imperatiu)
    Y  totes menys valencia           canti, cantis, adequo
    Z  totes menys central/nord-occ.  perd, dorm, servesc, llig
    0  totes                          cantant, cantava

Els digits 1-7 no son arees sino PARADIGMES de l'imperfet de subjuntiu
(cantes, cantessis, cantara, cantassis, cantesses, cantasses, cantas). Es
tradueixen a dialecte mes tard, quan s'ajuntin els fitxers.

Les uniques marques fora de les etiquetes verbals son als toponims valencians:
NPCSG0V es la forma catalana (Ademus) i NPCSG0O l'oficial castellanitzada
(Ademuz).

ELS ALTRES DOS FITXERS surten de comparar la font amb el diccionari que ja es
publica (diccionaris/separat/col_0,1,2):

    global        les files publicades que NO duen cap marca: el que val per
                  als quatre dialectes alhora, i que sera el diccionari base
    no_code_new   les files de la font sense marca que NO es publiquen: o son
                  paraules que Softcatala ha afegit despres de la versio que
                  vam manipular, o son les que vam decidir treure

Aixi, tota paraula que no surti a cap d'aquests fitxers no existeix: la particio
es completa i sense solapaments, i el programa ho comprova abans d'acabar.

NO S'ESCRIU RES FORA D'AQUESTA CARPETA. El diccionari publicat nomes es llegeix.
"""

import os
import sys

CARPETA = os.path.dirname(os.path.abspath(__file__))
ARREL = os.path.dirname(CARPETA)

FONT = os.path.join(CARPETA, "diccionari.txt")
PUBLICAT = [os.path.join(ARREL, "diccionaris", "separat", "col_%d.txt" % n)
            for n in (0, 1, 2)]

MARQUES_AREA = "CVBXYZ"
MARQUES_PARADIGMA = "1234567"
TOPONIMS = {"NPCSG0V": "top_V", "NPCSG0O": "top_O"}


def marca(codi):
    """En quin fitxer va aquesta etiqueta, o None si no duu cap marca.

    Les etiquetes verbals de vuit caracters porten la marca al vuite; un '0'
    hi vol dir "sense marca". La resta de categories (noms, adjectius,
    pronoms, determinants) no en porten mai, tret dels dos toponims.
    """
    if len(codi) == 8 and codi[0] == "V":
        ultim = codi[7]
        if ultim in MARQUES_AREA or ultim in MARQUES_PARADIGMA:
            return ultim
    return TOPONIMS.get(codi)


def llegir_columna(cami):
    """Una columna del diccionari publicat, una linia per fila.

    Es treuen els retorns de carro perque aquest clon es de Windows i el git li
    ha deixat els salts de linia en CRLF; sense aixo, els codis acabarien tots
    amb un \\r i no lligarien amb els de la font.
    """
    with open(cami, encoding="utf-8") as fitxer:
        text = fitxer.read().replace("\r", "")
    return text.rstrip("\n").split("\n")


def llegir_font():
    """Les files de la font: (forma, lema, codi). Tres camps separats per un
    espai i cap linia buida."""
    files = []
    with open(FONT, encoding="utf-8") as fitxer:
        for numero, linia in enumerate(fitxer, 1):
            camps = linia.split()
            if not camps:
                continue
            if len(camps) != 3:
                sys.exit("diccionari.txt, linia %d: hi ha %d camps i n'hi ha "
                         "d'haver 3 (forma, lema, codi)." % (numero, len(camps)))
            files.append(tuple(camps))
    return files


def escriure(nom, files):
    """Un fitxer de sortida, en el mateix format que l'entrada.

    Amb newline LF a posta: som a Windows i, sense dir-ho, el Python escriuria
    CRLF i els fitxers no serien comparables amb la font.
    """
    cami = os.path.join(CARPETA, nom + ".txt")
    with open(cami, "w", encoding="utf-8", newline="\n") as fitxer:
        for fila in files:
            fitxer.write(" ".join(fila) + "\n")


def main():
    print("Llegint el diccionari gros...")
    font = llegir_font()
    print("  {:,} files".format(len(font)))

    print("Llegint el diccionari publicat...")
    columnes = [llegir_columna(cami) for cami in PUBLICAT]
    if len(set(len(c) for c in columnes)) > 1:
        sys.exit("les columnes col_0, col_1 i col_2 no tenen el mateix nombre de files.")
    publicat = list(zip(*columnes))
    conjunt_publicat = set(publicat)
    print("  {:,} files ({:,} diferents)".format(len(publicat), len(conjunt_publicat)))

    # --- repartir la font ---
    # Cada fila va a un sol lloc: si duu marca, al fitxer de la seva marca; si
    # no en duu, depen de si es publica o no.
    grups = dict((m, []) for m in MARQUES_AREA + MARQUES_PARADIGMA)
    for nom in TOPONIMS.values():
        grups[nom] = []
    grups["no_code_new"] = []
    sense_marca_publicades = 0

    for fila in font:
        m = marca(fila[2])
        if m is not None:
            grups[m].append(fila)
        elif fila in conjunt_publicat:
            sense_marca_publicades += 1      # aquestes ja sortiran a global
        else:
            grups["no_code_new"].append(fila)

    # --- les correccions fetes a ma ---
    # Unes quantes files publicades duen marca i no son a la font: son
    # correccions nostres. El lema 'junyir' de Softcatala l'hem passat a
    # 'junyer' (junyeixo -> junyo, segona conjugacio), i hem aparellat el
    # toponim Moncada amb Montcada. Sense afegir-les aqui es quedarien fora de
    # tot: el global les rebutja per marcades i el fitxer de la seva marca
    # nomes mira la font.
    conjunt_font = set(font)
    afegides_a_ma = 0
    for fila in publicat:
        m = marca(fila[2])
        if m is not None and fila not in conjunt_font:
            grups[m].append(fila)
            afegides_a_ma += 1

    # --- el global surt del diccionari publicat, no de la font ---
    # Si sortis de la font hi faltarien les files que vam afegir a ma (Aqaba,
    # Bronx, Erevan...) i que no son al fitxer de Softcatala, pero que si que
    # son al diccionari i valen per als quatre dialectes.
    grups["global"] = [fila for fila in publicat if marca(fila[2]) is None]

    for nom in sorted(grups):
        escriure(nom, grups[nom])

    # ---------------------------------------------------------- comprovacions
    print("\nComprovant...")
    problemes = []

    # 1. La particio de la font es completa: cap fila perduda ni comptada dues vegades.
    repartides = sum(len(v) for k, v in grups.items() if k != "global")
    de_la_font = repartides - afegides_a_ma
    if de_la_font + sense_marca_publicades != len(font):
        problemes.append("la particio no quadra: {:,} de la font + {:,} a global "
                         "!= {:,} de la font".format(de_la_font, sense_marca_publicades,
                                                     len(font)))

    # 2. Cap fila del global duu marca (i per tant no pot ser a cap altre fitxer).
    ambmarca = [f for f in grups["global"] if marca(f[2]) is not None]
    if ambmarca:
        problemes.append("%d files del global duen marca: %s" % (len(ambmarca), ambmarca[:3]))

    # 3. Els fitxers no es trepitgen entre ells.
    vistes = set()
    for nom, files in grups.items():
        conjunt = set(files)
        xoc = vistes & conjunt
        if xoc:
            problemes.append("%s comparteix %d files amb un altre fitxer: %s"
                             % (nom, len(xoc), list(xoc)[:3]))
        vistes |= conjunt

    # 4. Tota fila publicada ha de sortir en algun fitxer: o al global, si no
    #    duu marca, o al fitxer de la seva marca. Si se n'escapes cap, una
    #    paraula que ara servim desapareixeria del diccionari sense dir res.
    a_la_sortida = set()
    for files in grups.values():
        a_la_sortida |= set(files)
    orfes = [f for f in publicat if f not in a_la_sortida]
    if orfes:
        problemes.append("%d files publicades no surten a cap fitxer: %s"
                         % (len(orfes), orfes[:3]))

    # 5. Els digits nomes poden sortir a l'imperfet de subjuntiu (VxSI....).
    mal = [f for m in MARQUES_PARADIGMA for f in grups[m] if f[2][2:4] != "SI"]
    if mal:
        problemes.append("%d files amb digit fora de l'imperfet de subjuntiu: %s"
                         % (len(mal), mal[:3]))

    # 6. Pedra de toc: 'cantar' i 'perdre' s'han de repartir tal com diu la
    #    guia (seccio 6). Es la comprovacio que enxampa gairebe qualsevol
    #    error al classificador, i mira que la fila hi sigui DE DEBO, no
    #    nomes que la funcio digui el que toca.
    esperat = [
        ("canto", "cantar", "VMIP1S0C", "C"), ("cante", "cantar", "VMIP1S0V", "V"),
        ("cant", "cantar", "VMIP1S0B", "B"), ("canteu", "cantar", "VMM02P0X", "X"),
        ("canti", "cantar", "VMSP1S0Y", "Y"), ("perd", "perdre", "VMIP1S0Z", "Z"),
        ("perdo", "perdre", "VMIP1S0C", "C"), ("perdi", "perdre", "VMSP1S0Y", "Y"),
        ("cantés", "cantar", "VMSI1S01", "1"),
        ("cantessis", "cantar", "VMSI2S02", "2"),
        ("cantara", "cantar", "VMSI1S03", "3"),
        ("cantassis", "cantar", "VMSI2S04", "4"),
        ("cantesses", "cantar", "VMSI2S05", "5"),
        ("cantasses", "cantar", "VMSI2S06", "6"),
        ("cantàs", "cantar", "VMSI1S07", "7"),
    ]
    for forma, lema, codi, nom in esperat:
        if (forma, lema, codi) not in set(grups[nom]):
            problemes.append("pedra de toc: %s (%s) no es a %s.txt" % (forma, codi, nom))

    # 7. I al reves: cap forma de 'cantar' pot quedar-se al global, perque la
    #    seva 1a persona (canto/cante/cant) es diferent a cada area.
    fugades = [f for f in grups["global"] if f[1] == "cantar" and f[2].startswith("VMIP1S")]
    if fugades:
        problemes.append("la 1a persona de 'cantar' no hauria de ser al global: %s" % fugades)

    if problemes:
        print("\nHi ha problemes:")
        for p in problemes:
            print("  - " + p)
        return 1
    print("  tot quadra: la particio es completa, sense solapaments i les marques "
          "van on toca.")

    # ----------------------------------------------------------------- resum
    # Quants lemes de cada fitxer sobreviuen al diccionari publicat: les files
    # amb un lema que no hi es son formes dialectals de verbs que vam treure
    # (abaconar -> abacono, abacone, abacon...) i que per tant no tindran mai
    # cap base on enganxar-se. No es filtren aqui, pero conve saber quantes son
    # abans de transcriure-les.
    lemes_publicats = set(columnes[1])
    print("\n{:<14}{:>12}{:>12}{:>16}".format("fitxer", "files", "formes", "lema publicat"))
    ordre = list(MARQUES_AREA) + list(MARQUES_PARADIGMA) + ["top_V", "top_O",
                                                            "no_code_new", "global"]
    for nom in ordre:
        files = grups[nom]
        amb_lema = sum(1 for f in files if f[1] in lemes_publicats)
        formes = len(set(f[0] for f in files))
        print("{:<14}{:>12,}{:>12,}{:>16,}".format(nom, len(files), formes, amb_lema))

    print("\n{:,} files de la font repartides; {:,} al diccionari base."
          .format(len(font), len(grups["global"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
