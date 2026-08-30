# Generador de les dades del joc de rimes.
#
# Llegeix el diccionari i les columnes de rima de CADA dialecte i n'escriu SIS
# fitxers, ni un mes:
#
#   joc/dades/<codi>.txt      -> totes les rimes d'un dialecte, els grups
#                                assonants un darrere l'altre
#   joc/dades/index.json      -> les claus jugables dels quatre dialectes i, de
#                                cada grup assonant, on comenca i quant ocupa
#                                dins el seu fitxer
#   joc/dades/versions.json   -> el resum de cada fitxer, que es com el joc sap
#                                si la copia que te el navegador encara val
#                                (igual que diccionaris/versions.json)
#
# ABANS N'HI HAVIA 183, un per grup assonant i dialecte, perque una partida
# nomes necessita un grup i aixi no es baixava la resta. Sortia a 145 KB per
# partida, pero omplia el repositori de fitxers que no mira mai ningu. Ara el
# joc es baixa el dialecte sencer un sol cop (1,9 MB comprimits) i despres les
# partides no costen res: a partir de tretze ja hi surt guanyant. Els
# desplacaments son el que fa que no hagi d'interpretar els 7,6 MB per jugar amb
# un grup: talla el tros que li toca i prou.
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
# ELS DESPLACAMENTS SON EN BYTES, no en caracters: el joc es baixa el fitxer com
# a ArrayBuffer i nomes descodifica el tros que li toca (vegeu grupDeRimes a
# joc/js/dades.js). Comptar caracters seria demanar-se problemes, perque un
# index de Python son punts de codi i un de JavaScript son unitats UTF-16.
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
INDEX = os.path.join(DIR_DADES, "index.json")


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


def escriure_si_cal(cami, contingut):
    """Refer-ho tot a cada passada vol dir reescriure desenes de MB que el git
    ni tan sols mirara, i deixa la data de tots els fitxers canviada per no
    res. Accepta text o bytes. Torna si ha calgut escriure'l."""
    dades = contingut if isinstance(contingut, bytes) else contingut.encode("utf-8")
    if os.path.exists(cami):
        with open(cami, "rb") as fitxer:
            if fitxer.read() == dades:
                return False
    os.makedirs(os.path.dirname(cami), exist_ok=True)
    with open(cami, "wb") as fitxer:
        fitxer.write(dades)
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
    """Escriu joc/dades/<codi>.txt i torna el seu tros d'index."""
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

    # Un sol fitxer per dialecte: els grups assonants un darrere l'altre,
    # separats per un salt de linia. De cada grup n'apuntem on comenca i quant
    # ocupa, EN BYTES, que es el que despres permet al joc tallar-ne un sense
    # haver d'interpretar la resta.
    trossos = []
    desplacaments = []
    posicio = 0
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
        dades = "\n".join(linies).encode("utf-8")
        desplacaments.append([posicio, len(dades)])
        trossos.append(dades)
        posicio += len(dades) + 1   # +1 pel salt que els separa

    contingut = b"\n".join(trossos)
    escrit = escriure_si_cal(os.path.join(DIR_DADES, f"{codi}.txt"), contingut)

    total_objectius = sum(len(objectius[clau]) for clau in qualificades)
    print(f"  {codi}: {len(qualificades)} claus jugables, {camins.mil(total_objectius)} "
          f"paraules objectiu, {len(asson_necessaris)} grups, "
          f"{len(contingut) / 1048576:.1f} MB"
          f"{'' if escrit else ' (sense canvis)'}")

    # El tros d'index d'aquest dialecte. Les "claus" son igual que sempre
    # ([clau, numeroDeGrup, objectius]); el que abans era un numero de fitxer
    # ara es un numero dins de "grups".
    tros_index = {
        # La mida del fitxer sense comprimir. El joc la fa servir per dir quant
        # li queda mentre el baixa: el Content-Length que dona el servidor es el
        # del cos COMPRIMIT, i el lector del fetch va donant bytes ja
        # descomprimits, o sigui que comparar-los faria percentatges falsos.
        "bytes": len(contingut),
        "grups": desplacaments,
        "claus": [
            [clau, id_de_asson[cons_a_asson[clau]], len(objectius[clau])]
            for clau in qualificades
        ],
    }

    return tros_index


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
    trossos = {}
    for codi in codis:
        trossos[codi] = generar_dialecte(codi, paraules, codis_gramaticals)

    # L'index es un de sol per als quatre dialectes. Si nomes se n'ha regenerat
    # un, els altres s'han de quedar tal com estan: es llegeix el que hi ha i
    # nomes se'n substitueix el tros que toca.
    index = {}
    if os.path.exists(INDEX):
        try:
            with open(INDEX, encoding="utf-8") as fitxer:
                index = json.load(fitxer).get("dialectes", {})
        except (ValueError, OSError):
            index = {}   # si ve romput, es refa sencer
    index.update(trossos)

    # I si un dialecte ha desaparegut de dialectes_col/, fora de l'index i fora
    # el seu fitxer: si no, el versions.json continuaria oferint-lo a la tira.
    for codi in sorted(set(index) - set(tots)):
        print(f"  (fora {codi}: ja no es a dialectes_col/)")
        del index[codi]
        cami = os.path.join(DIR_DADES, f"{codi}.txt")
        if os.path.exists(cami):
            os.remove(cami)

    # Les restes del format vell, quan hi havia un fitxer per grup assonant.
    for codi in tots:
        vella = os.path.join(DIR_DADES, codi)
        if os.path.isdir(vella):
            print(f"  (fora {codi}/: era el format d'un fitxer per grup)")
            shutil.rmtree(vella)

    presents = ordre_de_tira(sorted(index))
    escriure_si_cal(INDEX, json.dumps(
        {"min_rimes": MIN_RIMES,
         "dialectes": {codi: index[codi] for codi in presents}},
        ensure_ascii=False, separators=(",", ":")))

    escriure_versions(presents)

    fitxers = 2 + len(presents)
    print(f"Fet: {len(presents)} dialectes ({', '.join(presents)}) en {fitxers} fitxers.")


def escriure_versions(codis):
    """El versions.json del joc, germa de diccionaris/versions.json.

    Mateixa idea: la versio de cada fitxer es un resum del seu contingut, i el
    navegador la fa servir per saber si la copia que te encara val (vegeu
    carregarVersions a joc/js/dades.js). El fitxer que diu que hi ha versions no
    es pot cachejar mai; tota la resta, per sempre.

    Ara son cinc entrades: l'index i un fitxer per dialecte.
    """
    fitxers = {"index.json": resum(INDEX)}
    for codi in codis:
        fitxers[f"{codi}.txt"] = resum(os.path.join(DIR_DADES, f"{codi}.txt"))

    contingut = {
        "generat": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        # En l'ordre de la tira, no per ordre alfabetic: aquesta llista es la
        # que el joc pinta tal com li arriba (vegeu pintarTiraDialectes a
        # joc/js/ui.js).
        "dialectes": [
            {"codi": codi, "nom": NOMS_DE_DIALECTE.get(codi, codi)} for codi in codis
        ],
        "fitxers": fitxers,
    }
    with open(VERSIONS, "w", encoding="utf-8", newline="\n") as fitxer:
        json.dump(contingut, fitxer, ensure_ascii=False, indent=2)
        fitxer.write("\n")
    print(f"versions.json: {len(fitxers)} fitxers, dialectes {', '.join(codis)}")


if __name__ == "__main__":
    main()
