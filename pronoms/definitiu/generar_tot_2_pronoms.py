import os
import sys
import itertools
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import enclisi

CAMPS = 7  # Ajustat a 7 columnes per quadrar exactament amb verbs.txt

ARXIU_VERBS = "verbs.txt"
# Guardem l'arxiu a la carpeta txt_fets/2_pronoms
DIR_SORTIDA = os.path.join(BASE_DIR, "txt_fets", "2_pronoms")
PATRO_SORTIDA = "verb_pronom_{p1}_{p2}.txt"

# Generem totes les parelles de 2 pronoms automàticament segons l'ordre oficial,
# prescindint de llicencies.py
PARELLES = list(itertools.combinations(enclisi.ORDRE_PRONOMS, 2))

FORMES = {
    "VMN00000": ("N", None), "VSN00000": ("N", None), "VAN00000": ("N", None),
    "VMG00000": ("G", None), "VSG00000": ("G", None), "VAG00000": ("G", None),
}

NOM_FORMA = {"N": "infinitiu", "G": "gerundi"}


def llegir_columnes():
    col = {n: [] for n in range(CAMPS)}
    try:
        with open(ARXIU_VERBS, "r", encoding="utf-8") as f:
            for numero, linia in enumerate(f, 1):
                linia = linia.rstrip("\n")
                if not linia:
                    continue
                camps = linia.split("$")
                
                while len(camps) < CAMPS:
                    camps.append("")
                
                for n in range(CAMPS):
                    col[n].append(camps[n])
    except FileNotFoundError:
        raise SystemExit(f"No s'ha trobat l'arxiu '{ARXIU_VERBS}'.")
        
    if not col[0]:
        raise SystemExit(f"L'arxiu '{ARXIU_VERBS}' és buit.")
    return col


def generar(parelles=PARELLES, dir_sortida=DIR_SORTIDA):
    os.makedirs(dir_sortida, exist_ok=True)
    col = llegir_columnes()

    linies = {par: [] for par in parelles}
    per_forma = Counter()

    for i in range(len(col[0])):
        info = FORMES.get(col[2][i])
        if info is None:
            continue
        forma_verbal, persona = info
        forma = col[0][i]

        for par in parelles:
            p1, p2 = par

            # Crida neta i directa, tal com es fa amb 1 pronom
            r = enclisi.generar_forma(
                forma=forma, 
                pronoms=[p1, p2], 
                forma_verbal=forma_verbal, 
                persona=persona, 
                silabes_base=col[3][i]
            )
            
            linia_nova = [
                r["paraula"],        # 0: la nova forma gràfica (verb + 2 pronoms)
                col[1][i],           # 1: lema original
                r["codi"],           # 2: codi modificat
                "0",                 # 3: nou càlcul de síl·labes (substitueix l'antic)
                "NO",                # 4: Incondicionalment NO
                "NO",                # 5: Incondicionalment NO
                "NO"                 # 6: Incondicionalment NO
            ]
            
            linies[par].append("$".join(linia_nova))
            per_forma[forma_verbal] += 1

    fitxers = {}
    for par in parelles:
        p1, p2 = par
        ruta = os.path.join(dir_sortida, PATRO_SORTIDA.format(p1=p1, p2=p2))
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("\n".join(linies[par]) + "\n" if linies[par] else "")
        fitxers[par] = ruta

    return linies, fitxers, per_forma


def _parse_parella(text):
    if ":" not in text:
        raise SystemExit(f"Parella mal escrita: {text!r} (format p1:p2, p. ex. li:el)")
    
    p1, p2 = text.split(":", 1)
    
    if p1 not in enclisi.ENCLISI or p2 not in enclisi.ENCLISI:
        raise SystemExit(f"Pronoms desconeguts a la parella: {text}\n")
    
    # Ordenem els pronoms per coincidir amb les claus de l'itertools.combinations
    p_ordenats = tuple(enclisi.ordenar_pronoms([p1, p2]))
    if p_ordenats not in PARELLES:
        raise SystemExit(f"Parella no vàlida o repetida: {text}\n")
        
    return p_ordenats



def ajuntar_i_ordenar_resultats(fitxers, dir_sortida):
    """
    Llegeix tots els fitxers de pronoms generats, ajunta les línies,
    les ordena alfabèticament i crea dos arxius resultants a la carpeta de sortida.
    """
    totes_les_linies = []
    primeres_columnes = []

    for ruta in fitxers.values():
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                for linia in f:
                    linia = linia.strip()
                    if linia:
                        totes_les_linies.append(linia)
                        camps = linia.split("$")
                        if camps:
                            primeres_columnes.append(camps[0])

    totes_les_linies.sort()
    primeres_columnes.sort()

    ruta_totes = os.path.join(dir_sortida, "tots_ajuntats.txt")
    with open(ruta_totes, "w", encoding="utf-8") as f:
        f.write("\n".join(totes_les_linies) + "\n" if totes_les_linies else "")

    ruta_primera_columna = os.path.join(dir_sortida, "totes_primeres_columnes.txt")
    with open(ruta_primera_columna, "w", encoding="utf-8") as f:
        f.write("\n".join(primeres_columnes) + "\n" if primeres_columnes else "")

    return ruta_totes, ruta_primera_columna



def main():
    args = sys.argv[1:]
    parelles = tuple(_parse_parella(a) for a in args) if args else tuple(PARELLES)

    linies, fitxers, per_forma = generar(parelles)

    ruta_totes, ruta_col1 = ajuntar_i_ordenar_resultats(fitxers, DIR_SORTIDA)

    total = sum(len(v) for v in linies.values())
    print(f"Fet! {total:,} línies en {len(fitxers)} fitxers\n")
    print(f"  {'fitxer':32s} {'línies':>9s} {'mida':>8s}")
    for par in parelles:
        mida = os.path.getsize(fitxers[par]) / 1e6
        print(f"  {os.path.basename(fitxers[par]):32s} {len(linies[par]):9,} {mida:7.1f} MB")

    print(f"\nArxius totals generats i ordenats:")
    print(f"  - {os.path.basename(ruta_totes)} ({os.path.getsize(ruta_totes) / 1e6:.1f} MB)")
    print(f"  - {os.path.basename(ruta_col1)} ({os.path.getsize(ruta_col1) / 1e6:.1f} MB)")

    print("\n  per forma verbal:")
    for f in ("N", "G"):
        if per_forma[f]:
            print(f"    {NOM_FORMA[f]:11s} {per_forma[f]:9,}")


if __name__ == "__main__":
    main()