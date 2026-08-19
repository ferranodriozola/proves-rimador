# -*- coding: utf-8 -*-
"""
Comprova els fitxers que ha generat api_aina.py.

Fa dues coses ben diferents:

  1. REVISIÓ INTERNA (instantània, sense tocar l'API). Mira que hi siguin tots
     els mots, que cap línia no estigui buida i que no hi hagi rastres d'una
     altra resposta enganxats.

  2. VERIFICACIÓ CONTRA L'API (--mostra N). Agafa N mots a l'atzar, els demana
     d'un en un i mira que donin exactament el mateix que hi ha al fitxer. És
     l'única manera de detectar una transcripció que és perfecta però d'un
     altre mot; amb 200 mots ja veuries un problema de l'1%.

Ús:
    python3 comprova.py                          # revisió interna de col_0
    python3 comprova.py --mostra 200             # + verificació contra l'API
    python3 comprova.py --entrada ../../col_1.txt --dialectes Central
"""

import argparse
import glob
import os
import random
import re
import sys

from api_aina import (DIALECTES, PERFILS, Regulador, demanar_amb_reintents, mil,
                      neteja, sessio_nova)


def revisa(dialecte, linies, mots_unics, args):
    """Revisió interna d'un fitxer. Torna (problemes_greus, avisos)."""
    cami = f"{args.prefix}_{dialecte.lower()}.txt"
    if not os.path.exists(cami):
        pendents = os.path.join(args.cache, f"{args.prefix}__{dialecte}__pendents.txt")
        if os.path.exists(pendents):
            n = sum(1 for l in open(pendents, encoding="utf-8") if l.strip())
            return [f"{cami} no existeix: queden {mil(n)} mots per transcriure"], []
        return [f"{cami} no existeix"], []

    with open(cami, encoding="utf-8") as f:
        trans = [l.rstrip("\n") for l in f]

    greus, avisos = [], []
    if len(trans) != len(linies):
        greus.append(f"{cami}: {mil(len(trans))} línies, i l'entrada en té "
                     f"{mil(len(linies))}")
        return greus, avisos

    buides = [i for i, t in enumerate(trans) if not t.strip()]
    if buides:
        greus.append(f"{cami}: {mil(len(buides))} línies buides "
                     f"(la primera, la {buides[0] + 1})")

    dobles = [(linies[i], t) for i, t in enumerate(trans) if "  " in t]
    if dobles:
        greus.append(f"{cami}: {mil(len(dobles))} línies amb dos espais seguits "
                     f"— són restes d'una altra resposta. Exemple: {dobles[0]}")

    vores = [(linies[i], t) for i, t in enumerate(trans) if t != t.strip()]
    if vores:
        greus.append(f"{cami}: {mil(len(vores))} línies amb espais a la vora. "
                     f"Exemple: {vores[0]!r}")

    # Un mot sense guió ni apòstrof no hauria de donar espais. N'hi ha que sí
    # (AdWords -> 'ˈad bˈɔrs'), per això és un avís i no un error: val la pena
    # mirar-se la llista un cop, no cal patir-hi.
    rars = sorted({(linies[i], t) for i, t in enumerate(trans)
                   if " " in t and not re.search(r"[\s'’\-]", linies[i])})
    if rars:
        avisos.append(f"{cami}: {mil(len(rars))} mots sense guió ni apòstrof que "
                      f"es transcriuen amb espais. Exemples: {rars[:3]}")

    # coherència: el mateix mot ha de donar sempre la mateixa transcripció
    taula = {}
    incoherents = set()
    for mot, t in zip(linies, trans):
        if taula.setdefault(mot, t) != t:
            incoherents.add(mot)
    if incoherents:
        greus.append(f"{cami}: {mil(len(incoherents))} mots amb dues "
                     f"transcripcions diferents: {sorted(incoherents)[:3]}")

    if not greus:
        print(f"  ✓ {dialecte:12} {mil(len(trans))} línies, cap problema intern")
    return greus, avisos


def verifica(dialecte, linies, args, sessio, regulador):
    """Demana uns quants mots d'un en un i els compara amb el fitxer."""
    cami = f"{args.prefix}_{dialecte.lower()}.txt"
    if not os.path.exists(cami):
        return []
    with open(cami, encoding="utf-8") as f:
        taula = dict(zip(linies, (l.rstrip("\n") for l in f)))
    mostra = random.sample(sorted(taula), min(args.mostra, len(taula)))
    difs = []
    for i, mot in enumerate(mostra, 1):
        r = demanar_amb_reintents(sessio, mot + ".", dialecte, regulador)
        if r is None:
            continue
        sol = neteja(r)
        if sol != taula[mot]:
            difs.append((mot, taula[mot], sol))
        if i % 50 == 0:
            print(f"    {i}/{len(mostra)}…", flush=True)
    marca = "✓" if not difs else "✗"
    print(f"  {marca} {dialecte:12} {len(mostra)} mots comprovats contra l'API, "
          f"{len(difs)} diferents")
    for d in difs[:5]:
        print(f"      «{d[0]}»: al fitxer «{d[1]}», l'API diu «{d[2]}»")
    return difs


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--entrada", default="../../col_0.txt")
    p.add_argument("--dialectes", default=",".join(DIALECTES))
    p.add_argument("--cache", default="cache")
    p.add_argument("--perfil", default="rapid", choices=list(PERFILS),
                   help="ritme de les peticions de la verificació "
                        "(per defecte, %(default)s)")
    p.add_argument("--mostra", type=int, default=0,
                   help="mots per dialecte que es tornen a demanar a l'API "
                        "(0 = només revisió interna)")
    args = p.parse_args()
    args.prefix = os.path.splitext(os.path.basename(args.entrada))[0]

    with open(args.entrada, encoding="utf-8") as f:
        linies = [l.strip() for l in f if l.strip()]
    mots_unics = list(dict.fromkeys(linies))
    dialectes = [d.strip() for d in args.dialectes.split(",") if d.strip()]
    print(f"Entrada: {args.entrada} — {mil(len(linies))} línies, "
          f"{mil(len(mots_unics))} mots únics\n")

    greus, avisos = [], []
    for d in dialectes:
        g, a = revisa(d, linies, mots_unics, args)
        greus += g
        avisos += a

    if args.mostra:
        print(f"\nVerificació contra l'API ({args.mostra} mots per dialecte):")
        sessio, regulador = sessio_nova(), Regulador(PERFILS[args.perfil])
        for d in dialectes:
            if verifica(d, linies, args, sessio, regulador):
                greus.append(f"{d}: hi ha transcripcions que no coincideixen amb "
                             f"l'API (mira-ho més amunt)")

    print()
    for a in avisos:
        print(f"  · avís: {a}")
    if greus:
        print(f"\n✗ {len(greus)} problema(es):")
        for g in greus:
            print(f"    - {g}")
        sys.exit(1)
    print("✓ Tot correcte.")


if __name__ == "__main__":
    main()
