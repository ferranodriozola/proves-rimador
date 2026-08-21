"""
Posar d'acord els dos fitxers que s'editen, i escriure'n les transcripcions.

    python3 diccionaris/python/sincronitzar.py

    diccionari.5.2.3.txt   QUINES paraules hi ha
    col_10.txt             COM sona cadascuna, a tots els dialectes
                    ▼
    tots dos, corregits, i dialectes_col/<codi>/col_9

És el primer pas i l'únic que escriu als dos fitxers d'entrada. Corre tant si
el que s'ha tocat és el diccionari com si és la col_10 com si has posat una
carpeta de dialecte nova: no cal saber d'on ve el canvi, perquè es mira les
dades i no el push.

LA REGLA. Els camps es reparteixen així: síl·labes, Vicc, Viq i Diec només són
al diccionari; les transcripcions només a la col_10; i paraula, lema i codi són
als DOS, que és l'únic lloc on hi pot haver desacord. Per saber qui té raó fan
falta tres referències:

    base          separat/col_0, col_1 i col_2: la identitat de l'última
                  publicació. Les escriu el workflow i no les edita ningú
    diccionari    com és ara
    col_10        com és ara

Comparant cada costat amb la base se sap qui ha canviat. Si només n'ha canviat
un, guanya aquell i l'altre s'actualitza; si han canviat tots dos igual, no hi
ha res a fer; si han canviat tots dos diferent, és un conflicte de debò i val
més aturar-se i dir quines files són.

I no es fa amb "git show": als workflows, el commit que dispara l'execució JA
és HEAD, i la comparació sempre sortiria igual.

L'ORDRE de resolució és: primer les files esborrades, després les identitats i
al final les transcripcions.
"""

import collections
import difflib
import os
import sys

DIR_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if DIR_SCRIPTS not in sys.path:
    sys.path.insert(0, DIR_SCRIPTS)

import avisos
import camins
import col_10 as modul_col_10
import config

DICC = "diccionaris/diccionari.5.2.3.txt"
C10 = "diccionaris/col_10.txt"


def alinear(abans, ara):
    """Per a cada element d'"ara", quin element d'"abans" li correspon (o None
    si no n'hi ha cap).

    Es retallen el principi i el final que ja són iguals abans de comparar: els
    canvis són sempre un grapat de files, i sense això el difflib hauria de
    rumiar-se sis-centes mil línies per trobar-ne quatre.
    """
    inici = 0
    while inici < len(abans) and inici < len(ara) and abans[inici] == ara[inici]:
        inici += 1

    final = 0
    while (final < len(abans) - inici and final < len(ara) - inici
           and abans[len(abans) - 1 - final] == ara[len(ara) - 1 - final]):
        final += 1

    correspondencia = list(range(inici))
    for etiqueta, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, abans[inici:len(abans) - final], ara[inici:len(ara) - final],
            autojunk=False).get_opcodes():
        if etiqueta == "equal":
            correspondencia.extend(range(inici + i1, inici + i2))
        elif etiqueta == "insert":
            correspondencia.extend([None] * (j2 - j1))
        elif etiqueta == "replace":
            # Aquí hi ha files que ja no diuen el mateix, i el difflib no sap
            # si són les mateixes editades o unes altres. S'aparellen per
            # posició: una identitat corregida (canviar el codi d'una paraula)
            # ha de continuar sent la mateixa fila, o perdria la transcripció.
            #
            # Si has esborrat una paraula i n'has posat una altra al seu lloc,
            # això ho pren per un canvi de nom i la nova hereta la pronúncia de
            # la vella. No hi ha manera de distingir-ho, però tampoc no passa
            # desapercebut: canviar com s'escriu una paraula surt a l'informe
            # amb un "revisa'n la transcripció".
            quantes = min(i2 - i1, j2 - j1)
            correspondencia.extend(range(inici + i1, inici + i1 + quantes))
            correspondencia.extend([None] * (j2 - j1 - quantes))
    correspondencia.extend(range(len(abans) - final, len(abans)))
    return correspondencia


def comprovar_reordenacio(nom, base, ara, fitxer):
    """Reordenar és el moviment que més mal faria confós amb un altre: sense
    això sortiria "600.000 paraules noves" i no s'entendria res."""
    if len(base) == len(ara) and base != ara and sorted(base) == sorted(ara):
        avisos.plegar(
            f"{nom} té les mateixes files que l'última publicació però en un altre "
            "ordre. Reordenar de debò vol dir permutar el diccionari, la col_10 i el "
            "col_9 de cada dialecte alhora, i amb les identitats repetides (29: 'be', "
            "'cop', 'cos'...) la permutació és ambigua justament allà on més mal faria. "
            "No s'ha tocat res.", fitxer)


def llegir_la_base():
    for n in (0, 1, 2):
        if not os.path.exists(camins.cami_columna(n)):
            avisos.plegar(f"falta separat/col_{n}.txt, que és la referència amb què es "
                          "reconcilien el diccionari i la col_10. Passa el columnes.py.")
    columnes = [camins.llegir_columna(camins.cami_columna(n)) for n in (0, 1, 2)]
    if len({len(c) for c in columnes}) > 1:
        avisos.plegar("la col_0, la col_1 i la col_2 no tenen el mateix nombre de files.")
    return ["$".join(tres) for tres in zip(*columnes)]


def main():
    if config.CAL_V6:
        avisos.plegar(
            "config.py publica el v.6 i els dialectes encara no hi conviuen: les "
            "formes amb pronom haurien de portar la seva transcripció a cada dialecte.")

    files = camins.llegir_diccionari()
    identitats_dicc = [camins.identitat(fila) for fila in files]
    codis = camins.dialectes()
    if not codis:
        avisos.plegar("no hi ha cap dialecte a dialectes_col/.")
    avisos.nota(f"Diccionari: {camins.mil(len(files))} files. "
                f"Dialectes: {', '.join(codis)}")

    # --- la primera vegada: no hi ha col_10 i no hi ha res per reconciliar ---
    if not modul_col_10.existeix():
        avisos.nota("\nNo hi ha col_10.txt: se'n fa una de nova amb el que hi ha.")
        transcripcions = {}
        for codi in codis:
            cami = camins.cami_dialecte(codi, 9)
            if not os.path.exists(cami):
                avisos.plegar(f"falta {os.path.relpath(cami, camins.ARREL)}.")
            transcripcions[codi] = camins.llegir_columna(cami)
            if len(transcripcions[codi]) != len(files):
                avisos.plegar(f"el dialecte '{codi}' té "
                              f"{camins.mil(len(transcripcions[codi]))} files i el "
                              f"diccionari en té {camins.mil(len(files))}.")
        modul_col_10.escriure([fila[:3] for fila in files], transcripcions)
        avisos.nota("Feta. Ara toca el columnes.py.")
        return 0

    identitats_c10, transcripcions = modul_col_10.llegir()
    claus_c10 = ["$".join(tres) for tres in identitats_c10]
    base = llegir_la_base()

    comprovar_reordenacio("El diccionari", base, identitats_dicc, DICC)
    comprovar_reordenacio("La col_10", base, claus_c10, C10)

    # --- qui ve d'on ---
    de_dicc = alinear(base, identitats_dicc)          # fila del diccionari -> fila de la base
    de_c10 = alinear(base, claus_c10)                 # fila de la col_10   -> fila de la base
    inversa_c10 = {b: i for i, b in enumerate(de_c10) if b is not None}

    # Les files noves de la col_10, per identitat i en ordre: d'aquí surten les
    # transcripcions de les paraules que s'acaben de donar d'alta.
    noves_c10 = collections.defaultdict(collections.deque)
    for i, b in enumerate(de_c10):
        if b is None:
            noves_c10[claus_c10[i]].append(i)

    esborrades = len(base) - sum(1 for b in de_dicc if b is not None)
    problemes = []       # (fila, paraula, què hi passa)
    conflictes = []      # (fila, base, diccionari, col_10)
    corregides = []      # (fila, d'on ve el canvi, abans, després)
    parelles = []        # (fila del diccionari, fila de la col_10 o None)

    for i, fila in enumerate(files):
        b = de_dicc[i]

        if b is not None:
            c = inversa_c10.get(b)
            if c is None:
                # La fila era a la base i el diccionari encara la té: qui l'ha
                # treta és la col_10, i d'allà no se'n poden treure.
                problemes.append((i + 1, fila[0], "la col_10 ha esborrat aquesta fila; "
                                                  "si la paraula ha de marxar, treu-la "
                                                  "del diccionari"))
                parelles.append((i, None))
                continue
        else:
            pendents = noves_c10.get(identitats_dicc[i])
            if not pendents:
                problemes.append((i + 1, fila[0], "paraula nova al diccionari i no és a "
                                                  "la col_10: falta saber com sona"))
                parelles.append((i, None))
                continue
            c = pendents.popleft()

        parelles.append((i, c))

        # --- la identitat ---
        id_dicc = identitats_dicc[i]
        id_c10 = claus_c10[c]
        if b is None:
            final = id_dicc                        # totes dues noves i iguals
        else:
            id_base = base[b]
            canvia_dicc = id_dicc != id_base
            canvia_c10 = id_c10 != id_base
            if canvia_dicc and canvia_c10 and id_dicc != id_c10:
                conflictes.append((i + 1, id_base, id_dicc, id_c10))
                final = id_base
            elif canvia_c10:
                final = id_c10
                corregides.append((i + 1, "col_10", id_base, id_c10))
            else:
                final = id_dicc
                if canvia_dicc:
                    corregides.append((i + 1, "diccionari", id_base, id_dicc))

        nova = final.split("$")
        files[i] = nova + fila[camins.CAMPS_IDENTITAT:]
        identitats_c10[c] = nova

    # Files de la col_10 que no han trobat parella: paraules que hi són i que
    # al diccionari no hi ha.
    sobrants = [i for cua in noves_c10.values() for i in cua]
    for i in sorted(sobrants):
        problemes.append((i + 1, identitats_c10[i][0],
                          "aquesta paraula és a la col_10 i no al diccionari: les "
                          "síl·labes i els enllaços no es poden endevinar"))

    # --- res no s'escriu si hi ha res per resoldre ---
    if conflictes:
        avisos.error(f"{len(conflictes)} files que el diccionari i la col_10 han canviat "
                     "de manera diferent. No s'ha tocat res.")
        avisos.taula("Conflictes", ["fila", "abans", "diccionari diu", "col_10 diu"],
                     conflictes)
        for fila, _, _, _ in conflictes[:5]:
            avisos.error(f"fila {fila}: el diccionari i la col_10 no diuen el mateix", DICC, fila)
    if problemes:
        avisos.error(f"{len(problemes)} files sense parella entre el diccionari i la "
                     "col_10. No s'ha tocat res.")
        avisos.taula("Files sense parella", ["fila", "paraula", "què hi passa"], problemes)
        for fila, paraula, motiu in problemes[:5]:
            avisos.error(f"fila {fila}, '{paraula}': {motiu}", DICC, fila)
    if conflictes or problemes:
        for fila, paraula, motiu in problemes[:20]:
            avisos.nota(f"   fila {fila}: {paraula} — {motiu}")
        for fila, abans, d, c in conflictes[:20]:
            avisos.nota(f"   fila {fila}: abans {abans} | diccionari {d} | col_10 {c}")
        return 1

    # --- els dialectes ---
    sense_col_10 = [codi for codi in codis if codi not in transcripcions]
    sense_carpeta = [codi for codi in transcripcions if codi not in codis]
    for codi in sense_carpeta:
        avisos.avis(f"el dialecte '{codi}' era a la col_10 i ja no té carpeta a "
                    "dialectes_col/: se'n treu la columna.")
        del transcripcions[codi]

    for codi in sense_col_10:
        cami = camins.cami_dialecte(codi, 9)
        if not os.path.exists(cami):
            avisos.plegar(f"el dialecte '{codi}' no té ni columna a la col_10 ni "
                          f"{os.path.basename(cami)}.")
        seva = camins.llegir_columna(cami)
        if len(seva) != len(files):
            avisos.plegar(
                f"el dialecte nou '{codi}' té {camins.mil(len(seva))} files i el "
                f"diccionari en té {camins.mil(len(files))}. La transcripció d'un "
                "dialecte nou ha de tenir una línia per paraula del diccionari.")
        transcripcions[codi] = seva
        avisos.nota(f"  {codi}: dialecte nou, entra a la col_10")

    # --- escriure-ho tot ---
    identitats_finals = [identitats_c10[c] if c is not None else files[i][:3]
                         for i, c in parelles]
    ordenades = {}
    for codi, valors in transcripcions.items():
        if codi in sense_col_10:
            ordenades[codi] = valors
        else:
            ordenades[codi] = [valors[c] for _, c in parelles]

    camins.escriure_diccionari(files)
    modul_col_10.escriure(identitats_finals, ordenades)

    for codi in sorted(ordenades):
        cami = camins.cami_dialecte(codi, 9)
        anteriors = camins.llegir_columna(cami) if os.path.exists(cami) else []
        camins.escriure_columna(cami, ordenades[codi])
        canviades = (sum(1 for a, b in zip(anteriors, ordenades[codi]) if a != b)
                     if len(anteriors) == len(ordenades[codi]) else None)
        avisos.nota(f"  {codi}: {camins.mil(len(ordenades[codi]))} files"
                    + (f", {canviades} transcripcions diferents de les que hi havia"
                       if canviades else ""))

    if esborrades:
        avisos.nota(f"\n{esborrades} files esborrades del diccionari: fora de la col_10 "
                    "i de tots els dialectes")
    if corregides:
        canvis_de_paraula = [c for c in corregides if c[2].split("$")[0] != c[3].split("$")[0]]
        avisos.nota(f"{len(corregides)} identitats corregides")
        if canvis_de_paraula:
            avisos.avis(f"{len(canvis_de_paraula)} paraules han canviat com s'escriuen: "
                        "revisa'n la transcripció, que pot ser que ja no sigui la que toca")
        avisos.taula("Identitats corregides", ["fila", "ho ha dit", "abans", "ara"], corregides)

    avisos.nota("\nFet! Ara toca el columnes.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
