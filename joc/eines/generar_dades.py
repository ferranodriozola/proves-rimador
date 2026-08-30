# Generador de les dades del joc de rimes.
#
# Llegeix el diccionari i les columnes de rima de CADA dialecte i n'escriu, per
# dialecte, el que el joc necessita per jugar-hi:
#
#   joc/dades/<codi>/index.json    -> les claus de rima consonant que tenen prou
#                                     rimes per fer-hi una partida, amb quin
#                                     fitxer les conte i quantes paraules
#                                     objectiu (no verbs) hi ha.
#   joc/dades/<codi>/rimes/N.txt   -> un fitxer per grup assonant, dividit per
#                                     dins en seccions de rima consonant.
#   joc/dades/versions.json        -> el resum de cada fitxer generat, que es
#                                     com el joc sap si la copia que te el
#                                     navegador encara val (igual que
#                                     diccionaris/versions.json).
#
# La gracia: la clau consonant determina sempre la clau assonant (comprovat, i
# es torna a comprovar aqui a cada passada), o sigui que un sol fitxer per grup
# assonant serveix les dues dificultats. Facil = totes les paraules del fitxer;
# dificil = nomes la seccio de la paraula objectiu. Una sola descarrega per
# partida.
#
# Format de cada fitxer de rimes:
#
#   #aðə              <- capcalera de seccio: clau de rima consonant
#   *cascada          <- l'* marca les paraules que poden ser OBJECTIU (no verbs)
#   cavalcava         <- sense *, nomes val com a RIMA (aqui, una forma verbal)
#   *cami>camí        <- si la forma real porta accents, va despres del ">"
#
# Aixi el joc no ha de normalitzar res en temps d'execucio, i sap de seguida
# quines paraules pot proposar com a objectiu i quines nomes accepta com a rima.
#
# ON SON LES DADES: no se sap aqui. Els camins surten de
# diccionaris/python/camins.py, que es el vocabulari compartit de tots els
# scripts del repositori. La rima no es al diccionari (depen de com es parli) i
# viu a dialectes_col/<codi>/; els dialectes que hi ha son les subcarpetes
# d'alla i no es declaren enlloc.
#
# Execucio (des d'on sigui):
#   python joc/eines/generar_dades.py             tots els dialectes
#   python joc/eines/generar_dades.py ca va       nomes aquests

import collections
import hashlib
import json
import os
import shutil
import sys
import unicodedata
from datetime import datetime, timezone

# camins.py sap on es cada cosa i com es diu. Es el mateix modul que fan servir
# els scripts del diccionari, o sigui que si un dia les columnes es tornen a
# moure, el joc les segueix sense tocar res d'aqui.
DIR_EINES = os.path.dirname(os.path.abspath(__file__))
ARREL = os.path.dirname(os.path.dirname(DIR_EINES))
sys.path.insert(0, os.path.join(ARREL, "diccionaris", "python"))

import camins  # noqa: E402

# --- Configuracio -----------------------------------------------------------

# Rimes minimes que ha de tenir una clau consonant per poder-hi jugar. Com que
# la clau consonant implica la clau assonant, complir-ho en consonant ja ho
# garanteix en assonant.
MIN_RIMES = 50

# Els verbs no poden ser paraula objectiu (seria massa facil rimar-hi amb altres
# formes verbals), pero si que valen com a resposta. Els noms propis no compten
# ni per objectiu ni per resposta.
EXCLOURE_VERBS_OBJECTIU = True

# Si es posa a True, els plurals tampoc poden ser objectiu.
EXCLOURE_PLURALS_OBJECTIU = False

# Com es diu cada dialecte a la pantalla i EN QUIN ORDRE surt a la tira. Ha de
# coincidir amb la llista DIALECTES de js/components.js, que es la que pinta la
# tira del cercador: el joc no comparteix JS amb la web i se'ls ha de dir el nom
# a la seva manera, pero les dues tires han d'ensenyar el mateix i en el mateix
# ordre.
#
# Els codis, en canvi, no surten d'aqui sino de camins.dialectes(): un dialecte
# nou es una carpeta a dialectes_col/ i prou. Si n'hi ha un que no es en aquest
# mapa, es genera igualment i el joc n'ensenyara el codi tal qual, al final de
# la tira: lleig, pero no trencat ni silenciat.
NOMS_DE_DIALECTE = {
    "ca": "Central",
    "nw": "Nord-occidental",
    "va": "Valencià",
    "ba": "Balear",
}


def ordre_de_tira(codis):
    """Els codis en l'ordre de NOMS_DE_DIALECTE (el de la tira del cercador), i
    els que no hi surtin, al final i per ordre alfabetic."""
    coneguts = [c for c in NOMS_DE_DIALECTE if c in codis]
    return coneguts + sorted(c for c in codis if c not in NOMS_DE_DIALECTE)

DIR_DADES = os.path.join(ARREL, "joc", "dades")
VERSIONS = os.path.join(DIR_DADES, "versions.json")


# --- Utilitats --------------------------------------------------------------


def normalitzar(paraula):
    """Minuscules, sense accents, sense punt volat. Ha de coincidir exactament
    amb normalitza() de joc/js/normalitza.js."""
    text = paraula.strip().lower().replace("·", "").replace("’", "'")
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def es_resposta_valida(paraula, codi):
    """Val com a rima: qualsevol paraula que no sigui nom propi ni una sigla."""
    if not paraula:
        return False
    if codi[:2] == "NP":
        return False
    normalitzada = normalitzar(paraula)
    if not normalitzada:
        return False
    # Fora xifres i caracters estranys. Els guionets i apostrofs enmig si valen
    # (p. ex. "adeu-siau").
    return normalitzada.replace("-", "").replace("'", "").isalpha()


def pot_ser_objectiu(codi):
    """Val com a paraula a rimar. Ja sabem que es resposta valida."""
    if EXCLOURE_VERBS_OBJECTIU and codi[0] == "V":
        return False
    if EXCLOURE_PLURALS_OBJECTIU:
        if codi[0] == "N" and len(codi) > 3 and codi[3] == "P":
            return False
        if codi[0] in "AD" and len(codi) > 4 and codi[4] == "P":
            return False
    return True


def escriure_si_cal(cami, text):
    """Refer-ho tot a cada passada vol dir reescriure desenes de MB que el git
    ni tan sols mirara, i deixa la data de tots els fitxers canviada per no
    res. Torna si ha calgut escriure'l."""
    if os.path.exists(cami):
        with open(cami, encoding="utf-8") as fitxer:
            if fitxer.read() == text:
                return False
    os.makedirs(os.path.dirname(cami), exist_ok=True)
    with open(cami, "w", encoding="utf-8", newline="\n") as fitxer:
        fitxer.write(text)
    return True


def resum(cami):
    """La versio d'un fitxer es un resum del seu contingut, com a
    diccionaris/python/versions.py: es refresca exactament quan el fitxer ha
    canviat, ni abans ni de mes."""
    calculador = hashlib.sha256()
    with open(cami, "rb") as fitxer:
        for tros in iter(lambda: fitxer.read(1024 * 1024), b""):
            calculador.update(tros)
    return calculador.hexdigest()[:12]


# --- Un dialecte ------------------------------------------------------------


def generar_dialecte(codi, paraules, codis):
    """Escriu joc/dades/<codi>/ i torna un resum del que ha sortit."""
    rima_cons = camins.llegir_columna(camins.cami_dialecte(codi, 3))
    rima_asson = camins.llegir_columna(camins.cami_dialecte(codi, 4))

    total = len(paraules)
    if not (len(rima_cons) == len(rima_asson) == total):
        raise SystemExit(
            f"[{codi}] les columnes de rima tenen {len(rima_cons)} i "
            f"{len(rima_asson)} files, i el diccionari en te {total}. "
            "Passa el columnes.py.")

    # clau consonant -> {forma normalitzada: forma per mostrar}
    grups = collections.defaultdict(dict)
    # clau consonant -> {formes normalitzades que poden ser objectiu}
    objectius = collections.defaultdict(set)
    # clau consonant -> clau assonant
    cons_a_asson = {}

    for i in range(total):
        paraula, codi_gramatical = paraules[i], codis[i]
        if not es_resposta_valida(paraula, codi_gramatical):
            continue

        clau = rima_cons[i]
        normalitzada = normalitzar(paraula)
        grup = grups[clau]
        # Si dues entrades cauen a la mateixa forma normalitzada (dona / dóna),
        # ens quedem la mes curta d'escriure: nomes es per mostrar-la.
        if normalitzada not in grup or len(paraula) < len(grup[normalitzada]):
            grup[normalitzada] = paraula

        # Una forma es objectiu si ALGUNA de les seves entrades no es verb
        # (p. ex. "poder" es verb i nom; com a nom, pot ser objectiu).
        if pot_ser_objectiu(codi_gramatical):
            objectius[clau].add(normalitzada)

        anterior = cons_a_asson.setdefault(clau, rima_asson[i])
        if anterior != rima_asson[i]:
            raise SystemExit(
                f"[{codi}] la clau consonant '{clau}' apunta a dues claus "
                f"assonants ('{anterior}' i '{rima_asson[i]}'): el joc no ho "
                "suporta, perque es el que li permet servir les dues "
                "dificultats amb un sol fitxer.")

    qualificades = sorted(
        clau for clau, grup in grups.items()
        if len(grup) > MIN_RIMES and len(objectius[clau]) > 0
    )
    if not qualificades:
        raise SystemExit(f"[{codi}] cap clau supera el minim de rimes amb objectius.")

    # Nomes generem els grups assonants que fan falta per a alguna clau
    # qualificada. Cada fitxer, pero, conte el grup assonant sencer: fa falta
    # per validar les respostes en mode facil.
    asson_necessaris = sorted({cons_a_asson[clau] for clau in qualificades})
    id_de_asson = {clau: i for i, clau in enumerate(asson_necessaris)}

    claus_per_asson = collections.defaultdict(list)
    for clau in grups:
        claus_per_asson[cons_a_asson[clau]].append(clau)

    dir_dialecte = os.path.join(DIR_DADES, codi)
    dir_rimes = os.path.join(dir_dialecte, "rimes")
    os.makedirs(dir_rimes, exist_ok=True)
    # Els fitxers es numeren per posicio dins la llista de grups assonants, o
    # sigui que si el diccionari canvia poden sobrar-ne: fora els vells, que si
    # no quedarien servint-se sense que cap index hi apunti.
    esperats = {f"{i}.txt" for i in range(len(asson_necessaris))}
    for antic in os.listdir(dir_rimes):
        if antic.endswith(".txt") and antic not in esperats:
            os.remove(os.path.join(dir_rimes, antic))

    escrits = 0
    bytes_totals = 0
    for clau_asson in asson_necessaris:
        linies = []
        for clau_cons in sorted(claus_per_asson[clau_asson]):
            linies.append("#" + clau_cons)
            grup = grups[clau_cons]
            es_objectiu = objectius[clau_cons]
            for normalitzada in sorted(grup):
                mostrar = grup[normalitzada]
                cos = normalitzada if mostrar == normalitzada else f"{normalitzada}>{mostrar}"
                linies.append(("*" + cos) if normalitzada in es_objectiu else cos)
        cami = os.path.join(dir_rimes, f"{id_de_asson[clau_asson]}.txt")
        contingut = "\n".join(linies)
        if escriure_si_cal(cami, contingut):
            escrits += 1
        bytes_totals += len(contingut.encode("utf-8"))

    # index.json: per cada clau qualificada, a quin fitxer es i quantes paraules
    # objectiu hi ha. El joc tria la clau amb probabilitat proporcional al nombre
    # d'objectius, o sigui que totes les paraules objectiu son igual de probables.
    index = {
        "dialecte": codi,
        "min_rimes": MIN_RIMES,
        "fitxers": len(asson_necessaris),
        "claus": [
            [clau, id_de_asson[cons_a_asson[clau]], len(objectius[clau])]
            for clau in qualificades
        ],
    }
    if escriure_si_cal(os.path.join(dir_dialecte, "index.json"),
                       json.dumps(index, ensure_ascii=False, separators=(",", ":"))):
        escrits += 1

    total_objectius = sum(len(objectius[clau]) for clau in qualificades)
    print(f"  {codi}: {len(qualificades)} claus jugables, {camins.mil(total_objectius)} "
          f"paraules objectiu, {len(asson_necessaris)} fitxers, "
          f"{bytes_totals / 1048576:.1f} MB ({escrits} fitxers reescrits)")

    return {"claus": len(qualificades), "objectius": total_objectius,
            "fitxers": len(asson_necessaris)}


# --- Proces -----------------------------------------------------------------


def main():
    demanats = sys.argv[1:]
    tots = camins.dialectes()
    if not tots:
        raise SystemExit("No hi ha cap dialecte a dialectes_col/.")
    codis = demanats or tots
    for codi in codis:
        if codi not in tots:
            raise SystemExit(f"El dialecte '{codi}' no es a dialectes_col/. Hi ha: "
                             f"{', '.join(tots)}")

    print("Llegint el diccionari...")
    paraules = camins.llegir_columna(camins.cami_columna(0))
    codis_gramaticals = camins.llegir_columna(camins.cami_columna(2))
    if len(paraules) != len(codis_gramaticals):
        raise SystemExit("La col_0 i la col_2 no tenen el mateix nombre de files.")
    print(f"  {camins.mil(len(paraules))} entrades")

    print(f"Generant {len(codis)} dialecte{'s' if len(codis) > 1 else ''}...")
    resums = {}
    for codi in codis:
        resums[codi] = generar_dialecte(codi, paraules, codis_gramaticals)

    # Si nomes se n'ha regenerat un, els altres que ja hi hagi es queden i han
    # de continuar sortint al versions.json.
    presents = sorted(
        nom for nom in os.listdir(DIR_DADES)
        if os.path.isdir(os.path.join(DIR_DADES, nom))
        and os.path.exists(os.path.join(DIR_DADES, nom, "index.json"))
    )
    # I si un dialecte ha desaparegut de dialectes_col/, fora la seva carpeta:
    # si no, el versions.json continuaria oferint-lo a la tira del joc.
    for nom in list(presents):
        if nom not in tots:
            print(f"  (fora {nom}/: ja no es a dialectes_col/)")
            shutil.rmtree(os.path.join(DIR_DADES, nom))
            presents.remove(nom)

    escriure_versions(presents)

    print(f"Fet: {len(presents)} dialectes a joc/dades/ "
          f"({', '.join(presents)}).")


def escriure_versions(codis):
    """El versions.json del joc, germa de diccionaris/versions.json.

    Mateixa idea: la versio de cada fitxer es un resum del seu contingut, i el
    navegador la fa servir per saber si la copia que te encara val (vegeu
    carregarVersions a joc/js/dades.js). El fitxer que diu que hi ha versions
    no es pot cachejar mai; tota la resta, per sempre.

    A DIFERENCIA del versions.json del diccionari, aqui les claus son CAMINS i
    no noms de fitxer sols: alla el navegador indexa la memoria cau pel nom
    (rutaFitxer.split("/").pop()) i cada fitxer es unic, pero aqui el
    ca/rimes/0.txt i el va/rimes/0.txt es dirien igual.
    """
    fitxers = {}
    for codi in codis:
        dir_dialecte = os.path.join(DIR_DADES, codi)
        fitxers[f"{codi}/index.json"] = resum(os.path.join(dir_dialecte, "index.json"))
        dir_rimes = os.path.join(dir_dialecte, "rimes")
        for nom in sorted(os.listdir(dir_rimes), key=lambda n: int(n.split(".")[0])):
            if nom.endswith(".txt"):
                fitxers[f"{codi}/rimes/{nom}"] = resum(os.path.join(dir_rimes, nom))

    contingut = {
        "generat": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        # En l'ordre de la tira, no per ordre alfabetic: aquesta llista es la
        # que el joc pinta tal com li arriba (vegeu pintarTiraDialectes a
        # joc/js/ui.js).
        "dialectes": [
            {"codi": codi, "nom": NOMS_DE_DIALECTE.get(codi, codi)}
            for codi in ordre_de_tira(codis)
        ],
        "fitxers": fitxers,
    }
    with open(VERSIONS, "w", encoding="utf-8", newline="\n") as fitxer:
        json.dump(contingut, fitxer, ensure_ascii=False, indent=2)
        fitxer.write("\n")
    print(f"versions.json: {len(fitxers)} fitxers, dialectes {', '.join(codis)}")


if __name__ == "__main__":
    main()
