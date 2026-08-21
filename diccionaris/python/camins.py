"""
On és cada cosa i com es diu. El vocabulari compartit de tots els scripts.

    diccionaris/
      diccionari.5.2.3.txt   QUINES paraules hi ha        (s'edita a mà)
      col_10.txt             COM sona cadascuna           (s'edita a mà)
      separat/               les columnes del web
        col_0,1,2,5,6,7,8.txt
        internat/            taula + idx de cada columna
    dialectes_col/<codi>/
      col_9_transcripcio_<codi>.txt    la transcripció   ─┐ SORTIDES:
      col_3_rimacons_<codi>.txt        rima consonant     │ es refan senceres
      col_4_rimaass_<codi>.txt         rima assonant      │ a cada passada.
      internat/                        taula + idx        ┘ NO S'EDITEN

ELS NÚMEROS DE COLUMNA són els de sempre i hi ha forats (el 3, el 4 i el 9 no
surten del diccionari sinó dels dialectes): el navegador, les llistes i el joc
demanen les columnes pel nom del fitxer, i renumerar-les voldria dir tocar-ho
tot per no guanyar res.

EL CODI DEL DIALECTE va dins del nom dels fitxers internats i no només a la
carpeta: la memòria cau del navegador i el versions.json s'indexen pel nom del
fitxer sol (vegeu llegirFitxerAmbIndexedDB a js/script.js, que fa
rutaFitxer.split("/").pop()), i quatre col_3.idx.txt serien la mateixa entrada.
"""

import os

DIR_SCRIPTS = os.path.dirname(os.path.abspath(__file__))

# L'arrel del repositori. RIMADOR_ARREL la canvia, i això només és per a les
# proves: hi ha una còpia de joguina de l'arbre (un diccionari de vint files,
# dos dialectes) i els scripts corren contra ella tal com són. Sense això, provar
# un moviment vol dir escriure 100 MB dues vegades.
ARREL = os.path.abspath(os.environ["RIMADOR_ARREL"]) if os.environ.get("RIMADOR_ARREL") \
        else os.path.dirname(os.path.dirname(DIR_SCRIPTS))
BASE = os.path.join(ARREL, "diccionaris")

DICCIONARI = os.path.join(BASE, "diccionari.5.2.3.txt")
COL_10 = os.path.join(BASE, "col_10.txt")
SEPARAT = os.path.join(BASE, "separat")
INTERNAT = os.path.join(SEPARAT, "internat")
VERSIONS = os.path.join(BASE, "versions.json")
DIALECTES_COL = os.path.join(ARREL, "dialectes_col")

# El dialecte de sempre: el que es publica mentre no es pugui triar, i l'únic
# amb la transcripció repassada a mà (els altres surten de l'espeak-ng).
CENTRAL = "ca"

# El diccionari: paraula, lema, codi, síl·labes, Vicc, Viq, Diec.
CAMPS = 7
# Quin camp del diccionari va a quina columna del web.
COLUMNES_DEL_DICCIONARI = (0, 1, 2, 5, 6, 7, 8)
# Les que no en surten, sinó de la transcripció de cada dialecte.
COLUMNES_DE_DIALECTE = (3, 4)
# Les que s'internen de cada banda.
INTERNADES_DEL_DICCIONARI = (1, 2, 5, 6, 7, 8)

NOMS = {3: "rimacons", 4: "rimaass", 9: "transcripcio"}

# Els tres primers camps: el que identifica una entrada. Són els únics que
# surten als DOS fitxers que s'editen, i per tant els únics on hi pot haver
# desacord (vegeu sincronitzar.py).
CAMPS_IDENTITAT = 3


def dialectes():
    """Els codis, que són les subcarpetes de dialectes_col/. Un dialecte nou
    és una carpeta amb la seva transcripció a dins: no es declara enlloc."""
    if not os.path.isdir(DIALECTES_COL):
        return []
    return sorted(
        nom for nom in os.listdir(DIALECTES_COL)
        if os.path.isdir(os.path.join(DIALECTES_COL, nom)) and not nom.startswith(".")
    )


def cami_dialecte(codi, numero):
    """dialectes_col/va/col_3_rimacons_va.txt"""
    return os.path.join(DIALECTES_COL, codi, f"col_{numero}_{NOMS[numero]}_{codi}.txt")


def cami_internat_dialecte(codi, numero, mena):
    """dialectes_col/va/internat/col_3_rimacons_va.idx.txt"""
    return os.path.join(DIALECTES_COL, codi, "internat",
                        f"col_{numero}_{NOMS[numero]}_{codi}.{mena}.txt")


def cami_columna(numero):
    """diccionaris/separat/col_5.txt"""
    return os.path.join(SEPARAT, f"col_{numero}.txt")


def cami_internat(numero, mena):
    """diccionaris/separat/internat/col_5.idx.txt"""
    return os.path.join(INTERNAT, f"col_{numero}.{mena}.txt")


def llegir_columna(cami):
    """Una columna és una línia per fila i NO acaba amb salt de línia. Si el
    fitxer en duu, se li perdona en llegir; en escriure no n'hi posem mai."""
    with open(cami, encoding="utf-8") as fitxer:
        text = fitxer.read()
    if text.endswith("\n"):
        text = text[:-1]
    return text.split("\n")


def escriure_columna(cami, valors):
    """Sense salt de línia al final: el navegador munta els seus arrays
    partint el text per '\\n' sense filtrar res (vegeu processarFitxerDeText a
    js/script.js), i un salt final li donaria una fila de més que quedaria
    desquadrada amb la resta de columnes.

    Si el fitxer ja diu això mateix, no s'hi torna a escriure: refer-ho tot a
    cada passada vol dir escriure centenars de MB que el git ni tan sols
    mirarà, i deixa la data del fitxer canviada per no res. Torna si ha
    calgut escriure'l."""
    return _escriure_si_cal(cami, "\n".join(valors))


def _escriure_si_cal(cami, text):
    if os.path.exists(cami):
        with open(cami, encoding="utf-8") as fitxer:
            if fitxer.read() == text:
                return False
    os.makedirs(os.path.dirname(cami), exist_ok=True)
    with open(cami, "w", encoding="utf-8") as fitxer:
        fitxer.write(text)
    return True


def llegir_diccionari(cami=None):
    """Les files del diccionari, cadascuna partida en els seus set camps."""
    files = []
    for numero, linia in enumerate(llegir_columna(cami or DICCIONARI), 1):
        if not linia:
            continue
        camps = linia.split("$")
        if len(camps) != CAMPS:
            from avisos import plegar
            plegar(f"diccionari.5.2.3.txt, línia {numero}: hi ha {len(camps)} camps i "
                   f"n'hi ha d'haver {CAMPS} (paraula, lema, codi, síl·labes, Vicc, "
                   f"Viq, Diec). Ni la rima ni la transcripció no hi van: són a "
                   f"dialectes_col/.", fitxer="diccionaris/diccionari.5.2.3.txt", linia=numero)
        files.append(camps)
    return files


def escriure_diccionari(files, cami=None):
    """El diccionari SÍ que acaba amb salt de línia: no és cap columna, és un
    fitxer de text normal i sempre n'ha dut."""
    return _escriure_si_cal(cami or DICCIONARI,
                            "\n".join("$".join(fila) for fila in files) + "\n")


def identitat(fila):
    """paraula$lema$codi, a partir d'una fila del diccionari o de la col_10."""
    return "$".join(fila[:CAMPS_IDENTITAT])


def mil(n):
    """619783 -> '619.783', com la resta de la documentació."""
    return f"{n:,}".replace(",", ".")
