"""
EINA LOCAL. Donar d'alta una paraula als dos fitxers alhora.

    python3 diccionaris/python/afegir_paraula.py \
        --paraula tiktokera --lema tiktoker --codi NCFS000 --silabes 4 \
        --ca tiktukˈeɾə --nw tiktokˈeɾɛ --va tiktokˈeɾa --ba tiktukˈəɾə

Una paraula nova ha d'entrar al diccionari (paraula, lema, codi, síl·labes i
els tres enllaços) i a la col_10 (com sona a cada dialecte) A LA MATEIXA FILA i
al mateix commit. Fer-ho a mà vol dir encertar la mateixa posició en dos fitxers
de sis-centes mil línies, un dels quals fa 76 MB; per això hi ha aquesta eina.

No corre mai als workflows: allà, si els dos fitxers no es corresponen, el
sincronitzar.py s'atura i diu quina paraula falta i on.

LA POSICIÓ. El diccionari està ordenat alfabèticament ignorant accents,
majúscules, guions i punts volats, però no del tot (423 llocs de 619.783 no hi
quadren, quasi tots per la puntuació). Per això la fila es proposa i s'ensenya
amb els veïns perquè la miris, i sempre la pots dir tu amb --fila.
"""

import argparse
import os
import sys
import unicodedata

DIR_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if DIR_SCRIPTS not in sys.path:
    sys.path.insert(0, DIR_SCRIPTS)

import avisos
import camins
import col_10 as modul_col_10


def clau_dordre(paraula):
    text = paraula.strip().lower()
    for tros in ("·", "'", "’", "-", " "):
        text = text.replace(tros, "")
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def on_va(paraules, paraula):
    """La primera fila que ja no va abans que la paraula nova."""
    clau = clau_dordre(paraula)
    esquerra, dreta = 0, len(paraules)
    while esquerra < dreta:
        mig = (esquerra + dreta) // 2
        if clau_dordre(paraules[mig]) < clau:
            esquerra = mig + 1
        else:
            dreta = mig
    return esquerra


def main():
    codis = camins.dialectes()

    analitzador = argparse.ArgumentParser(description="Dona d'alta una paraula.")
    analitzador.add_argument("--paraula", required=True)
    analitzador.add_argument("--lema", help="per defecte, la mateixa paraula")
    analitzador.add_argument("--codi", required=True, help="el codi EAGLES, p. ex. NCFS000")
    analitzador.add_argument("--silabes", required=True, type=int)
    analitzador.add_argument("--vicc", action="store_true", help="surt al Viccionari")
    analitzador.add_argument("--viq", action="store_true", help="surt a la Viquipèdia")
    analitzador.add_argument("--diec", action="store_true", help="surt al DIEC")
    analitzador.add_argument("--fila", type=int, help="on posar-la (1 = la primera)")
    analitzador.add_argument("--si", action="store_true", help="no preguntis res")
    for codi in codis:
        analitzador.add_argument(f"--{codi}", required=True,
                                 help=f"la transcripció en {codi}")
    opcions = analitzador.parse_args()

    files = camins.llegir_diccionari()
    identitats, transcripcions = modul_col_10.llegir()
    if len(identitats) != len(files):
        avisos.plegar(f"la col_10 té {camins.mil(len(identitats))} línies i el diccionari "
                      f"{camins.mil(len(files))}: primer passa el sincronitzar.py.")

    paraules = [fila[0] for fila in files]
    posicio = (opcions.fila - 1) if opcions.fila else on_va(paraules, opcions.paraula)
    if not 0 <= posicio <= len(files):
        avisos.plegar(f"la fila {posicio + 1} no existeix (n'hi ha {camins.mil(len(files))}).")

    nova = [
        opcions.paraula,
        opcions.lema or opcions.paraula,
        opcions.codi,
        str(opcions.silabes),
        "Vicc" if opcions.vicc else "NO",
        "Viq" if opcions.viq else "NO",
        "Diec" if opcions.diec else "NO",
    ]

    print(f"\nA la fila {posicio + 1}:\n")
    for i in range(max(0, posicio - 2), posicio):
        print(f"   {i + 1:>7}  {'$'.join(files[i])}")
    print(f"   {posicio + 1:>7}  {'$'.join(nova)}   <-- nova")
    for i in range(posicio, min(len(files), posicio + 2)):
        print(f"   {i + 2:>7}  {'$'.join(files[i])}")
    print()
    for codi in codis:
        print(f"   {codi}: {getattr(opcions, codi)}")

    if not opcions.si:
        if input("\nVa bé? [s/N] ").strip().lower() not in ("s", "si", "sí"):
            print("No s'ha tocat res.")
            return 1

    files.insert(posicio, nova)
    identitats.insert(posicio, nova[:camins.CAMPS_IDENTITAT])
    for codi in codis:
        transcripcions[codi].insert(posicio, getattr(opcions, codi))

    camins.escriure_diccionari(files)
    modul_col_10.escriure(identitats, transcripcions)

    print(f"\nFeta. El diccionari i la col_10 tenen {camins.mil(len(files))} files.")
    print("Comiteja'ls tots dos junts: el workflow s'espera trobar-los d'acord.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
