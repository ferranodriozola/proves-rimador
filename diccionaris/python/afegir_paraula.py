"""
EINA LOCAL. Donar d'alta una paraula al diccionari, als dos fitxers alhora.

    python3 diccionaris/python/afegir_paraula.py

ÉS PER AL DICCIONARI, o sigui per a una paraula que es diu a TOTS els
dialectes: entra a diccionari.5.2.3.txt i a col_10.txt, i et demana com sona a
cadascun. Una paraula que només es digui en un lloc no va aquí sinó a l'apendix
d'aquell dialecte (dialectes_col/<codi>/apendix/), que és una llista de
paraules a part i té la seva pròpia col_10.

No porta arguments: l'engegues (des del VS Code amb el botó de Run, o des del
terminal) i et va demanant la paraula, el lema, el codi, les síl·labes, els
enllaços i la transcripció de cada dialecte, un per un.

Una paraula nova ha d'entrar al diccionari (paraula, lema, codi, síl·labes i
els tres enllaços) i a la col_10 (com sona a cada dialecte) A LA MATEIXA FILA i
al mateix commit. Fer-ho a mà vol dir encertar la mateixa posició en dos fitxers
de sis-centes mil línies, un dels quals fa 76 MB; per això hi ha aquesta eina.

No corre mai als workflows: allà, si els dos fitxers no es corresponen, el
sincronitzar.py s'atura i diu quina paraula falta i on.

LA POSICIÓ. El diccionari està ordenat alfabèticament ignorant accents,
majúscules, guions i punts volats, però no del tot (423 llocs de 619.783 no hi
quadren, quasi tots per la puntuació). Per això la fila es proposa i s'ensenya
amb els veïns perquè la miris, i sempre la pots dir tu quan et pregunti la fila.
"""

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


def _preguntar(text):
    """Un input que no peta si tanques la finestra o fas Ctrl+C."""
    try:
        return input(text).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nDeixat córrer. No s'ha tocat res.")
        sys.exit(1)


def demanar(text, per_defecte=None):
    """Text obligatori. Si hi ha per_defecte, l'Enter el pren."""
    if per_defecte:
        text = f"{text} [{per_defecte}]: "
    else:
        text = f"{text}: "
    while True:
        resposta = _preguntar(text)
        if resposta:
            return resposta
        if per_defecte:
            return per_defecte
        print("   Cal posar-hi alguna cosa.")


def demanar_nombre(text):
    while True:
        resposta = _preguntar(f"{text}: ")
        if resposta.isdigit() and int(resposta) > 0:
            return int(resposta)
        print("   Ha de ser un nombre enter positiu.")


def demanar_si(text):
    """[s/N]: l'Enter és que no."""
    return _preguntar(f"{text} [s/N]: ").lower() in ("s", "si", "sí")


def main():
    codis = camins.dialectes()

    print("\nDONAR D'ALTA UNA PARAULA (Ctrl+C per deixar-ho córrer)\n")
    print("Carregant el diccionari i la col_10 (van uns segons)...")
    files = camins.llegir_diccionari()
    identitats, transcripcions = modul_col_10.llegir()
    if len(identitats) != len(files):
        avisos.plegar(f"la col_10 té {camins.mil(len(identitats))} línies i el diccionari "
                      f"{camins.mil(len(files))}: primer passa el sincronitzar.py.")

    paraules = [fila[0] for fila in files]
    print(f"Hi ha {camins.mil(len(files))} files.\n")

    paraula = demanar("Paraula")
    lema = demanar("Lema", per_defecte=paraula)
    codi_eagles = demanar("Codi EAGLES (p. ex. NCFS000)")
    silabes = demanar_nombre("Síl·labes")
    vicc = demanar_si("Surt al Viccionari?")
    viq = demanar_si("Surt a la Viquipèdia?")
    diec = demanar_si("Surt al DIEC?")

    transcripcions_noves = {}
    for codi in codis:
        transcripcions_noves[codi] = demanar(f"Transcripció en {codi}")

    fila = _preguntar("\nFila on posar-la (1 = la primera; Enter = la que et proposi): ")
    if fila:
        if not fila.isdigit() or int(fila) < 1:
            avisos.plegar("la fila ha de ser un nombre enter a partir de l'1.")
        posicio = int(fila) - 1
    else:
        posicio = on_va(paraules, paraula)
    if not 0 <= posicio <= len(files):
        avisos.plegar(f"la fila {posicio + 1} no existeix (n'hi ha {camins.mil(len(files))}).")

    nova = [
        paraula,
        lema,
        codi_eagles,
        str(silabes),
        "Vicc" if vicc else "NO",
        "Viq" if viq else "NO",
        "Diec" if diec else "NO",
    ]

    print(f"\nA la fila {posicio + 1}:\n")
    for i in range(max(0, posicio - 2), posicio):
        print(f"   {i + 1:>7}  {'$'.join(files[i])}")
    print(f"   {posicio + 1:>7}  {'$'.join(nova)}   <-- nova")
    for i in range(posicio, min(len(files), posicio + 2)):
        print(f"   {i + 2:>7}  {'$'.join(files[i])}")
    print()
    for codi in codis:
        print(f"   {codi}: {transcripcions_noves[codi]}")

    if not demanar_si("\nVa bé?"):
        print("No s'ha tocat res.")
        return 1

    files.insert(posicio, nova)
    identitats.insert(posicio, nova[:camins.CAMPS_IDENTITAT])
    for codi in codis:
        transcripcions[codi].insert(posicio, transcripcions_noves[codi])

    camins.escriure_diccionari(files)
    modul_col_10.escriure(identitats, transcripcions)

    print(f"\nFeta. El diccionari i la col_10 tenen {camins.mil(len(files))} files.")
    print("Comiteja'ls tots dos junts: el workflow s'espera trobar-los d'acord.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
