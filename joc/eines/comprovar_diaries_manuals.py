<<<<<<< Updated upstream
#!/usr/bin/env python3
"""Comprova que les paraules del dades/diaries_manuals.json existeixen als
quatre dialectes com a paraules objectiu (*  o +) i mostra quantes rimes te
cadascuna. Passeu-lo abans de publicar paraules noves."""
=======
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
>>>>>>> Stashed changes

import json
import os
import re
import sys
import unicodedata

DIR_EINES = os.path.dirname(os.path.abspath(__file__))
<<<<<<< Updated upstream
DIR_JOC = os.path.dirname(DIR_EINES)
DIR_DADES = os.path.join(DIR_JOC, "dades")
MANUAL_JSON = os.path.join(DIR_DADES, "diaries_manuals.json")
DIALECTES = ("ca", "nw", "va", "ba")
MIN_RIMES = 30
MAX_RIMES = 800


def normalitza(paraula):
    """Mateixa normalitzacio que js/normalitza.js: minuscules, sense accents."""
    paraula = paraula.lower().strip()
    return "".join(
        c for c in unicodedata.normalize("NFD", paraula)
        if unicodedata.category(c) != "Mn"
    )


def llegir_dialecte(codi):
    cami = os.path.join(DIR_DADES, f"{codi}.txt")
    with open(cami, encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def buscar(text, normalitzada):
    """Busca la paraula al fitxer; torna (clau, n_rimes) o None."""
    m = re.search(rf"^[*+]{re.escape(normalitzada)}(?:>.*)?$", text, re.MULTILINE)
    if not m:
        return None
    cap = text.rfind("\n#", 0, m.start())
    if cap == -1:
        return None
    fi_linia = text.index("\n", cap + 1)
    clau = text[cap + 2 : fi_linia]
    seguent = text.find("\n#", fi_linia)
    if seguent == -1:
        seccio = text[fi_linia:]
    else:
        seccio = text[fi_linia:seguent]
    rimes = sum(1 for linia in seccio.splitlines() if linia and not linia.startswith("#"))
    return clau, rimes


def main():
    with open(MANUAL_JSON, encoding="utf-8") as f:
        manuals = json.load(f)

    textos = {codi: llegir_dialecte(codi) for codi in DIALECTES}
    errors = 0
    avisos = 0

    for data, entrada in sorted(manuals.items()):
        if data.startswith("_"):
            continue
        if isinstance(entrada, str):
            paraules = {"(totes)": entrada}
        elif isinstance(entrada, dict):
            paraules = {}
            if "facil" in entrada:
                paraules["facil"] = entrada["facil"]
            if "dificil" in entrada:
                paraules["dificil"] = entrada["dificil"]
        else:
            print(f"  !! {data}: format desconegut {entrada!r}")
            errors += 1
            continue

        for dificultat, paraula in paraules.items():
            norm = normalitza(paraula)
            print(f"\n  {data} [{dificultat}]: {paraula!r} -> {norm!r}")
            for codi in DIALECTES:
                resultat = buscar(textos[codi], norm)
                if resultat is None:
                    print(f"    {codi}: !! NO TROBADA com a objectiu")
                    errors += 1
                else:
                    clau, n = resultat
                    marca = ""
                    if n < MIN_RIMES:
                        marca = f"  (< {MIN_RIMES}, poc!)"
                        avisos += 1
                    elif n > MAX_RIMES:
                        marca = f"  (> {MAX_RIMES}, massa!)"
                        avisos += 1
                    print(f"    {codi}: \\{clau}\\ -> {n} rimes{marca}")

    print()
    if errors:
        print(f"  ERRORS: {errors} paraules no trobades.")
        sys.exit(1)
    elif avisos:
        print(f"  Tot trobat, pero {avisos} fora de la finestra {MIN_RIMES}-{MAX_RIMES}.")
    else:
        print("  Tot correcte.")
=======
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
>>>>>>> Stashed changes


if __name__ == "__main__":
    main()
