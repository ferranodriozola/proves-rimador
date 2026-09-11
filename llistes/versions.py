"""
Actualitza versions_llistes.json amb un resum sha256 del fitxer que acaba de
generar cada script de llistes/, igual que diccionaris/python/versions.py
fa amb les columnes del diccionari: la versió és un resum del contingut, no un
comptador manual que cal recordar de pujar i que puja igual encara que el
fitxer surti bit a bit idèntic.

Cada script de llistes/ genera el seu fitxer i prou (no van tots al mateix
commit, vegeu .github/workflows/generar_llistes.yml), o sigui que aquí només
es toca la clau pròpia: es llegeix el json sencer, es substitueix un valor i
es torna a escriure, sense tocar les claus dels altres scripts.
"""
import hashlib
import json
import os
from datetime import datetime, timezone

RUTA_VERSIONS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "versions_llistes.json")


def resum(cami):
    calculador = hashlib.sha256()
    with open(cami, "rb") as fitxer:
        for tros in iter(lambda: fitxer.read(1024 * 1024), b""):
            calculador.update(tros)
    return calculador.hexdigest()[:12]


def actualitzar_versio(nom_fitxer, cami_fitxer):
    """nom_fitxer és el nom pel qual el navegador el demana (p. ex.
    'paraules_naufragues_ca.json'), no pas el camí sencer: és la clau que fa
    servir VERSIONS_FITXERS a js/script.js (vegeu llegirFitxerAmbIndexedDB)."""
    try:
        with open(RUTA_VERSIONS, "r", encoding="utf-8") as fitxer:
            dades = json.load(fitxer)
    except FileNotFoundError:
        dades = {}

    dades.setdefault("fitxers", {})[nom_fitxer] = resum(cami_fitxer)
    dades["generat"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    with open(RUTA_VERSIONS, "w", encoding="utf-8") as fitxer:
        json.dump(dades, fitxer, ensure_ascii=False, indent=2)
        fitxer.write("\n")
