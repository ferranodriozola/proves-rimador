"""
Com surten els errors i els avisos, perquè no quedin per mirar.

Un print va al registre de l'execució, i el registre d'una execució verda no
el llegeix ningú. Als workflows, GitHub té tres canals de debò i aquí es fan
servir tots tres, cadascun per a una cosa:

    error()   ::error::    requadre vermell a dalt de l'execució i, si el
                           procés surt amb codi != 0, correu
    avis()    ::warning::  triangle groc a dalt de l'execució ENCARA QUE
                           acabi verda. No envia cap correu
    taula()   summary      la pàgina "Summary" de l'execució, en markdown

Si l'anotació porta un fitxer i una línia, surt DINS del diff del commit, que
és on estàs mirant quan has fet la cagada.

FORA DELS WORKFLOWS no s'escriu res d'això: en local, les anotacions són
soroll il·legible, i el que es veu és un print de tota la vida.

QUANTES. GitHub només n'ensenya una desena per pas. Per això la norma és una
anotació que digui el TOTAL i el detall sencer al summary (i, quan toca, a un
fitxer comitejat, que és l'única manera que una llista quedi al diff quan
canvia i no faci soroll quan no).

ELS AVISOS NO ENVIEN CORREU, MAI. Si una cosa t'ha d'arribar al correu, ha de
ser un error i ha de fer petar el workflow: plegar().
"""

import atexit
import os
import sys

ALS_WORKFLOWS = os.environ.get("GITHUB_ACTIONS") == "true"
FITXER_RESUM = os.environ.get("GITHUB_STEP_SUMMARY")

_resum = []


def _escapar(text):
    """Les anotacions van en una sola línia i el % hi és especial."""
    return (str(text).replace("%", "%25")
                     .replace("\r", "%0D")
                     .replace("\n", "%0A"))


def _anotacio(mena, text, fitxer=None, linia=None):
    lloc = ""
    if fitxer:
        lloc = f" file={fitxer}"
        if linia:
            lloc += f",line={linia}"
    print(f"::{mena}{lloc}::{_escapar(text)}")


def error(text, fitxer=None, linia=None):
    """Una cosa que ha d'aturar la publicació. NO surt del programa: qui crida
    decideix si en vol dir més abans de plegar."""
    if ALS_WORKFLOWS:
        _anotacio("error", text, fitxer, linia)
    else:
        print(f"ERROR: {text}", file=sys.stderr)


def avis(text, fitxer=None, linia=None):
    """Una cosa per mirar que no atura res."""
    if ALS_WORKFLOWS:
        _anotacio("warning", text, fitxer, linia)
    else:
        print(f"AVÍS: {text}")


def nota(text):
    """El que sempre s'ha escrit: el compte de files, què s'ha fet."""
    print(text)


def taula(titol, capçaleres, files, maxim=50):
    """Una taula al Summary de l'execució. En local, les primeres files i
    prou: a la terminal, cinquanta línies de taula no les llegeix ningú."""
    if not files:
        return
    if ALS_WORKFLOWS:
        _resum.append(f"### {titol}\n")
        _resum.append("| " + " | ".join(capçaleres) + " |")
        _resum.append("|" + "---|" * len(capçaleres))
        for fila in files[:maxim]:
            _resum.append("| " + " | ".join(str(t) for t in fila) + " |")
        if len(files) > maxim:
            _resum.append(f"\n_...i {len(files) - maxim} més._\n")
        _resum.append("")
    else:
        print(f"\n{titol}:")
        for fila in files[:10]:
            print("   " + "  ".join(str(t) for t in fila))
        if len(files) > 10:
            print(f"   ...i {len(files) - 10} més")


def text_al_resum(text):
    if ALS_WORKFLOWS:
        _resum.append(text)


def plegar(text, fitxer=None, linia=None):
    """Error i fora, amb codi 1: el pas del workflow es posa vermell, el job
    s'atura, el desplegament no arrenca i el commit no es fa. És l'única
    manera que t'arribi un correu."""
    error(text, fitxer, linia)
    sys.exit(1)


@atexit.register
def _bolcar():
    """El summary s'escriu passi el que passi, també quan s'ha plegat: si un
    error deixés la taula del detall sense escriure, hauries de baixar al
    registre a buscar-la, que és justament el que estem evitant."""
    if not (_resum and FITXER_RESUM):
        return
    try:
        with open(FITXER_RESUM, "a", encoding="utf-8") as fitxer:
            fitxer.write("\n".join(_resum) + "\n")
    except OSError:
        pass
