"""
Què passaria amb les rimes si el diccionari incorporés les formes amb pronom.

Tres passos, en aquest ordre:

  1. ajunta tots els .txt de txt_fets/ en un de sol      -> txt_fets/tot.txt
  2. n'agafa la columna de rima consonant i l'enganxa
     darrere la del diccionari real                      -> txt_fets/col_3_prova_v.6.txt
  3. repassa línia per línia els dos documents de rimes i els compara

    python3 ajuntar_i_comptar_rimes.py

Els passos 1 i 2 estan COMENTATS a main(): els dos fitxers ja estan fets, i
tornar-los a escriure són 300 MB i mig minut per res. Es descomenten quan
canviï alguna cosa a txt_fets/ o a la columna del diccionari.

Els fitxers que genera van a txt_fets/, no a diccionaris/: aquesta carpeta és
de treball i no toca mai el diccionari de producció (vegeu README.md).

El pas 3 compta dues coses que no són la mateixa:

  · línies DIFERENTS -> quants valors distints hi ha. Una rima repetida 500
    vegades hi compta una sola vegada: és el nombre de CLASSES DE RIMA.
  · línies ÚNIQUES   -> quantes d'aquestes classes surten exactament un cop,
    o sigui quantes paraules no rimen amb cap altra del document.
"""

import os
from collections import Counter

# .parent perquè aquest fitxer viu a pronoms/python/ i txt_fets/ és a pronoms/.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRONOMS_DIR = os.path.dirname(BASE_DIR)
DIR_TXT = os.path.join(PRONOMS_DIR, "txt_fets")

FITXER_TOT = os.path.join(DIR_TXT, "tot.txt")
FITXER_PROVA = os.path.join(DIR_TXT, "col_3_prova_v.6.txt")

# La mateixa columna, però del diccionari de producció. Les dues són
# comparables perquè enclisi.calcular_rimes() fa servir el mateix càlcul que
# el creador de rimes del diccionari, a posta.
COL_3_BASE = os.path.join(PRONOMS_DIR, "..", "diccionaris", "separat", "col_3.txt")

# La columna de les paraules, alineada línia per línia amb col_3: serveix per
# dir QUINA paraula hi ha darrere d'una rima del diccionari.
COL_0_BASE = os.path.join(PRONOMS_DIR, "..", "diccionaris", "separat", "col_0.txt")

CAMPS = 10
COL_RIMA_CONSONANT = 3


def mil(n):
    """619783 -> '619.783', com els números de la documentació."""
    return f"{n:,}".replace(",", ".")


# ------------------------------------------------- 1. ajuntar els .txt fets

def fitxers_font():
    """
    Els .txt de les SUBCARPETES de txt_fets/ (1_pronom/ i 2_pronoms/).

    Només mira dins de subcarpetes a posta: així el que aquest script deixa a
    txt_fets/ mateix (tot.txt, col_3_prova_v.6.txt) no s'hi torna a colar mai,
    per moltes vegades que es cridi.
    """
    trobats = []
    for nom in sorted(os.listdir(DIR_TXT)):
        carpeta = os.path.join(DIR_TXT, nom)
        if not os.path.isdir(carpeta):
            continue
        for arrel, _, noms in os.walk(carpeta):
            trobats += [os.path.join(arrel, n) for n in noms if n.endswith(".txt")]
    if not trobats:
        raise SystemExit(f"No hi ha cap .txt a les subcarpetes de {DIR_TXT}")
    return sorted(trobats)


def ajuntar(fitxers, sortida):
    """
    Copia els fitxers un darrere l'altre, en binari i a trossos (són 280 MB:
    no cal tenir-los mai tots a la memòria). Retorna el nombre de línies.

    Si un fitxer no acaba en salt de línia, l'hi afegeix: si no, l'última
    línia d'un i la primera del següent quedarien enganxades.
    """
    linies = 0
    with open(sortida, "wb") as sortint:
        for ruta in fitxers:
            ultim = b"\n"
            with open(ruta, "rb") as entrant:
                while tros := entrant.read(1 << 20):
                    linies += tros.count(b"\n")
                    sortint.write(tros)
                    ultim = tros[-1:]
            if ultim != b"\n":
                sortint.write(b"\n")
                linies += 1
    return linies


# --------------------------------------------- 2. la columna_3 de la prova

def escriure_col_3_prova(tot, base, sortida):
    """
    col_3 del diccionari real + col_3 de tot.txt, en aquest ordre: la columna
    de rimes que tindria un diccionari v.6 que incorporés les formes amb
    pronom al darrere de les d'ara. Retorna (línies del base, línies noves).

    Compte amb l'última línia de col_3.txt, que no porta salt de línia: sense
    afegir-l'hi, l'última rima del diccionari i la primera amb pronom
    quedarien fetes una sola línia ("ɛt" + "anəl" -> "ɛtanəl").
    """
    with open(sortida, "w", encoding="utf-8") as sortint:
        with open(base, "r", encoding="utf-8") as f:
            velles = 0
            for rima in f:
                sortint.write(rima if rima.endswith("\n") else rima + "\n")
                velles += 1

        with open(tot, "r", encoding="utf-8") as f:
            noves = 0
            for linia in f:
                camps = linia.rstrip("\n").split("$")
                if len(camps) == CAMPS:
                    sortint.write(camps[COL_RIMA_CONSONANT] + "\n")
                    noves += 1
    return velles, noves


# ------------------------------------------------------- 3. els recomptes

def comptar_linies(ruta):
    """
    Repassa el document línia per línia (sense carregar-lo sencer) i en torna
    el recompte: {línia: quantes vegades hi surt}.

    Torna el Counter sencer i no els totals ja fets perquè les preguntes que
    creuen els dos documents (quines rimes deixen de ser úniques) necessiten
    saber quantes vegades surt cada línia a cada banda, no només quantes n'hi
    ha de diferents.
    """
    vistes = Counter()
    with open(ruta, "r", encoding="utf-8") as f:
        for linia in f:
            vistes[linia.rstrip("\n")] += 1
    return vistes


def totals(vistes):
    """(línies, diferents, úniques) a partir del recompte d'un document."""
    return (sum(vistes.values()),
            len(vistes),
            sum(1 for n in vistes.values() if n == 1))


def percent(part, total):
    """'1,62 %', amb la coma decimal de casa."""
    return f"{part / total * 100:.2f} %".replace(".", ",") if total else "--"


def decimal(x):
    """61.64 -> '61,64' (punt de milers, coma decimal)."""
    return f"{x:,.2f}".replace(",", "§").replace(".", ",").replace("§", ".")


def informe(documents):
    """
    La taula: un document per fila, sempre els mateixos recomptes.

    Cada recompte va amb el seu percentatge, i el denominador no és el mateix
    a tot arreu -- per això les columnes el diuen:

      diferents / línies      quanta repetició hi ha (com més baix, més
                              paraules comparteixen rima)
      línies / diferents      la mateixa cosa del dret: quantes paraules té
                              de mitjana cada classe de rima
      úniques / línies        quina part del document no rima amb res
      úniques / diferents     quina part de les CLASSES de rima té un sol
                              membre, que és la mateixa xifra mirada des de
                              les rimes i no des de les paraules
    """
    comptadors = {}
    for nom, ruta in documents:
        if not os.path.exists(ruta):
            raise SystemExit(f"No hi ha {ruta}.\n"
                             "Descomenta els passos 1 i 2 de main() per generar-lo.")
        comptadors[nom] = comptar_linies(ruta)
    resultats = [(nom,) + totals(c) for nom, c in comptadors.items()]

    ample = max(len(nom) for nom, *_ in resultats)
    print(f"  {'document':{ample}s} {'línies':>12s} {'diferents':>11s}"
          f" {'/línies':>9s} {'mitjana':>9s} {'úniques':>11s} {'/línies':>9s}"
          f" {'/difer.':>9s}")
    for nom, linies, diferents, uniques in resultats:
        print(f"  {nom:{ample}s} {mil(linies):>12s}"
              f" {mil(diferents):>11s} {percent(diferents, linies):>9s}"
              f" {decimal(linies / diferents):>9s}"
              f" {mil(uniques):>11s} {percent(uniques, linies):>9s}"
              f" {percent(uniques, diferents):>9s}")

    print("\n  diferents = valors distints (les classes de rima)")
    print("  úniques   = valors que surten exactament un cop")
    print("  mitjana   = línies / diferents: quantes vegades es repeteix de"
          " mitjana")
    print("              cada línia diferent")
    print("  /línies   = sobre el total de línies del document")
    print("  /difer.   = úniques sobre les diferents: quina part de les classes"
          " de rima")
    print("              té un sol membre")
    return comptadors


def rescatades(base, prova):
    """
    Les rimes que a col_3 són úniques i a col_3_prova_v.6 ja no.

    És a dir: paraules del diccionari que avui no rimen amb res i que, si
    s'hi afegissin les formes amb pronom, passarien a rimar amb alguna cosa.
    Com que la prova és col_3 + les formes noves, "ja no és única" vol dir
    exactament que hi ha arribat companyia de fora.
    """
    return sorted(r for r, n in base.items() if n == 1 and prova[r] > 1)


def paraules_de(rimes):
    """
    La paraula que hi ha darrere de cada rima al diccionari. col_0 i col_3
    van alineades línia per línia, i com que aquestes rimes són úniques, cada
    una té una sola paraula.
    """
    volem = set(rimes)
    trobades = {}
    with open(COL_0_BASE, encoding="utf-8") as f0, \
         open(COL_3_BASE, encoding="utf-8") as f3:
        for paraula, rima in zip(f0, f3):
            rima = rima.rstrip("\n")
            if rima in volem:
                trobades.setdefault(rima, paraula.rstrip("\n"))
    return trobades


def informe_rescatades(base, prova, mostra=25):
    llista = rescatades(base, prova)
    uniques_base = sum(1 for n in base.values() if n == 1)
    print(f"RIMES QUE A col_3 SÓN ÚNIQUES I A LA PROVA JA NO\n")
    print(f"  {mil(len(llista))} de les {mil(uniques_base)} rimes úniques de"
          f" col_3 ({percent(len(llista), uniques_base)})")
    print("  són paraules que avui no rimen amb res i que hi guanyarien"
          " companyia:\n")

    paraules = paraules_de(llista)
    for rima in llista[:mostra]:
        companyia = prova[rima] - 1
        print(f"    {paraules.get(rima, ''):22s} {rima:14s}"
              f" +{mil(companyia):>7s} formes")
    if len(llista) > mostra:
        print(f"    ... i {mil(len(llista) - mostra)} més")
    return llista


def main():
    # --- Passos 1 i 2: ja fets. Descomenta'ls per refer els dos fitxers.
    #
    # fitxers = fitxers_font()
    # linies = ajuntar(fitxers, FITXER_TOT)
    # print(f"1. Ajuntats {len(fitxers)} fitxers -> "
    #       f"{os.path.relpath(FITXER_TOT, BASE_DIR)}")
    # print(f"   {mil(linies)} línies, {os.path.getsize(FITXER_TOT) / 1e6:,.0f} MB\n")
    #
    # velles, noves = escriure_col_3_prova(FITXER_TOT, COL_3_BASE, FITXER_PROVA)
    # print(f"2. Escrit {os.path.relpath(FITXER_PROVA, BASE_DIR)}")
    # print(f"   {mil(velles)} rimes de col_3.txt + {mil(noves)} de tot.txt"
    #       f" = {mil(velles + noves)} línies\n")

    print("RECOMPTE DE LÍNIES\n")
    comptadors = informe([("col_3.txt", COL_3_BASE),
                          ("col_3_prova_v.6.txt", FITXER_PROVA)])

    print()
    informe_rescatades(comptadors["col_3.txt"],
                       comptadors["col_3_prova_v.6.txt"])


if __name__ == "__main__":
    main()
