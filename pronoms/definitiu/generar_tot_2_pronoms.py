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

# Carpetes de sortida separades
DIR_SORTIDA_NORMALS = os.path.join(BASE_DIR, "txt_fets", "2_pronoms")
DIR_SORTIDA_APENDIX = os.path.join(BASE_DIR, "txt_fets", "apendix")
PATRO_SORTIDA = "verb_pronom_{p1}_{p2}.txt"

# 1. IDENTIFIQUEM LES COMBINACIONS EXCEPCIONALS
PARELLES_APENDIX_SET = {("li", "les"), ("li", "la"), ("li", "els"), ("li", "el")}

TOTES_LES_PARELLES = list(itertools.combinations(enclisi.ORDRE_PRONOMS, 2))
PARELLES_NORMALS = [p for p in TOTES_LES_PARELLES if p not in PARELLES_APENDIX_SET]
PARELLES_APENDIX = [p for p in TOTES_LES_PARELLES if p in PARELLES_APENDIX_SET]

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


# ====================================================================
# ESPAI PER A LES TEVES REGLES EXCEPCIONALS
# ====================================================================
def aplicar_regles_apendix(forma, p1, p2, forma_verbal, persona, silabes_base):
    """
    Aquesta funció genera LES + LI = LES-HI / LA + LI = LA-HI / 
    ELS + LI = LOS-HI (o 'ls-hi) / EL + LI = L'HI.
    """
    # DE MOMENT HO DEIXO COM A PLACEHOLDER: 
    # Aquí esciuràs l'algorisme gràfic. Ara afegeix '-APENDIX' per provar-ho.
    paraula_actual = f"{forma}-APENDIX"
    
    # Mantenim el codi morfològic com l'estàndard
    codi = enclisi.construir_codi(forma_verbal, persona, [p1, p2])
    
    return {
        "paraula": paraula_actual,
        "codi": codi,
        "silabes": silabes_base
    }


def generar(parelles, dir_sortida, us_apendix=False):
    if not parelles:
        return {}, {}, Counter()
        
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

            # Derivem l'execució cap a les regles noves si és l'apèndix
            if us_apendix:
                r = aplicar_regles_apendix(
                    forma=forma, p1=p1, p2=p2, 
                    forma_verbal=forma_verbal, 
                    persona=persona, 
                    silabes_base=col[3][i]
                )
            else:
                r = enclisi.generar_forma(
                    forma=forma, pronoms=[p1, p2], 
                    forma_verbal=forma_verbal, 
                    persona=persona, silabes_base=col[3][i]
                )
            
            linia_nova = [
                r["paraula"], col[1][i], r["codi"], "0", "NO", "NO", "NO"
            ]
            
            linies[par].append("$".join(linia_nova))
            per_forma[forma_verbal] += 1

        fitxers = {}
        for par in parelles:
            ruta = os.path.join(dir_sortida, PATRO_SORTIDA.format(p1=par[0], p2=par[1]))
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
    
    p_ordenats = tuple(enclisi.ordenar_pronoms([p1, p2]))
    if p_ordenats not in TOTES_LES_PARELLES:
        raise SystemExit(f"Parella no vàlida o repetida: {text}\n")
        
    return p_ordenats


def ajuntar_i_ordenar_resultats(fitxers, dir_sortida):
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

    ruta_totes = os.path.join(dir_sortida, "tots_ajuntats_2_pr.txt")
    with open(ruta_totes, "w", encoding="utf-8") as f:
        f.write("\n".join(totes_les_linies) + "\n" if totes_les_linies else "")

    ruta_primera_columna = os.path.join(dir_sortida, "totes_primeres_columnes_2_pr.txt")
    with open(ruta_primera_columna, "w", encoding="utf-8") as f:
        f.write("\n".join(primeres_columnes) + "\n" if primeres_columnes else "")

    return ruta_totes, ruta_primera_columna


def main():
    args = sys.argv[1:]
    
    if args:
        parelles_usuari = tuple(_parse_parella(a) for a in args)
        p_normals_exec = [p for p in parelles_usuari if p in PARELLES_NORMALS]
        p_apendix_exec = [p for p in parelles_usuari if p in PARELLES_APENDIX]
    else:
        p_normals_exec = PARELLES_NORMALS
        p_apendix_exec = PARELLES_APENDIX

    print("--- GENERANT COMBINACIONS NORMALS ---")
    linies_n, fitxers_n, per_forma_n = generar(p_normals_exec, DIR_SORTIDA_NORMALS, us_apendix=False)
    if fitxers_n:
        ajuntar_i_ordenar_resultats(fitxers_n, DIR_SORTIDA_NORMALS)

    print("\n--- GENERANT COMBINACIONS APÈNDIX ---")
    linies_a, fitxers_a, per_forma_a = generar(p_apendix_exec, DIR_SORTIDA_APENDIX, us_apendix=True)
    if fitxers_a:
        ajuntar_i_ordenar_resultats(fitxers_a, DIR_SORTIDA_APENDIX)

    # Resum final
    totes_linies = sum(len(v) for v in linies_n.values()) + sum(len(v) for v in linies_a.values())
    tots_fitxers = {**fitxers_n, **fitxers_a}
    
    print(f"\nFet! {totes_linies:,} línies totals generades en {len(tots_fitxers)} fitxers\n")

if __name__ == "__main__":
    main()