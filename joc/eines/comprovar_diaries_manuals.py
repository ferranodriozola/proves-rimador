#!/usr/bin/env python3
"""Comprova que les paraules del dades/diaries_manuals.json existeixen als
quatre dialectes com a paraules objectiu (*  o +) i mostra quantes rimes te
cadascuna. Passeu-lo abans de publicar paraules noves."""

import json
import os
import re
import sys
import unicodedata

DIR_EINES = os.path.dirname(os.path.abspath(__file__))
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


if __name__ == "__main__":
    main()
