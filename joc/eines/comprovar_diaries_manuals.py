# Comprova les paraules del dia triades a ma (joc/dades/diaries_manuals.json).
#
# El joc les resol en temps d'execucio buscant-les al fitxer del dialecte que
# es juga (vegeu trobarObjectiu a joc/js/dades.js), i si no les hi troba com a
# paraula a rimar aquell dialecte juga amb la roda de sempre sense que ningu
# se n'adoni. Aquest script fa la mateixa cerca als QUATRE fitxers abans de
# publicar res, i diu, de cada paraula i dialecte:
#
#   - si hi es i pot ser objectiu ("*" o "+" al fitxer);
#   - quantes rimes te en dificil (la seva seccio) i en facil (el grup sencer),
#     perque una paraula amb tres mil rimes en balear i cent en central no es
#     la mateixa partida per a tothom (la finestra dels modes normals es de
#     MIN_RIMES a MAX_RIMES: vegeu generar_dades.py).
#
# Surt amb error si alguna paraula no es troba en algun dialecte o si el JSON
# esta mal format. Els avisos de finestra no fan petar res: son perque ho
# sapigueu, que un dia assenyalat pot valer la pena una paraula facil.
#
# Execucio (des d'on sigui):
#   python joc/eines/comprovar_diaries_manuals.py

import json
import os
import re
import sys
import unicodedata

DIR_EINES = os.path.dirname(os.path.abspath(__file__))
DIR_DADES = os.path.join(os.path.dirname(DIR_EINES), "dades")
FITXER = os.path.join(DIR_DADES, "diaries_manuals.json")

DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def normalitzar(paraula):
    """El mateix que normalitza() de joc/js/normalitza.js."""
    text = paraula.strip().lower().replace("·", "").replace("’", "'")
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def llegir_manuals():
    with open(FITXER, encoding="utf-8") as f:
        manuals = json.load(f)
    if not isinstance(manuals, dict):
        raise SystemExit(f"{FITXER}: ha de ser un objecte de data a paraula.")

    entrades = []   # (data, dificultat, paraula)
    for data, valor in manuals.items():
        if not DATA.match(data):
            continue   # "_ajuda", "_exemple"...
        if isinstance(valor, str):
            entrades += [(data, "facil", valor), (data, "dificil", valor)]
        elif isinstance(valor, dict):
            for dificultat in ("facil", "dificil"):
                if dificultat in valor:
                    if not isinstance(valor[dificultat], str):
                        raise SystemExit(f"{data}/{dificultat}: ha de ser una paraula.")
                    entrades.append((data, dificultat, valor[dificultat]))
            for clau in valor:
                if clau not in ("facil", "dificil"):
                    raise SystemExit(f"{data}: la clau '{clau}' no es ni 'facil' ni 'dificil'.")
        else:
            raise SystemExit(f"{data}: ha de ser una paraula o un objecte amb facil/dificil.")
    return entrades


def llegir_dialecte(codi, index):
    """paraula normalitzada -> (marca, mostrar, rimes de la seccio, rimes del grup).
    La primera seccio on surt, com fa el joc."""
    tros = index["dialectes"][codi]
    grup_de = {c[0]: c[1] for c in tros["claus"]}
    rimes_de_clau = {c[0]: c[3] for c in tros["claus"]}
    rimes_de_grup = {i: g[3] for i, g in enumerate(tros["grups"])}

    trobades = {}
    clau = None
    with open(os.path.join(DIR_DADES, f"{codi}.txt"), encoding="utf-8") as f:
        for linia in f:
            linia = linia.rstrip("\r\n")
            if not linia:
                continue
            if linia[0] == "#":
                clau = linia[1:]
                continue
            marca = linia[0] if linia[0] in "*+" else ""
            cos = linia[1:] if marca else linia
            normalitzada, _, mostrar = cos.partition(">")
            if normalitzada in trobades or not marca:
                continue
            grup = grup_de.get(clau)
            trobades[normalitzada] = (marca, mostrar or normalitzada,
                                      rimes_de_clau.get(clau, 0),
                                      rimes_de_grup.get(grup, 0) if grup is not None else 0)
    return trobades


def main():
    entrades = llegir_manuals()
    if not entrades:
        print("No hi ha cap paraula manual: tot va amb la roda.")
        return

    with open(os.path.join(DIR_DADES, "index.json"), encoding="utf-8") as f:
        index = json.load(f)
    minim, maxim = index["min_rimes"], index["max_rimes"]
    codis = [d["codi"] for d in json.load(open(os.path.join(DIR_DADES, "versions.json"),
                                               encoding="utf-8"))["dialectes"]]

    print("Llegint els fitxers dels dialectes...")
    per_dialecte = {codi: llegir_dialecte(codi, index) for codi in codis}

    errors = 0
    for data, dificultat, paraula in sorted(entrades):
        normalitzada = normalitzar(paraula)
        print(f"\n{data} {dificultat}: «{paraula}»")
        for codi in codis:
            trobada = per_dialecte[codi].get(normalitzada)
            if not trobada:
                print(f"  {codi}: NO HI ES com a paraula a rimar -> aquest dialecte jugaria amb la roda")
                errors += 1
                continue
            marca, mostrar, seccio, grup = trobada
            rimes = seccio if dificultat == "dificil" else grup
            avis = ""
            if dificultat == "dificil" and not (minim <= seccio <= maxim):
                avis = f"  (fora de la finestra {minim}-{maxim} dels modes normals)"
            print(f"  {codi}: «{mostrar}» {marca} {rimes} rimes{avis}")

    print()
    if errors:
        raise SystemExit(f"{errors} problema(es): alguna paraula no es a tots els dialectes.")
    print("Tot correcte: totes les paraules manuals es troben als "
          f"{len(codis)} dialectes com a paraula a rimar.")


if __name__ == "__main__":
    main()
