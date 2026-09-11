"""
Posar d'acord els fitxers que s'editen, i escriure'n les transcripcions.

    python3 diccionaris/python/sincronitzar.py

    diccionari.5.2.3.txt   QUINES paraules hi ha
    col_10.txt             COM sona cadascuna, a tots els dialectes
                    ▼
    tots dos, corregits, i dialectes_col/<codi>/trans_dicc/col_9

    dialectes_col/<codi>/apendix/col_10_<codi>.txt   les paraules pròpies
                    ▼
    les col_0, 1, 2 i 9 d'aquell apendix, i les 5 a 8 tornades a alinear

És el primer pas i l'únic que escriu als fitxers d'entrada. Corre tant si el
que s'ha tocat és el diccionari com si és una col_10 com si has posat una
carpeta de dialecte nova: no cal saber d'on ve el canvi, perquè es mira les
dades i no el push.

SÓN DUES FEINES QUE NO S'ASSEMBLEN, i val la pena veure per què.

EL DICCIONARI I LA SEVA COL_10 es reparteixen els camps: síl·labes, Vicc, Viq i
Diec només són al diccionari; les transcripcions només a la col_10; i paraula,
lema i codi són als DOS, que és l'únic lloc on hi pot haver desacord. Per saber
qui té raó fan falta tres referències:

    base          separat/col_0, col_1 i col_2: la identitat de l'última
                  publicació. Les escriu el workflow i no les edita ningú
    diccionari    com és ara
    col_10        com és ara

Comparant cada costat amb la base se sap qui ha canviat. Si només n'ha canviat
un, guanya aquell i l'altre s'actualitza; si han canviat tots dos igual, no hi
ha res a fer; si han canviat tots dos diferent, és un conflicte de debò i val
més aturar-se i dir quines files són.

L'APENDIX D'UN DIALECTE no té tres referències sinó dues, i per tant no hi ha
cap conflicte que resoldre: MANA LA SEVA COL_10. Les col_0, 1, 2 i 9 són
sortides seves i no s'editen; les col_5 a 8 (síl·labes i enllaços) sí que
s'editen a mà, però no porten cap paraula a dins i van fila per fila, o sigui
que quan la col_10 dona una paraula d'alta o de baixa s'han de tornar a
alinear. Això últim és tota la feina, i la fa el mateix alinear() del
diccionari.

    donar de baixa   treure la línia de la col_10. Es fa, i es diu quina era
    donar d'alta     posar la línia a la col_10 I les síl·labes i els enllaços
                     a les col_5 a 8, a la mateixa fila. Si falten, s'atura i
                     diu quina fila és: no es poden endevinar

I no es fa amb "git show": als workflows, el commit que dispara l'execució JA
és HEAD, i la comparació sempre sortiria igual.

L'ORDRE de resolució és: primer les files esborrades, després les identitats i
al final les transcripcions. Els apendixs van al final de tot, quan el
diccionari ja està resolt: són llistes de paraules a part i no depenen d'ell.
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


PERMUTAR_EL_DICCIONARI = (
    "Reordenar de debò vol dir permutar el diccionari, la col_10 i el col_9 de cada "
    "dialecte alhora, i amb les identitats repetides (29: 'be', 'cop', 'cos'...) la "
    "permutació és ambigua justament allà on més mal faria.")

PERMUTAR_UN_APENDIX = (
    "Les col_5 a 8 van fila per fila amb la col_10 i no porten cap paraula a dins: "
    "reordenar-ne una i no les altres vol dir que cada paraula hereta les síl·labes i "
    "els enllaços d'una altra, i amb les identitats repetides la permutació és ambigua "
    "justament allà on més mal faria.")


def comprovar_reordenacio(nom, base, ara, fitxer, explicacio=PERMUTAR_EL_DICCIONARI):
    """Reordenar és el moviment que més mal faria confós amb un altre: sense
    això sortiria "600.000 paraules noves" i no s'entendria res."""
    if len(base) == len(ara) and base != ara and sorted(base) == sorted(ara):
        avisos.plegar(
            f"{nom} té les mateixes files que l'última publicació però en un altre "
            f"ordre. {explicacio} No s'ha tocat res.", fitxer)


def llegir_la_base():
    for n in (0, 1, 2):
        if not os.path.exists(camins.cami_columna(n)):
            avisos.plegar(f"falta separat/col_{n}.txt, que és la referència amb què es "
                          "reconcilien el diccionari i la col_10. Passa el columnes.py.")
    columnes = [camins.llegir_columna(camins.cami_columna(n)) for n in (0, 1, 2)]
    if len({len(c) for c in columnes}) > 1:
        avisos.plegar("la col_0, la col_1 i la col_2 no tenen el mateix nombre de files.")
    return ["$".join(tres) for tres in zip(*columnes)]


# ---------------------------------------------------------------- els apendixs
#
# UN APENDIX ES REPARTEIX ELS FITXERS IGUAL QUE EL DICCIONARI, i per això les
# regles s'assemblen tant:
#
#     el diccionari                    un apendix
#     ─────────────────────────────    ──────────────────────────────────────
#     diccionari.5.2.3.txt             col_5, 6, 7 i 8 (síl·labes, enllaços)
#       síl·labes i enllaços             s'editen a mà
#     col_10.txt                       col_10_<codi>.txt
#       identitat i transcripció         identitat i transcripció
#     separat/col_0, 1 i 2             col_0, 1 i 2 del mateix apendix
#       la identitat de l'última         la identitat de l'última passada
#       publicació
#
# La diferència: al diccionari, els dos costats poden discrepar sobre la
# identitat (paraula, lema i codi hi són als dos) i cal repartir culpes. En un
# apendix no: la identitat només és a la col_10, i les col_0, 1 i 2 en són
# sortides. Per tant no hi ha cap conflicte possible, i la referència només
# serveix per dir QUÈ HA CANVIAT.
#
# LES COL_5 A 8 VAN EN PAS AMB LA COL_10. Quan hi dones una paraula d'alta,
# posa-la als dos llocs i a la mateixa fila, com fas al diccionari. L'única
# excepció, perquè és la que no té cap ambigüitat, són les baixes: si l'únic
# que has fet és treure línies de la col_10, les col_5 a 8 es retallen soles.


def _llegir_grup(codi, numeros, que_son):
    """Un grup de columnes d'un apendix que han de quadrar entre elles."""
    valors = {}
    for numero in numeros:
        cami = camins.cami_apendix(codi, numero)
        if not os.path.exists(cami):
            avisos.plegar(
                f"falta {camins.relatiu(cami)}. L'apendix d'un dialecte ha de dur "
                + ", ".join(f"col_{n}" for n in numeros) + f" ({que_son}).")
        valors[numero] = camins.llegir_columna(cami)

    quantes = {numero: len(fila) for numero, fila in valors.items()}
    if len(set(quantes.values())) > 1:
        detall = ", ".join(f"col_{n}: {camins.mil(q)}" for n, q in sorted(quantes.items()))
        avisos.plegar(f"a l'apendix del '{codi}', {que_son} no tenen el mateix nombre "
                      f"de files ({detall}). Van fila per fila i no porten cap paraula "
                      f"a dins: desquadrades, cada paraula duu les dades d'una altra.",
                      camins.relatiu(camins.dir_apendix(codi)))
    return valors, quantes[numeros[0]]


def _estrenar_apendix(codi, identitats):
    """La primera vegada: no hi ha col_10 i se'n fa una del que hi ha."""
    cami_9 = camins.cami_apendix(codi, 9)
    if not os.path.exists(cami_9):
        avisos.plegar(f"l'apendix del '{codi}' no té ni col_10 ni "
                      f"{os.path.basename(cami_9)}: no se sap com sonen aquelles paraules.")
    transcripcio = camins.llegir_columna(cami_9)
    if len(transcripcio) != len(identitats):
        avisos.plegar(
            f"la col_9 de l'apendix del '{codi}' té {camins.mil(len(transcripcio))} files "
            f"i les col_0, 1 i 2 en tenen {camins.mil(len(identitats))}.")

    modul_col_10.escriure(identitats, {codi: transcripcio},
                          camins.cami_col_10_apendix(codi))
    avisos.nota(f"  {codi}: no hi havia col_10_{codi}.txt; se n'ha fet una amb les "
                f"{camins.mil(len(identitats))} paraules que hi ha")


def sincronitzar_apendix(codi):
    """Escriure les columnes d'un apendix des de la seva col_10.

    Torna True si ha petat (i llavors no s'ha tocat res d'aquest apendix)."""
    identificadores, files_antigues = _llegir_grup(
        codi, camins.APENDIX_DE_LA_COL_10, "les col_0, 1 i 2")
    identitats_antigues = [list(tres) for tres in zip(*(
        identificadores[n] for n in camins.APENDIX_DE_LA_COL_10))]

    cami_c10 = camins.cami_col_10_apendix(codi)
    relatiu_c10 = camins.relatiu(cami_c10)

    if not modul_col_10.existeix(cami_c10):
        _estrenar_apendix(codi, identitats_antigues)
        return False

    dades, files_dades = _llegir_grup(
        codi, camins.APENDIX_A_MA, "les síl·labes i els enllaços (col_5 a 8)")

    identitats, transcripcions = modul_col_10.llegir(cami_c10)
    dialectes_dins = list(transcripcions)
    if dialectes_dins != [codi]:
        avisos.plegar(
            f"la col_10 de l'apendix del '{codi}' porta "
            + (f"els dialectes {', '.join(dialectes_dins)}" if dialectes_dins
               else "cap dialecte")
            + f", i només n'hi pot dur un: el seu. Aquelles paraules només es diuen "
              f"en '{codi}' i als altres dialectes no existeixen.", relatiu_c10)

    antigues = ["$".join(tres) for tres in identitats_antigues]
    noves = ["$".join(tres) for tres in identitats]

    comprovar_reordenacio(f"La col_10 de l'apendix del '{codi}'", antigues, noves,
                          relatiu_c10, PERMUTAR_UN_APENDIX)

    # Per a cada fila de la col_10, quina fila tenia a l'última passada. Serveix
    # per dir què ha canviat i, quan només s'han donat paraules de baixa, per
    # retallar les col_5 a 8 sense haver-les de tocar a mà.
    correspondencia = alinear(antigues, noves)
    noves_de_trinca = [i for i, anterior in enumerate(correspondencia) if anterior is None]
    tenen_parella = {anterior for anterior in correspondencia if anterior is not None}
    esborrades = [clau for b, clau in enumerate(antigues) if b not in tenen_parella]

    if files_dades == len(noves):
        # Van en pas amb la col_10, que és com han d'anar: es prenen tal com són.
        arrossegades = dades
    elif files_dades == files_antigues and not noves_de_trinca:
        # Només s'hi han donat paraules de baixa. És l'únic cas on es pot
        # endevinar sense ambigüitat quina fila era quina, i per això és l'únic
        # que es fa sol.
        arrossegades = {numero: [dades[numero][anterior] for anterior in correspondencia]
                        for numero in camins.APENDIX_A_MA}
    else:
        noms = ", ".join(f"col_{n}_{codi}.txt" for n in camins.APENDIX_A_MA)
        avisos.error(
            f"apendix del '{codi}': la col_10 té {camins.mil(len(noves))} línies i les "
            f"síl·labes i els enllaços en tenen {camins.mil(files_dades)}. Han d'anar en "
            f"pas: una paraula nova va a la col_10 I a {noms}, a la mateixa fila. "
            f"No s'ha tocat res d'aquest apendix.", relatiu_c10)
        if noves_de_trinca:
            avisos.taula(f"Apendix del '{codi}': paraules noves a la col_10",
                         ["fila", "paraula", "lema", "codi"],
                         [(i + 1, *identitats[i]) for i in noves_de_trinca])
            for i in noves_de_trinca[:5]:
                avisos.error(f"fila {i + 1}, '{identitats[i][0]}': paraula nova; posa-hi "
                             f"les síl·labes i els enllaços a {noms}", relatiu_c10, i + 1)
            for i in noves_de_trinca[:20]:
                avisos.nota(f"   fila {i + 1}: {identitats[i][0]} — nova a la col_10")
        return True

    # --- escriure-ho tot ---
    canvis = 0
    for camp, numero in enumerate(camins.APENDIX_DE_LA_COL_10):
        canvis += camins.escriure_columna(camins.cami_apendix(codi, numero),
                                          [fila[camp] for fila in identitats])
    for numero in camins.APENDIX_A_MA:
        canvis += camins.escriure_columna(camins.cami_apendix(codi, numero),
                                          arrossegades[numero])
    canvis += camins.escriure_columna(camins.cami_apendix(codi, 9), transcripcions[codi])

    avisos.nota(f"  {codi}: {camins.mil(len(identitats))} paraules pròpies"
                + (f", {len(noves_de_trinca)} d'alta" if noves_de_trinca else "")
                + (f", {len(esborrades)} de baixa" if esborrades else "")
                + ("" if canvis else " (res no ha canviat)"))
    if esborrades:
        avisos.taula(f"Apendix del '{codi}': paraules donades de baixa",
                     ["paraula", "lema", "codi"],
                     [tuple(clau.split("$")) for clau in esborrades])
    return False


def sincronitzar_apendixs():
    """Tots els apendixs que hi hagi. Torna quants han petat."""
    codis = camins.dialectes_amb_apendix()
    if not codis:
        return 0

    avisos.nota(f"\nEls apendixs ({', '.join(codis)}): les paraules que només es diuen "
                f"en un dialecte")
    return sum(1 for codi in codis if sincronitzar_apendix(codi))


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

    if sincronitzar_apendixs():
        return 1

    avisos.nota("\nFet! Ara toca el columnes.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
